# Generated by Django 4.1.7 on 2023-03-04 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_new_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='new_password',
            field=models.CharField(blank=True, default=None, max_length=150, null=True),
        ),
    ]
