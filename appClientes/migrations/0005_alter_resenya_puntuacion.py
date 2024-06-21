# Generated by Django 5.0.6 on 2024-06-13 02:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appClientes', '0004_alter_resenya_resenya'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resenya',
            name='puntuacion',
            field=models.FloatField(help_text='Ingrese una puntuacion de 1 a 5.', validators=[django.core.validators.MinLengthValidator(1), django.core.validators.MaxLengthValidator(5)]),
        ),
    ]
