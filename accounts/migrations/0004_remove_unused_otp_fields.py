# Generated manually to clean up unused OTP fields from production database

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_check_in_interval_months_user_grace_period_days_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # Drop columns if they exist (PostgreSQL syntax)
                "ALTER TABLE accounts_user DROP COLUMN IF EXISTS otp_attempts;",
                "ALTER TABLE accounts_user DROP COLUMN IF EXISTS otp_code;",
                "ALTER TABLE accounts_user DROP COLUMN IF EXISTS otp_created_at;",
                "ALTER TABLE accounts_user DROP COLUMN IF EXISTS is_email_verified;",
            ],
            reverse_sql=[
                # No reverse - these columns shouldn't exist
            ],
        ),
    ]
