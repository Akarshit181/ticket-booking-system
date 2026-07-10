from redis import Redis
from app.utils.config import settings 


class RedisDB:
    _client = None

    @classmethod
    def connect(cls):
        if cls._client is None:
            cls._client = Redis(
                host = settings.redis_host,
                port = settings.redis_port,
                db = settings.redis_db,
                password = settings.redis_password,
                # decode_responses=True without it redis.get("login") return b'5' (bytes) with that return "5" string
                decode_responses = True
            )

            cls._client.ping()
            print("Redis Connected")

    @classmethod
    def get_clien(cls):
        if cls._client is None:
            raise Exception("Redis is not connected.")
        return cls._client

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            cls._client = None