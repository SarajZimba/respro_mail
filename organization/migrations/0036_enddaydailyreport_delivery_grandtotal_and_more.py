# Generated by Django 4.0.6 on 2024-06-10 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0035_organization_loyalty_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='enddaydailyreport',
            name='delivery_grandtotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='delivery_nettotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='delivery_vattotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='dine_grandtotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='dine_nettotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='dine_vattotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='takeaway_grandtotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='takeaway_nettotal',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='enddaydailyreport',
            name='takeaway_vattotal',
            field=models.FloatField(default=0),
        ),
    ]
