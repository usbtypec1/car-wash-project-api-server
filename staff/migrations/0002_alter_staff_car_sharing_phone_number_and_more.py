# Generated by Django 5.1.1 on 2024-11-09 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='staff',
            name='car_sharing_phone_number',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='staff',
            name='console_phone_number',
            field=models.CharField(max_length=20),
        ),
    ]
