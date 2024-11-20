# Generated by Django 5.1.1 on 2024-11-20 09:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('staff', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Penalty',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=255)),
                ('amount', models.PositiveIntegerField()),
                ('consequence', models.CharField(blank=True, choices=[('dismissal', 'dismissal'), ('warn', 'warn')], max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='staff.staff')),
            ],
            options={
                'verbose_name': 'penalty',
                'verbose_name_plural': 'penalties',
            },
        ),
        migrations.CreateModel(
            name='Surcharge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(max_length=255)),
                ('amount', models.PositiveIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='staff.staff')),
            ],
            options={
                'verbose_name': 'surcharge',
                'verbose_name_plural': 'surcharges',
            },
        ),
    ]
