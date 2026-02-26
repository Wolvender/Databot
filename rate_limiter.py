# rate_limiter.py - API rate limiting and cost tracking
"""
Prevent API abuse and track costs for billing
Essential for multi-tenant SaaS deployment
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional
import streamlit as st

class RateLimiter:
    """Token bucket rate limiter for API calls."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in time window
            time_window: Time window in seconds (default: 1 hour)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, user: str) -> tuple[bool, Optional[int]]:
        """
        Check if user is allowed to make a request based on their tier limits.
        
        Returns:
            (allowed: bool, retry_after_seconds: int or None)
        """
        from config_enterprise import EnterpriseConfig, get_user_tier
        
        # Get user's limit and time window based on tier
        tier = get_user_tier(user)
        limit = EnterpriseConfig.RATE_LIMITS[tier]
        # Default to 1 hour if not specified in RESET_PERIODS (fallback)
        time_window = EnterpriseConfig.RESET_PERIODS.get(tier, 3600)
        
        now = time.time()
        cutoff = now - time_window
        
        # Remove old requests (sliding window)
        self.requests[user] = [req_time for req_time in self.requests[user] if req_time > cutoff]
        
        # Check limit
        if len(self.requests[user]) >= limit:
            oldest_request = min(self.requests[user])
            retry_after = int(oldest_request + time_window - now)
            return False, retry_after
        
        # Allow request
        self.requests[user].append(now)
        return True, None
    
    def get_remaining(self, user: str) -> int:
        """Get remaining requests for user based on tier."""
        from config_enterprise import EnterpriseConfig, get_user_tier
        
        tier = get_user_tier(user)
        limit = EnterpriseConfig.RATE_LIMITS[tier]
        time_window = EnterpriseConfig.RESET_PERIODS.get(tier, 3600)
        
        now = time.time()
        cutoff = now - time_window
        self.requests[user] = [req_time for req_time in self.requests[user] if req_time > cutoff]
        return max(0, limit - len(self.requests[user]))


class CostTracker:
    """Track API costs for billing and budgeting."""
    
    # Pricing per 1M tokens (update with actual pricing)
    PRICING = {
        "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
        "llama-3.1-70b-versatile": {"input": 0.59, "output": 0.79},
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    }
    
    def __init__(self):
        """Initialize cost tracker."""
        if "cost_tracking" not in st.session_state:
            st.session_state.cost_tracking = {
                "total_cost": 0.0,
                "total_tokens": 0,
                "requests_count": 0,
                "daily_costs": defaultdict(float),
                "user_costs": defaultdict(float)
            }
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of tokens (4 chars ≈ 1 token)."""
        return len(text) // 4
    
    def track_request(self, model: str, input_text: str, output_text: str, user: str):
        """Track a single API request."""
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        pricing = self.PRICING.get(model, {"input": 0.0, "output": 0.0})
        cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1_000_000
        
        # Update tracking
        today = datetime.now().strftime("%Y-%m-%d")
        st.session_state.cost_tracking["total_cost"] += cost
        st.session_state.cost_tracking["total_tokens"] += total_tokens
        st.session_state.cost_tracking["requests_count"] += 1
        st.session_state.cost_tracking["daily_costs"][today] += cost
        st.session_state.cost_tracking["user_costs"][user] += cost
        
        return {
            "tokens": total_tokens,
            "cost": cost,
            "total_cost": st.session_state.cost_tracking["total_cost"]
        }
    
    def get_user_stats(self, user: str) -> dict:
        """Get cost statistics for a user."""
        return {
            "total_cost": st.session_state.cost_tracking["user_costs"].get(user, 0.0),
            "total_requests": st.session_state.cost_tracking["requests_count"]
        }
    
    def get_daily_costs(self, days: int = 7) -> dict:
        """Get daily costs for last N days."""
        daily_costs = st.session_state.cost_tracking["daily_costs"]
        
        # Get last N days
        result = {}
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            result[date] = daily_costs.get(date, 0.0)
        
        return dict(sorted(result.items()))
    
    def check_budget_limit(self, user: str, monthly_limit: float) -> tuple[bool, float]:
        """
        Check if user is within budget.
        
        Returns:
            (within_budget: bool, remaining_budget: float)
        """
        user_cost = st.session_state.cost_tracking["user_costs"].get(user, 0.0)
        remaining = monthly_limit - user_cost
        return remaining > 0, remaining


# Global instances
rate_limiter = RateLimiter(max_requests=100, time_window=3600)  # 100 requests/hour
cost_tracker = CostTracker()
