# Generated by Django 5.1.1 on 2024-11-09 18:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0002_alter_cartowashadditionalservice_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableDate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(limit_value=1, message='Month must be at least 1'), django.core.validators.MaxValueValidator(limit_value=12, message='Month cannot be greater than 12')])),
                ('year', models.PositiveSmallIntegerField()),
            ],
            options={
                'verbose_name': 'available date',
                'verbose_name_plural': 'available dates',
                'ordering': ('year', 'month'),
                'unique_together': {('month', 'year')},
            },
        ),
    ]
