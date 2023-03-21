import csv, os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    """Loading data to ingredient model."""
    help = 'Load csv files to ingredient model.'


    def handle(self, *args, **kwargs):
        BASE_PATH = settings.BASE_DIR
        PATH_TO_FILE = f'../../{BASE_PATH}'
        print(PATH_TO_FILE)

        csv_file = 'ingredients.csv'
        path_to_data = '/Users/vitalii/DEV/Diploma_current/foodgram-project-react/data/ingredients.csv'

        try:
            with open(f'{path_to_data}', 'r'
                    ) as csvfile:
                Ingredient.objects.all().delete()
                for row in csvfile:
                    line = row.strip().split(',')
                    if len(line) > 2:
                        pass
                    else:
                        ingredient, unit = line
                        Ingredient.objects.create(
                        name=ingredient,
                        units=unit
                    )
                return f'Unpacking of {csv_file} was successful!'
        except Exception as er:
            print('During handling a file the next error has arose:', er)
