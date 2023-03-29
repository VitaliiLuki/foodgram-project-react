import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag


class Command(BaseCommand):
    """Loading data to ingredient model."""
    help = 'Load csv files to ingredient model.'

    def handle(self, *args, **kwargs):
        path_to_data = f'{settings.BASE_DIR}/ingredients_tags_data'
        model_and_filename = [
            {
                'model': Ingredient,
                'filename': 'ingredients.csv'
            },
            {
                'model': Tag,
                'filename': 'tags.csv'
            },
        ]
        print(path_to_data)
        for el in model_and_filename:
            csv_file = Path(path_to_data, el['filename'])
            try:
                with open(f'{csv_file}', 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    el['model'].objects.all().delete()
                    objs = [el['model'](**row) for row in reader]
                    el['model'].objects.bulk_create(objs)
                    print(f'Unpacking of {el["filename"]} was successful!')
            except Exception as er:
                raise ('An error occurred while unpacking the file', er)
