# user_manager.py - Persistent user management
import json
import os
from typing import Dict, Optional
from config_enterprise import SubscriptionTier

USERS_FILE = "users.json"

class UserManager:
    """Manages user persistence (credentials, tiers, roles)."""
    
    def __init__(self):
        self.users = {}
        self.load_users()

    def load_users(self):
        """Load users from JSON file, or create default if not exists."""
        if not os.path.exists(USERS_FILE):
            # Default initial users
            self.users = {
                "admin": {
                    "password": "admin123",
                    "tier": "enterprise",
                    "is_admin": True
                },
                "user": {
                    "password": "user456",
                    "tier": "free",
                    "is_admin": False
                }
            }
            self.save_users()
        else:
            try:
                with open(USERS_FILE, "r") as f:
                    self.users = json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}

    def save_users(self):
        """Save current users to JSON file."""
        with open(USERS_FILE, "w") as f:
            json.dump(self.users, f, indent=4)

    def get_user(self, username: str) -> Optional[Dict]:
        return self.users.get(username)

    def verify_password(self, username, password) -> bool:
        user = self.users.get(username)
        if user:
            return user["password"] == password
        return False

    def get_tier(self, username: str) -> SubscriptionTier:
        user = self.users.get(username)
        if user:
            tier_str = user.get("tier", "free").upper()
            try:
                return SubscriptionTier[tier_str]
            except KeyError:
                return SubscriptionTier.FREE
        return SubscriptionTier.FREE

    def update_tier(self, username: str, new_tier: SubscriptionTier):
        """Update user's subscription tier."""
        if username in self.users:
            self.users[username]["tier"] = new_tier.name.lower()
            self.save_users()
            return True
        return False

    def create_user(self, username: str, password: str) -> bool:
        """Create a new user with default free tier."""
        if not username or not password:
            return False
        if username in self.users:
            return False
        self.users[username] = {
            "password": password,
            "tier": "free",
            "is_admin": False
        }
        self.save_users()
        return True

# Global instance
user_manager = UserManager()
