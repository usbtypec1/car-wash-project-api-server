# Generated by Django 5.1.1 on 2024-11-01 13:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shifts', '0002_alter_cartowash_number'),
        ('staff', '0004_remove_staff_shift_schedule_month_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='shift',
            unique_together={('staff', 'date')},
        ),
    ]