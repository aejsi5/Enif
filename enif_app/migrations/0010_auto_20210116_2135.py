# Generated by Django 3.1.5 on 2021-01-16 20:35

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enif_app', '0009_auto_20210116_2134'),
    ]

    operations = [
        migrations.RenameField(
            model_name='enif_request',
            old_name='Intent_ACCURACY',
            new_name='Intent_Accuracy',
        ),
        migrations.AlterField(
            model_name='enif_session',
            name='Valid_Until',
            field=models.DateTimeField(default=datetime.datetime(2021, 1, 16, 21, 45, 16, 775012), verbose_name='Gültig bis'),
        ),
    ]
