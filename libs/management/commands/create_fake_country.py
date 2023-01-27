from django.conf import settings
from django.core.management import BaseCommand

from libs.django_cities_light.factories import CountryFactory


class Command(BaseCommand):
    """Create fake country.

    Django cities light manage command for loading location data, takes too
    much time and it can be annoying. Instead you can use this.

    """
    help = 'Generate fake country'

    def handle(self, *args, **options) -> None:
        assert settings.ENVIRONMENT != 'production'

        country = CountryFactory()
        self.stdout.write(f'Fake country {country.name} has been created')
