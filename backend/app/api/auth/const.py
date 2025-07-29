from datetime import timedelta

SESSION_MAX_LIFETIME = int(timedelta(days=1).total_seconds())

SESSION_EXPIRATION = int(timedelta(hours=1).total_seconds())
