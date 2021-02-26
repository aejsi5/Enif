# Generated by Django 3.1.5 on 2021-01-16 14:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enif_app', '0006_auto_20210116_1543'),
    ]

    operations = [
        migrations.RenameField(
            model_name='enif_request',
            old_name='Request_Pattern',
            new_name='Pattern',
        ),
        migrations.AlterField(
            model_name='enif_session',
            name='Valid_Until',
            field=models.DateTimeField(default=datetime.datetime(2021, 1, 16, 15, 51, 16, 94607), verbose_name='Gültig bis'),
        ),
    ]