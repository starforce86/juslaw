import logging

from django.conf import settings

from health_check.contrib.redis.backends import \
    RedisHealthCheck as BaseRedisHealthCheck
from health_check.exceptions import ServiceUnavailable
from redis import exceptions, from_url

from .base import AbstractHealthCheckBackend

logger = logging.getLogger(__name__)


class RedisHealthCheck(BaseRedisHealthCheck, AbstractHealthCheckBackend):
    """Checks that redis is working alright."""
    _identifier = 'redis'
    _description = 'Redis Health Check'

    def check_status(self):
        """Overridden to change redis url."""
        redis_url = getattr(
            settings, 'REDIS_URL', settings.CACHES['default']['LOCATION']
        )
        logger.debug(
            f'Got {redis_url} as the redis_url. Connecting to redis...',
        )

        logger.debug('Attempting to connect to redis...')
        try:
            # conn is used as a context to release opened resources later
            with from_url(redis_url) as conn:
                conn.ping()  # exceptions may be raised upon ping
        except ConnectionRefusedError as e:
            self.add_error(ServiceUnavailable(
                'Unable to connect to Redis: Connection was refused.'), e
            )
        except exceptions.TimeoutError as e:
            self.add_error(ServiceUnavailable(
                'Unable to connect to Redis: Timeout.'), e
            )
        except exceptions.ConnectionError as e:
            self.add_error(ServiceUnavailable(
                'Unable to connect to Redis: Connection Error'), e
            )
        except BaseException as e:
            self.add_error(ServiceUnavailable('Unknown error'), e)
        else:
            logger.debug('Connection established. Redis is healthy.')
