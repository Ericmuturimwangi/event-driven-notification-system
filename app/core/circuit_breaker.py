import logging
import pybreaker
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_breaker_redis = redis.from_url(
    settings.redis_url,
    db=2,
)

class _BreakerListener(pybreaker.CircuitBreakerListener):
    """Logs state transitions. Hook point for metrics in a later phase."""

    def state_change(self, cb, old_state, new_state):
        logger.warning(
            f"[CircuitBreaker:{cb.name}] {old_state.name} -> {new_state.name}"
        )

_breakers: dict[str, pybreaker.CircuitBreaker] = {}


def get_breaker(channel: str) -> pybreaker.CircuitBreaker:

    if channel not in _breakers:
        _breakers[channel] = pybreaker.CircuitBreaker(
            fail_max=settings.circuit_breaker_fail_max,
            reset_timeout=settings.circuit_breaker_reset_timeout,
            state_storage=pybreaker.CircuitRedisStorage(
                pybreaker.STATE_CLOSED,
                _breaker_redis,
                namespace=f"breaker:{channel}",
            ),
            listeners=[_BreakerListener()],
            name=channel,
        )
    return _breakers[channel]