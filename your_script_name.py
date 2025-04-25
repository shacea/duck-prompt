import psycopg2
import yaml
import os
from pathlib import Path
from datetime import datetime

# --- Database Connection Details ---
# !!! 보안 경고: 실제 애플리케이션에서는 비밀번호를 코드에 직접 넣지 마세요.
# 환경 변수나 보안 관리 도구를 사용하는 것이 좋습니다.
DB_HOST = "postgresdb.lab.miraker.me"
DB_PORT = 5333
DB_NAME = "duck_agent"
DB_USER = "shacea"
DB_PASSWORD = "alfkzj9389" # 경고: 실제 비밀번호

# --- Config File Path ---
# 이 스크립트가 프로젝트 루트에 있다고 가정합니다.
# 실제 위치에 맞게 경로를 조정하세요.
CONFIG_FILE_PATH = "src/config.yml"

# --- SQL Schema Definition ---
# 이전 단계에서 생성한 SQL 쿼리
SCHEMA_SQL = """
-- 타임스탬프 자동 업데이트를 위한 함수 생성 (존재하지 않을 경우)
CREATE OR REPLACE FUNCTION trigger_set_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 기존 테이블 삭제 (스크립트를 여러 번 실행할 경우)
DROP TABLE IF EXISTS application_config CASCADE;
DROP TABLE IF EXISTS api_key_usage CASCADE;
DROP TABLE IF EXISTS model_rate_limits CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;


-- ==== API 키 테이블 ====
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    api_key TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'google',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER set_api_keys_timestamp
BEFORE UPDATE ON api_keys
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

COMMENT ON TABLE api_keys IS 'Stores individual API keys and their metadata.';
COMMENT ON COLUMN api_keys.api_key IS 'The actual API key string. Sensitive data.';
COMMENT ON COLUMN api_keys.provider IS 'The provider of the API key (e.g., google, anthropic).';
COMMENT ON COLUMN api_keys.description IS 'User-friendly description for the key.';
COMMENT ON COLUMN api_keys.is_active IS 'Flag to enable/disable the key for use.';


-- ==== 모델별 기본 Rate Limit 테이블 ====
CREATE TABLE model_rate_limits (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'google',
    rpm_limit INTEGER NOT NULL,
    daily_limit INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER set_model_rate_limits_timestamp
BEFORE UPDATE ON model_rate_limits
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

COMMENT ON TABLE model_rate_limits IS 'Stores default rate limit information per model.';
COMMENT ON COLUMN model_rate_limits.model_name IS 'Identifier for the language model.';
COMMENT ON COLUMN model_rate_limits.rpm_limit IS 'Default Requests Per Minute limit for the model.';
COMMENT ON COLUMN model_rate_limits.daily_limit IS 'Default Requests Per Day limit for the model.';


-- ==== API 키 사용량 추적 테이블 ====
CREATE TABLE api_key_usage (
    id SERIAL PRIMARY KEY,
    api_key_id INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
    last_api_call_timestamp TIMESTAMPTZ,
    calls_this_minute INTEGER NOT NULL DEFAULT 0,
    minute_start_timestamp TIMESTAMPTZ,
    calls_this_day INTEGER NOT NULL DEFAULT 0,
    day_start_timestamp TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (api_key_id)
);

CREATE TRIGGER set_api_key_usage_timestamp
BEFORE UPDATE ON api_key_usage
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

CREATE INDEX idx_api_key_usage_api_key_id ON api_key_usage(api_key_id);

COMMENT ON TABLE api_key_usage IS 'Tracks the actual usage counts and timestamps for each API key.';
COMMENT ON COLUMN api_key_usage.api_key_id IS 'Foreign key referencing the api_keys table.';
COMMENT ON COLUMN api_key_usage.last_api_call_timestamp IS 'Timestamp of the last successful API call using this key.';
COMMENT ON COLUMN api_key_usage.calls_this_minute IS 'Counter for calls made within the current minute window.';
COMMENT ON COLUMN api_key_usage.minute_start_timestamp IS 'Timestamp marking the beginning of the current minute window for rate limiting.';
COMMENT ON COLUMN api_key_usage.calls_this_day IS 'Counter for calls made within the current day window.';
COMMENT ON COLUMN api_key_usage.day_start_timestamp IS 'Timestamp marking the beginning of the current day window for rate limiting.';


-- ==== 애플리케이션 설정 테이블 ====
CREATE TABLE application_config (
    id SERIAL PRIMARY KEY,
    profile_name TEXT NOT NULL UNIQUE DEFAULT 'default',
    default_system_prompt TEXT,
    allowed_extensions TEXT[],
    excluded_dirs TEXT[],
    default_ignore_list TEXT[],
    gemini_default_model TEXT,
    claude_default_model TEXT,
    gpt_default_model TEXT,
    gemini_available_models TEXT[],
    claude_available_models TEXT[],
    gpt_available_models TEXT[],
    gemini_temperature NUMERIC(3, 2) DEFAULT 0.0,
    gemini_enable_thinking BOOLEAN DEFAULT TRUE,
    gemini_thinking_budget INTEGER DEFAULT 24576,
    gemini_enable_search BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER set_application_config_timestamp
BEFORE UPDATE ON application_config
FOR EACH ROW
EXECUTE FUNCTION trigger_set_timestamp();

COMMENT ON TABLE application_config IS 'Stores application-wide configuration settings, replacing config.yml.';
COMMENT ON COLUMN application_config.profile_name IS 'Identifier for the configuration profile (e.g., default, development).';
COMMENT ON COLUMN application_config.allowed_extensions IS 'Array of allowed file extensions.';
COMMENT ON COLUMN application_config.excluded_dirs IS 'Array of directory/file patterns to exclude.';
COMMENT ON COLUMN application_config.default_ignore_list IS 'Array of default patterns to ignore.';
COMMENT ON COLUMN application_config.gemini_available_models IS 'Array of available Gemini model names.';
COMMENT ON COLUMN application_config.claude_available_models IS 'Array of available Claude model names.';
COMMENT ON COLUMN application_config.gpt_available_models IS 'Array of available GPT model names.';
COMMENT ON COLUMN application_config.gemini_temperature IS 'Generation temperature for Gemini models.';

"""

