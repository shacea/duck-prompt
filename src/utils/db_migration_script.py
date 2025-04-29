
import psycopg2
import logging
from typing import Dict, Any, Optional, List

# --- Database Connection Details (from db_service.py or environment) ---
DB_HOST = "postgresdb.lab.miraker.me"
DB_PORT = 5333
DB_NAME = "duck_agent"
DB_USER = "shacea"
DB_PASSWORD = "alfkzj9389" # Warning: Hardcoded password

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_migration():
    """Performs the database migration: adds usage columns to api_keys, migrates data, drops api_key_usage."""
    conn = None
    try:
        # 1. Connect to the database
        logger.info(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = False # Start transaction
        logger.info("Database connection successful.")
        cur = conn.cursor()

        # 2. Add new columns to api_keys table if they don't exist
        logger.info("Adding usage tracking columns to api_keys table (if they don't exist)...")
        columns_to_add = [
            ("last_api_call_timestamp", "TIMESTAMPTZ", "NULL"),
            ("calls_this_minute", "INTEGER", "NOT NULL DEFAULT 0"),
            ("minute_start_timestamp", "TIMESTAMPTZ", "NULL"),
            ("calls_this_day", "INTEGER", "NOT NULL DEFAULT 0"),
            ("day_start_timestamp", "TIMESTAMPTZ", "NULL")
        ]
        for col_name, col_type, col_constraint in columns_to_add:
            try:
                alter_sql = f"ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS {col_name} {col_type} {col_constraint};"
                logger.debug(f"Executing: {alter_sql}")
                cur.execute(alter_sql)
                logger.info(f"Column '{col_name}' added or already exists in api_keys.")
            except psycopg2.Error as e:
                logger.error(f"Error adding column '{col_name}' to api_keys: {e}")
                raise # Stop migration if altering fails

        # 3. Check if api_key_usage table exists before attempting migration
        cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'api_key_usage');")
        usage_table_exists = cur.fetchone()[0]

        if usage_table_exists:
            logger.info("api_key_usage table exists. Migrating data...")

            # 4. Fetch data from api_key_usage
            logger.info("Fetching data from api_key_usage table...")
            try:
                cur.execute("""
                    SELECT api_key_id, last_api_call_timestamp, calls_this_minute,
                           minute_start_timestamp, calls_this_day, day_start_timestamp
                    FROM api_key_usage;
                """)
                usage_data = cur.fetchall()
                logger.info(f"Fetched {len(usage_data)} rows from api_key_usage.")
            except psycopg2.Error as e:
                logger.error(f"Error fetching data from api_key_usage: {e}")
                raise

            # 5. Update api_keys table with migrated data
            logger.info("Updating api_keys table with migrated usage data...")
            update_count = 0
            for row in usage_data:
                key_id, last_call, calls_min, min_start, calls_day, day_start = row
                try:
                    update_sql = """
                        UPDATE api_keys
                        SET last_api_call_timestamp = %s,
                            calls_this_minute = %s,
                            minute_start_timestamp = %s,
                            calls_this_day = %s,
                            day_start_timestamp = %s,
                            updated_at = NOW()
                        WHERE id = %s;
                    """
                    cur.execute(update_sql, (last_call, calls_min, min_start, calls_day, day_start, key_id))
                    if cur.rowcount == 1:
                        update_count += 1
                    else:
                        logger.warning(f"API key ID {key_id} not found in api_keys table during migration update.")
                except psycopg2.Error as e:
                    logger.error(f"Error updating api_keys for key_id {key_id}: {e}")
                    # Decide whether to continue or stop on error
                    # raise # Uncomment to stop on first error
            logger.info(f"Successfully updated {update_count} rows in api_keys with usage data.")

            # 6. Drop the api_key_usage table
            logger.info("Dropping api_key_usage table...")
            try:
                cur.execute("DROP TABLE IF EXISTS api_key_usage;")
                logger.info("api_key_usage table dropped successfully.")
            except psycopg2.Error as e:
                logger.error(f"Error dropping api_key_usage table: {e}")
                raise
        else:
            logger.info("api_key_usage table does not exist. Skipping data migration and table drop.")

        # 7. Commit transaction
        conn.commit()
        logger.info("Database migration completed successfully.")

    except (Exception, psycopg2.Error) as error:
        logger.error(f"Database migration failed: {error}", exc_info=True)
        if conn:
            conn.rollback()
            logger.info("Transaction rolled back.")
    finally:
        if conn:
            cur.close()
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    run_migration()
