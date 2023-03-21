from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    """Loading data to ingredient model."""
    help = 'Load csv files to ingredient model.'


    def handle(self, *args, **kwargs):
        # НАйти относительный путь относилтельно BASE_PATH
        BASE_PATH = settings.BASE_DIR
        PATH_TO_FILE = f'../../{BASE_PATH}'
        print(PATH_TO_FILE)
        