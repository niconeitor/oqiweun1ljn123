# Generated by Django 5.0.6 on 2024-06-13 14:52

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appClientes', '0007_alter_resenya_puntuacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resenya',
            name='puntuacion',
            field=models.FloatField(help_text='Puntuación entre 1 y 5', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)]),
        ),
    ]
