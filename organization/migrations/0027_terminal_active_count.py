# Generated by Django 4.0.6 on 2024-05-13 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0026_rename_is_estimate_table_is_estimated'),
    ]

    operations = [
        migrations.AddField(
            model_name='terminal',
            name='active_count',
            field=models.IntegerField(default=0),
        ),
    ]
