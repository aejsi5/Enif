# Generated by Django 3.1.5 on 2021-01-16 14:18

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enif_app', '0004_whitelist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enif_session',
            name='Valid_Until',
            field=models.DateTimeField(default=datetime.datetime(2021, 1, 16, 15, 23, 15, 922908), verbose_name='Gültig bis'),
        ),
    ]