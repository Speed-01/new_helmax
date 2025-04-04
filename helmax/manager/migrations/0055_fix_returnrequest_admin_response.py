# Generated manually to fix migration issues

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0054_alter_otp_expiration_time_and_more'),
    ]

    operations = [
        # Use SQL to ensure the admin_response field is properly set up as a TextField
        migrations.RunSQL(
            # Forward SQL: Ensure the field exists as a TextField
            """
            DO $$
            BEGIN
                -- Check if admin_response_id column exists and drop it if it does
                IF EXISTS (SELECT 1 FROM information_schema.columns 
                          WHERE table_name = 'manager_returnrequest' 
                          AND column_name = 'admin_response_id') THEN
                    ALTER TABLE manager_returnrequest DROP COLUMN admin_response_id;
                END IF;
                
                -- Check if admin_response column exists, if not add it
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                             WHERE table_name = 'manager_returnrequest' 
                             AND column_name = 'admin_response') THEN
                    ALTER TABLE manager_returnrequest ADD COLUMN admin_response TEXT;
                END IF;
            END
            $$;
            """,
            # Reverse SQL (empty as this is a fix)
            """
            """
        ),
    ]