import os
from django.core.management.base import BaseCommand
from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    """Loading data to ingredient model."""
    help = 'Load csv files to ingredient model.'

    def handle(self, *args, **kwargs):
        path_to_data = f'{settings.BASE_DIR}/../../data/ingredients.csv'
        csv_file = os.path.split(path_to_data)

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
                return f'Unpacking of {csv_file[-1]} was successful!'
        except Exception as er:
            raise('During handling a file the next error has arose:', er)
