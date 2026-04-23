# user_manager.py - Persistent user management with bcrypt password hashing
import json
import os
import secrets
from typing import Dict, Optional
from config_enterprise import SubscriptionTier

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    import hashlib
    BCRYPT_AVAILABLE = False
    print("⚠️  bcrypt not installed. Run: pip install bcrypt")
    print("   Falling back to SHA-256 (less secure). Install bcrypt for production!")

USERS_FILE = "users.json"


def _hash_password(plain: str) -> str:
    """Hash a password securely. Uses bcrypt if available, SHA-256 as fallback."""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
    # Fallback — acceptable for a school project, not for production
    return hashlib.sha256(plain.encode()).hexdigest()


def _verify_password(plain: str, stored: str) -> bool:
    """Verify a plain password against a stored hash."""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(plain.encode(), stored.encode())
        except Exception:
            return False
    # Fallback SHA-256 check
    import hashlib
    return hashlib.sha256(plain.encode()).hexdigest() == stored


def _is_hashed(value: str) -> bool:
    """
    Detect whether a stored password is already hashed or is still plain text.
    Bcrypt hashes start with '$2b$'. SHA-256 hashes are exactly 64 hex chars.
    Anything else is assumed to be plain text (legacy).
    """
    if value.startswith("$2b$") or value.startswith("$2a$"):
        return True  # bcrypt
    if len(value) == 64 and all(c in "0123456789abcdef" for c in value):
        return True  # SHA-256 hex
    return False


class UserManager:
    """Manages user persistence: credentials, tiers, roles, and remember-me tokens."""

    def __init__(self):
        self.users: Dict[str, dict] = {}
        self.load_users()

    # ──────────────────────────────────────────────
    # Load / Save
    # ──────────────────────────────────────────────

    def load_users(self):
        """Load users from JSON, creating defaults if the file doesn't exist."""
        if not os.path.exists(USERS_FILE):
            self._create_defaults()
        else:
            try:
                with open(USERS_FILE, "r") as f:
                    self.users = json.load(f)
                # Migrate any plain-text passwords on first load
                self._migrate_plain_passwords()
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Could not load {USERS_FILE}: {e}. Starting fresh.")
                self._create_defaults()

    def save_users(self):
        """Persist current users dict to disk."""
        try:
            with open(USERS_FILE, "w") as f:
                json.dump(self.users, f, indent=4)
        except IOError as e:
            print(f"⚠️  Could not save users: {e}")

    def _create_defaults(self):
        """Create the initial admin + demo user with hashed passwords."""
        self.users = {
            "admin": {
                "password_hash": _hash_password("admin123"),
                "tier": "enterprise",
                "is_admin": True,
                "remember_tokens": {}   # token -> expiry_timestamp
            },
            "user": {
                "password_hash": _hash_password("user456"),
                "tier": "free",
                "is_admin": False,
                "remember_tokens": {}
            },
        }
        self.save_users()

    def _migrate_plain_passwords(self):
        """
        One-time migration: if an existing user record has a plain-text
        'password' key (old format), hash it and rename the key.
        """
        changed = False
        for username, data in self.users.items():
            # Old key was "password", new key is "password_hash"
            if "password" in data and "password_hash" not in data:
                plain = data.pop("password")
                data["password_hash"] = _hash_password(plain)
                data.setdefault("remember_tokens", {})
                changed = True
                print(f"   Migrated password for '{username}' → hashed.")
            # Ensure the tokens dict always exists
            data.setdefault("remember_tokens", {})
        if changed:
            self.save_users()
            print("✅ Password migration complete.")

    # ──────────────────────────────────────────────
    # Core Auth
    # ──────────────────────────────────────────────

    def get_user(self, username: str) -> Optional[dict]:
        return self.users.get(username)

    def verify_password(self, username: str, password: str) -> bool:
        """Return True if username + password are correct."""
        user = self.users.get(username)
        if not user:
            return False
        stored = user.get("password_hash", "")
        return _verify_password(password, stored)

    def create_user(self, username: str, password: str) -> bool:
        """
        Create a new free-tier user.
        Returns False if the username already exists or inputs are empty.
        """
        if not username or not password:
            return False
        if username in self.users:
            return False
        if len(password) < 4:   # Minimal check — raise this limit for production
            return False
        self.users[username] = {
            "password_hash": _hash_password(password),
            "tier": "free",
            "is_admin": False,
            "remember_tokens": {}
        }
        self.save_users()
        return True

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password after verifying the old one."""
        if not self.verify_password(username, old_password):
            return False
        self.users[username]["password_hash"] = _hash_password(new_password)
        # Invalidate all existing remember-me tokens on password change
        self.users[username]["remember_tokens"] = {}
        self.save_users()
        return True

    # ──────────────────────────────────────────────
    # Remember-Me Tokens  (no plain password on disk!)
    # ──────────────────────────────────────────────

    def create_remember_token(self, username: str) -> str:
        """
        Generate a secure random token, store it (hashed) for the user,
        and return the raw token to be stored client-side.
        Token is valid for 30 days.
        """
        import time
        raw_token = secrets.token_hex(32)           # 64-char hex string
        token_hash = _hash_password(raw_token)      # store hashed copy
        expiry = int(time.time()) + 30 * 24 * 3600  # 30 days from now

        self.users[username]["remember_tokens"][token_hash] = expiry
        # Prune expired tokens while we're here
        self._prune_tokens(username)
        self.save_users()
        return raw_token   # caller stores THIS in session / localStorage

    def verify_remember_token(self, username: str, raw_token: str) -> bool:
        """Return True if the raw token matches a stored (non-expired) entry."""
        import time
        user = self.users.get(username)
        if not user:
            return False
        now = int(time.time())
        for stored_hash, expiry in list(user["remember_tokens"].items()):
            if expiry < now:
                continue
            if _verify_password(raw_token, stored_hash):
                return True
        return False

    def revoke_remember_token(self, username: str, raw_token: str):
        """Remove a specific token (called on logout)."""
        user = self.users.get(username)
        if not user:
            return
        for stored_hash in list(user["remember_tokens"].keys()):
            if _verify_password(raw_token, stored_hash):
                del user["remember_tokens"][stored_hash]
                break
        self.save_users()

    def revoke_all_tokens(self, username: str):
        """Invalidate every remember-me token for a user (e.g. password change)."""
        if username in self.users:
            self.users[username]["remember_tokens"] = {}
            self.save_users()

    def _prune_tokens(self, username: str):
        """Remove expired tokens for a user (housekeeping)."""
        import time
        user = self.users.get(username)
        if not user:
            return
        now = int(time.time())
        user["remember_tokens"] = {
            h: exp for h, exp in user["remember_tokens"].items() if exp >= now
        }

    # ──────────────────────────────────────────────
    # Tier Management
    # ──────────────────────────────────────────────

    def get_tier(self, username: str) -> SubscriptionTier:
        user = self.users.get(username)
        if user:
            tier_str = user.get("tier", "free").upper()
            try:
                return SubscriptionTier[tier_str]
            except KeyError:
                return SubscriptionTier.FREE
        return SubscriptionTier.FREE

    def update_tier(self, username: str, new_tier: SubscriptionTier) -> bool:
        if username not in self.users:
            return False
        self.users[username]["tier"] = new_tier.name.lower()
        self.save_users()
        return True

    def is_admin(self, username: str) -> bool:
        user = self.users.get(username)
        return bool(user and user.get("is_admin", False))


# Global singleton
user_manager = UserManager()