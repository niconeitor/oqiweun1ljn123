# Generated by Django 5.0.6 on 2024-06-13 14:49

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appClientes', '0006_alter_resenya_puntuacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resenya',
            name='puntuacion',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
