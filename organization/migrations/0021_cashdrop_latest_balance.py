# Generated by Django 4.0.6 on 2023-12-04 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0020_alter_cashdrop_is_end_day'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashdrop',
            name='latest_balance',
            field=models.FloatField(default=0.0),
        ),
    ]
