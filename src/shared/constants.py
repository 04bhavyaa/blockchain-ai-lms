"""
Shared constants and configuration across services
"""

# Token Rewards [web:152]
TOKEN_REWARDS = {
    'LESSON_COMPLETE': 5,
    'QUIZ_COMPLETE': 20,
    'QUIZ_PASS_BONUS': 10,  # Bonus on top if passed
    'COURSE_COMPLETE': 100,
    'FIRST_COURSE_BONUS': 50,
    'STREAK_BONUS': 5,  # Per day streak
}

# Token Costs
TOKEN_COSTS = {
    'COURSE_UNLOCK': 30,
    'PREMIUM_MODULE': 15,
    'CHATBOT_DETAILED_QUERY': 2,
    'CHATBOT_FAQ': 0,  # Free
}

# Recommendation Weights
RECOMMENDATION_WEIGHTS = {
    'COLLABORATIVE_FILTERING': 0.6,
    'CONTENT_BASED_FILTERING': 0.4,
}

# Course Constants
COURSE_STATUSES = [
    'draft', 'published', 'archived'
]

DIFFICULTY_LEVELS = [
    'beginner', 'intermediate', 'advanced'
]

ACCESS_TYPES = [
    'free', 'token', 'paid'
]

# Authentication
JWT_ACCESS_TOKEN_LIFETIME_HOURS = 24
JWT_REFRESH_TOKEN_LIFETIME_DAYS = 7

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# API Versioning
API_VERSION = 'v1'

# Blockchain
BLOCKCHAIN_NETWORK = 'sepolia'
BLOCKCHAIN_CONFIRMATION_BLOCKS = 12

# Rate Limiting
RATE_LIMITS = {
    "login": {"limit": 5, "period": 60},          # 5 requests per minute
    "api_default": {"limit": 100, "period": 3600}, # 100 requests per hour
    "chatbot": {"limit": 20, "period": 300},      # 20 per 5 min
}
