# Generated by Django 5.2.4 on 2025-07-14 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operations', '0005_walletfunding'),
    ]

    operations = [
        migrations.AlterField(
            model_name='walletfunding',
            name='transaction_type',
            field=models.CharField(default='Deposit', max_length=10),
        ),
    ]
