from logging import getLogger

from django.core.management import BaseCommand

from apps.forums.services import forum_update

logger = getLogger('django')


class Command(BaseCommand):
    """Initiate full statistic recalculation in forum app."""
    def handle(self, *args, **options):
        """Run forum update service to recalculate stats."""
        logger.info('Start forum stat recalculation')
        try:
            forum_update.update_all()
            logger.info('Successfully update forum statistic')
        except Exception as e:
            logger.error(f'Failed to fully update forum cause of {e}')
