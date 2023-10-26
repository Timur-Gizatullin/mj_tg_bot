from functools import lru_cache

from decouple import config

CONFIG_REDIS_HOST = config("CONFIG_REDIS_HOST", default=None)
CONFIG_REDIS_PORT = config("CONFIG_REDIS_PORT", default=None)
CONFIG_REDIS_PASSWORD = config("CONFIG_REDIS_PASSWORD", default=None)
CONFIG_REDIS_URL = config("REDIS_URL", default=None)
CONFIG_REDIS_DB = config("CONFIG_REDIS_DB", default=None)


@lru_cache()
def get_redis_url() -> str:
    """Returns irl for redis."""
    if CONFIG_REDIS_URL:
        return CONFIG_REDIS_URL
    if CONFIG_REDIS_PASSWORD:
        return f"redis://:{CONFIG_REDIS_PASSWORD}@{CONFIG_REDIS_HOST}:{CONFIG_REDIS_PORT}/{CONFIG_REDIS_DB}"
    return f"redis://{CONFIG_REDIS_HOST}:{CONFIG_REDIS_PORT}/{CONFIG_REDIS_DB}"


REDIS_URL = get_redis_url()

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
