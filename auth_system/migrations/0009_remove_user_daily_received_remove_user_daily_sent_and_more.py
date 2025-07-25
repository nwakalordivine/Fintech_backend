# Generated by Django 5.2.4 on 2025-07-12 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_system", "0008_delete_sendemail_remove_user_is_verified_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="daily_received",
        ),
        migrations.RemoveField(
            model_name="user",
            name="daily_sent",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_limit_reset",
        ),
        migrations.AddField(
            model_name="wallet",
            name="daily_received",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
        migrations.AddField(
            model_name="wallet",
            name="daily_sent",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=12),
        ),
        migrations.AddField(
            model_name="wallet",
            name="last_limit_reset",
            field=models.DateField(blank=True, null=True),
        ),
    ]
