import os

SESSION_TTL_SECONDS = 3600 * 24 * 7  # 7 days

# Database URL from environment (no hardcoding)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
