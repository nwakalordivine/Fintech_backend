from upstash_redis import Redis
from django.conf import settings

# Redis client with Upstash configuration
redis = Redis(
    url=settings.UPSTASH_REDIS_REST_URL,
    token=settings.UPSTASH_REDIS_REST_TOKEN,
)
