# Request
#    ↓
# IP Rate Limiter Middleware
#    ↓
# Login Endpoint
#    ↓
# Login Attempt Service
#    ↓
# Check email/account attempts
#    ↓
# Auth Service login logic

from app.database.redis import RedisDB
from app.utils.config import settings

LOGIN_ATTEMPT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

return current
"""


class LoginAttemptService:

    def __init__(self):
        self.redis_client = RedisDB.get_client()

    def _get_key(self, identifier: str):
        return f"login_attempt:{identifier.lower()}"

    def is_blocked(self, identifier: str):
        redis_key = self._get_key(identifier)

        try:
            attempts = self.redis_client.get(redis_key)

            if attempts is None:
                return False

            return int(attempts) >= settings.login_max_attempts

        except Exception as error:
            print(f"Login attempt Redis error: {error}")
            return False


    def record_failed_attempt(self, identifier: str):
        redis_key = self._get_key(identifier)

        try:
            return self.redis_client.eval(
                LOGIN_ATTEMPT_SCRIPT,
                1,
                redis_key,
                settings.login_attempt_window_seconds,
            )

        except Exception as error:
            print(f"Login attempt Redis error: {error}")
            return None


    def clear_attempts(self, identifier: str):
        redis_key = self._get_key(identifier)

        try:
            self.redis_client.delete(redis_key)

        except Exception as error:
            print(f"Login attempt Redis error: {error}")
