# rate_limiter.py - API rate limiting and cost tracking
"""
Sliding-window rate limiter that persists request history to disk so limits
are not reset every time the Streamlit process restarts.

Key improvements over the original:
  - Request timestamps stored in a JSON file (rate_limits.json)
  - Loaded once at startup, written on every change
  - Thread-safe via a simple in-process lock
  - CostTracker also persisted to cost_data.json (no more session_state loss)
"""

import json
import os
import time
import threading
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Persistence helpers
# ──────────────────────────────────────────────────────────────────────────────

RATE_FILE = "rate_limits.json"
COST_FILE = "cost_data.json"


def _load_json(path: str, default) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return default


def _save_json(path: str, data: dict):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"⚠️  Could not write {path}: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# Rate Limiter
# ──────────────────────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding-window rate limiter backed by a JSON file.

    Each user's entry is a list of Unix timestamps representing past requests.
    Old entries (outside the current window) are pruned on every check.
    """

    def __init__(self):
        self._lock = threading.Lock()
        # { username: [timestamp, ...] }
        raw = _load_json(RATE_FILE, {})
        self._requests: Dict[str, list] = defaultdict(list, {k: v for k, v in raw.items()})

    # ── private ──────────────────────────────────────────────────────────────

    def _get_tier_limits(self, user: str):
        """Return (limit, window_seconds) for the user's subscription tier."""
        from config_enterprise import EnterpriseConfig, get_user_tier
        tier = get_user_tier(user)
        limit = EnterpriseConfig.RATE_LIMITS[tier]
        window = EnterpriseConfig.RESET_PERIODS.get(tier, 3600)
        return limit, window

    def _prune(self, user: str, cutoff: float):
        """Remove timestamps older than cutoff (in-place, no save)."""
        self._requests[user] = [t for t in self._requests[user] if t > cutoff]

    def _persist(self):
        """Write current state to disk. Must be called with lock held."""
        _save_json(RATE_FILE, dict(self._requests))

    # ── public ───────────────────────────────────────────────────────────────

    def is_allowed(self, user: str) -> Tuple[bool, Optional[int]]:
        """
        Check whether the user may make another request right now.

        Returns:
            (True, None)          – request is allowed; timestamp recorded.
            (False, retry_after)  – limit hit; retry_after is seconds to wait.
        """
        with self._lock:
            limit, window = self._get_tier_limits(user)
            now = time.time()
            self._prune(user, now - window)

            if len(self._requests[user]) >= limit:
                oldest = min(self._requests[user])
                retry_after = max(1, int(oldest + window - now))
                return False, retry_after

            self._requests[user].append(now)
            self._persist()
            return True, None

    def get_remaining(self, user: str) -> int:
        """Return how many requests the user can still make in the current window."""
        with self._lock:
            limit, window = self._get_tier_limits(user)
            now = time.time()
            self._prune(user, now - window)
            return max(0, limit - len(self._requests[user]))

    def get_reset_time(self, user: str) -> Optional[datetime]:
        """
        Return the datetime when the oldest in-window request falls off
        (i.e. when at least one slot frees up).  Returns None if there are
        no requests in the window.
        """
        with self._lock:
            _, window = self._get_tier_limits(user)
            now = time.time()
            self._prune(user, now - window)
            if not self._requests[user]:
                return None
            oldest = min(self._requests[user])
            return datetime.fromtimestamp(oldest + window)

    def reset_user(self, user: str):
        """Manually clear all recorded requests for a user (admin use)."""
        with self._lock:
            self._requests[user] = []
            self._persist()


# ──────────────────────────────────────────────────────────────────────────────
# Cost Tracker
# ──────────────────────────────────────────────────────────────────────────────

class CostTracker:
    """
    Tracks per-user, per-day API costs.
    Data is persisted to cost_data.json so it survives restarts.

    Structure of cost_data.json:
    {
      "total_cost": 1.23,
      "total_tokens": 45000,
      "requests_count": 12,
      "daily_costs": { "2025-01-15": 0.45, ... },
      "user_costs":  { "alice": 0.80, ... }
    }
    """

    # Pricing per 1 M tokens (input / output)
    PRICING = {
        "llama-3.1-8b-instant":    {"input": 0.05,  "output": 0.08},
        "llama-3.1-70b-versatile": {"input": 0.59,  "output": 0.79},
        "llama-3.3-70b-versatile": {"input": 0.59,  "output": 0.79},
        "gpt-4":                   {"input": 30.0,  "output": 60.0},
        "gpt-3.5-turbo":           {"input": 0.50,  "output": 1.50},
    }

    _EMPTY = {
        "total_cost": 0.0,
        "total_tokens": 0,
        "requests_count": 0,
        "daily_costs": {},
        "user_costs": {},
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict = _load_json(COST_FILE, dict(self._EMPTY))
        # Ensure all keys exist (forward-compat if the file is from an older version)
        for k, v in self._EMPTY.items():
            self._data.setdefault(k, v)

    # ── private ──────────────────────────────────────────────────────────────

    def _persist(self):
        _save_json(COST_FILE, self._data)

    # ── public ───────────────────────────────────────────────────────────────

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough estimate: ~4 characters per token."""
        return max(1, len(text) // 4)

    def track_request(
        self,
        model: str,
        input_text: str,
        output_text: str,
        user: str,
    ) -> dict:
        """
        Record the cost of one LLM call.

        Returns a dict with keys: tokens, cost, total_cost.
        """
        input_tokens  = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        total_tokens  = input_tokens + output_tokens

        pricing = self.PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (
            input_tokens  * pricing["input"] +
            output_tokens * pricing["output"]
        ) / 1_000_000

        today = datetime.now().strftime("%Y-%m-%d")

        with self._lock:
            self._data["total_cost"]      += cost
            self._data["total_tokens"]    += total_tokens
            self._data["requests_count"]  += 1
            self._data["daily_costs"][today] = (
                self._data["daily_costs"].get(today, 0.0) + cost
            )
            self._data["user_costs"][user] = (
                self._data["user_costs"].get(user, 0.0) + cost
            )
            total = self._data["total_cost"]
            self._persist()

        return {"tokens": total_tokens, "cost": cost, "total_cost": total}

    def get_user_stats(self, user: str) -> dict:
        return {
            "total_cost":     self._data["user_costs"].get(user, 0.0),
            "total_requests": self._data["requests_count"],
        }

    def get_daily_costs(self, days: int = 7) -> dict:
        """Return a date-sorted dict of costs for the last N days."""
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            result[date] = self._data["daily_costs"].get(date, 0.0)
        return dict(sorted(result.items()))

    def check_budget_limit(
        self, user: str, monthly_limit: float
    ) -> Tuple[bool, float]:
        """
        Returns (within_budget, remaining_dollars).
        within_budget is False when the user has met or exceeded monthly_limit.
        """
        spent = self._data["user_costs"].get(user, 0.0)
        remaining = monthly_limit - spent
        return remaining > 0, remaining

    def reset_user_costs(self, user: str):
        """Zero out a user's recorded spend (e.g. start of new billing cycle)."""
        with self._lock:
            self._data["user_costs"][user] = 0.0
            self._persist()


# ──────────────────────────────────────────────────────────────────────────────
# Global singletons  (same API as original — drop-in replacement)
# ──────────────────────────────────────────────────────────────────────────────

rate_limiter  = RateLimiter()
cost_tracker  = CostTracker()