def create_tables(conn):
    """Creates database tables based on the SCHEMA_SQL."""
    print("Attempting to create database tables...")
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Tables created (or already exist) successfully.")
    except psycopg2.Error as e:
        print(f"Error creating tables: {e}")
        conn.rollback() # Roll back changes on error
        raise # Re-raise the exception to stop the script

def load_config_from_yaml(file_path):
    """Loads configuration from the specified YAML file."""
    print(f"Loading configuration from {file_path}...")
    if not os.path.exists(file_path):
        print(f"Error: Configuration file not found at {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        print("Configuration loaded successfully.")
        return config_data
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error loading config file: {e}")
        return None

def migrate_config_to_db(conn, config_data):
    """Migrates data from the config dictionary to the database."""
    if not config_data:
        print("No configuration data to migrate.")
        return

    print("Starting data migration to database...")
    try:
        with conn.cursor() as cur:
            # 1. Migrate application_config
            print("Migrating application_config...")
            # Handle potential None values and convert sets/lists correctly
            allowed_extensions = list(config_data.get('allowed_extensions') or set())
            excluded_dirs = list(config_data.get('excluded_dirs') or set())
            default_ignore_list = list(config_data.get('default_ignore_list') or [])
            gemini_available = list(config_data.get('gemini_available_models') or [])
            claude_available = list(config_data.get('claude_available_models') or [])
            gpt_available = list(config_data.get('gpt_available_models') or [])

            config_insert_sql = """
                INSERT INTO application_config (
                    profile_name, default_system_prompt, allowed_extensions, excluded_dirs,
                    default_ignore_list, gemini_default_model, claude_default_model,
                    gpt_default_model, gemini_available_models, claude_available_models,
                    gpt_available_models, gemini_temperature, gemini_enable_thinking,
                    gemini_thinking_budget, gemini_enable_search
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (profile_name) DO UPDATE SET
                    default_system_prompt = EXCLUDED.default_system_prompt,
                    allowed_extensions = EXCLUDED.allowed_extensions,
                    excluded_dirs = EXCLUDED.excluded_dirs,
                    default_ignore_list = EXCLUDED.default_ignore_list,
                    gemini_default_model = EXCLUDED.gemini_default_model,
                    claude_default_model = EXCLUDED.claude_default_model,
                    gpt_default_model = EXCLUDED.gpt_default_model,
                    gemini_available_models = EXCLUDED.gemini_available_models,
                    claude_available_models = EXCLUDED.claude_available_models,
                    gpt_available_models = EXCLUDED.gpt_available_models,
                    gemini_temperature = EXCLUDED.gemini_temperature,
                    gemini_enable_thinking = EXCLUDED.gemini_enable_thinking,
                    gemini_thinking_budget = EXCLUDED.gemini_thinking_budget,
                    gemini_enable_search = EXCLUDED.gemini_enable_search,
                    updated_at = NOW();
            """
            cur.execute(config_insert_sql, (
                'default', # profile_name
                config_data.get('default_system_prompt'),
                allowed_extensions,
                excluded_dirs,
                default_ignore_list,
                config_data.get('gemini_default_model'),
                config_data.get('claude_default_model'),
                config_data.get('gpt_default_model'),
                gemini_available,
                claude_available,
                gpt_available,
                config_data.get('gemini_temperature', 0.0),
                config_data.get('gemini_enable_thinking', True),
                config_data.get('gemini_thinking_budget', 0),
                config_data.get('gemini_enable_search', True)
            ))
            print("  - application_config migrated.")

            # 2. Migrate API Keys and initialize usage
            print("Migrating API keys and initializing usage...")

            # Gemini Key
            gemini_key = config_data.get('gemini_api_key')
            if gemini_key:
                key_id = insert_api_key(cur, gemini_key, 'google', 'Default Gemini Key from config.yml')
                if key_id:
                    initialize_key_usage(cur, key_id)
                    print(f"  - Gemini key migrated (ID: {key_id}).")
                else:
                    print("  - Failed to migrate Gemini key.")


            # Anthropic Key
            anthropic_key = config_data.get('anthropic_api_key')
            if anthropic_key:
                 key_id = insert_api_key(cur, anthropic_key, 'anthropic', 'Default Anthropic Key from config.yml')
                 if key_id:
                     initialize_key_usage(cur, key_id)
                     print(f"  - Anthropic key migrated (ID: {key_id}).")
                 else:
                     print("  - Failed to migrate Anthropic key.")

            # 3. Migrate Model Rate Limits (from provided info, not config.yml)
            print("Migrating model rate limits...")
            # These values are from your initial prompt, not config.yml
            model_limits = [
                ('gemini-2.5-pro-preview-03-25', 'google', 5, 25, 'Provided limit info'),
                ('gemini-2.5-flash-preview-04-17', 'google', 10, 500, 'Provided limit info')
            ]
            limit_insert_sql = """
                INSERT INTO model_rate_limits (model_name, provider, rpm_limit, daily_limit, notes)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (model_name) DO NOTHING;
            """
            for limit_data in model_limits:
                cur.execute(limit_insert_sql, limit_data)
            print("  - Model rate limits migrated.")


        conn.commit()
        print("Data migration completed successfully.")

    except psycopg2.Error as e:
        print(f"Error during data migration: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during migration: {e}")
        conn.rollback()


def insert_api_key(cur, api_key, provider, description):
    """Inserts an API key if it doesn't exist, returns its ID."""
    key_insert_sql = """
        INSERT INTO api_keys (api_key, provider, description, is_active)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (api_key) DO UPDATE SET
            provider = EXCLUDED.provider,
            description = EXCLUDED.description,
            is_active = TRUE, -- Ensure it's active on update
            updated_at = NOW()
        RETURNING id;
    """
    try:
        cur.execute(key_insert_sql, (api_key, provider, description))
        result = cur.fetchone()
        return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Error inserting/updating API key for {provider}: {e}")
        return None

def initialize_key_usage(cur, api_key_id):
    """Initializes the usage record for a given API key ID if it doesn't exist."""
    usage_insert_sql = """
        INSERT INTO api_key_usage (api_key_id, minute_start_timestamp, day_start_timestamp)
        VALUES (%s, NOW(), NOW())
        ON CONFLICT (api_key_id) DO NOTHING;
    """
    try:
        cur.execute(usage_insert_sql, (api_key_id,))
    except psycopg2.Error as e:
        print(f"Error initializing usage for API key ID {api_key_id}: {e}")


def main():
    """Main function to connect, setup DB, and migrate data."""
    conn = None
    try:
        # 1. Connect to the database
        print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Database connection successful.")

        # 2. Create tables
        create_tables(conn)

        # 3. Load configuration from YAML
        config_data = load_config_from_yaml(CONFIG_FILE_PATH)

        # 4. Migrate data to the database
        if config_data:
            migrate_config_to_db(conn, config_data)
        else:
            print("Skipping migration due to config loading error.")

    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    # 스크립트 실행 전 필요한 라이브러리 설치 확인
    try:
        import psycopg2
        import yaml
    except ImportError as e:
        print(f"Error: Required library not found: {e.name}.")
        print("Please install required libraries:")
        print("pip install psycopg2-binary PyYAML") # 또는 uv install psycopg2-binary PyYAML
        exit(1)

    main()