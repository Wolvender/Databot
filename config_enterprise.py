# config_enterprise.py - Enterprise configuration management
"""
Advanced configuration for multi-tenant deployment
Supports different tiers, feature flags, and environment-specific settings
"""

import os
from enum import Enum
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class SubscriptionTier(Enum):
    """Subscription tiers for SaaS pricing."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class EnterpriseConfig:
    """Enterprise configuration with tier-based features."""
    
    # Environment
    ENV = Environment(os.getenv("ENVIRONMENT", "development"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///databot.db")
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    
    # Rate Limits (Files per Reset Period)
    RATE_LIMITS = {
        SubscriptionTier.FREE: 100,
        SubscriptionTier.STARTER: 5000,
        SubscriptionTier.PROFESSIONAL: 10000,
        SubscriptionTier.ENTERPRISE: 1000000000,  # Unlimited
    }
    
    # Reset Periods (in seconds)
    # Free: 2 weeks, Starter/Pro: 1 week, Enterprise: 30 days
    RESET_PERIODS = {
        SubscriptionTier.FREE: 14 * 24 * 3600,  # 2 weeks
        SubscriptionTier.STARTER: 7 * 24 * 3600,  # 1 week
        SubscriptionTier.PROFESSIONAL: 7 * 24 * 3600,  # 1 week
        SubscriptionTier.ENTERPRISE: 30 * 24 * 3600,  # 30 days
    }
    
    # File Upload Limits (MB)
    FILE_SIZE_LIMITS = {
        SubscriptionTier.FREE: 10,
        SubscriptionTier.STARTER: 50,
        SubscriptionTier.PROFESSIONAL: 200,
        SubscriptionTier.ENTERPRISE: 1024,
    }
    
    # (Legacy Monthly Limits - kept for reference if needed, but RATE_LIMITS is primary now)
    MONTHLY_LIMITS = {
        SubscriptionTier.FREE: 100,
        SubscriptionTier.STARTER: 20000,
        SubscriptionTier.PROFESSIONAL: 80000,
        SubscriptionTier.ENTERPRISE: 1000000,
    }
    
    # Feature Flags
    FEATURES = {
        SubscriptionTier.FREE: {
            "batch_processing": False,
            "api_access": False,
            "custom_templates": False,
            "priority_support": False,
            "audit_logs": False,
            "sso": False,
            "white_label": False,
        },
        SubscriptionTier.STARTER: {
            "batch_processing": True,
            "api_access": False,
            "custom_templates": True,
            "priority_support": False,
            "audit_logs": False,
            "sso": False,
            "white_label": False,
        },
        SubscriptionTier.PROFESSIONAL: {
            "batch_processing": True,
            "api_access": True,
            "custom_templates": True,
            "priority_support": True,
            "audit_logs": True,
            "sso": False,
            "white_label": False,
        },
        SubscriptionTier.ENTERPRISE: {
            "batch_processing": True,
            "api_access": True,
            "custom_templates": True,
            "priority_support": True,
            "audit_logs": True,
            "sso": True,
            "white_label": True,
        },
    }
    
    # LLM Models by Tier
    ALLOWED_MODELS = {
        SubscriptionTier.FREE: ["llama-3.1-8b-instant"],
        SubscriptionTier.STARTER: ["llama-3.1-8b-instant", "llama-3.1-70b-versatile"],
        SubscriptionTier.PROFESSIONAL: ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "gpt-3.5-turbo"],
        SubscriptionTier.ENTERPRISE: ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "gpt-3.5-turbo", "gpt-4"],
    }
    
    # Supported File Types
    SUPPORTED_FILE_TYPES = [".pdf", ".txt", ".eml", ".docx", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"]
    
    # Email Configuration (for notifications)
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    # Monitoring
    SENTRY_DSN = os.getenv("SENTRY_DSN")  # Error tracking
    ANALYTICS_ID = os.getenv("ANALYTICS_ID")  # Google Analytics
    
    @classmethod
    def get_tier_config(cls, tier: SubscriptionTier) -> Dict[str, Any]:
        """Get configuration for a specific subscription tier."""
        return {
            "rate_limit": cls.RATE_LIMITS[tier],
            "file_size_limit": cls.FILE_SIZE_LIMITS[tier],
            "monthly_limit": cls.MONTHLY_LIMITS[tier],
            "features": cls.FEATURES[tier],
            "allowed_models": cls.ALLOWED_MODELS[tier],
        }
    
    @classmethod
    def has_feature(cls, tier: SubscriptionTier, feature: str) -> bool:
        """Check if a tier has access to a feature."""
        return cls.FEATURES.get(tier, {}).get(feature, False)
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production."""
        return cls.ENV == Environment.PRODUCTION


# Pricing (monthly/period, in USD/EUR)
PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.STARTER: 30,  # 5000 files / week
    SubscriptionTier.PROFESSIONAL: 99,
    SubscriptionTier.ENTERPRISE: 499,
}

# Use persistent UserManager
def get_user_tier(username: str) -> SubscriptionTier:
    """Get the subscription tier for a user."""
    # Avoid circular import at global level if possible, but safe here
    from user_manager import user_manager
    return user_manager.get_tier(username)


# Example .env file for production:
"""
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@localhost/databot
GROQ_API_KEY=your_groq_key
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key_here
SESSION_TIMEOUT=7200
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your_smtp_password
SENTRY_DSN=https://your_sentry_dsn
"""
