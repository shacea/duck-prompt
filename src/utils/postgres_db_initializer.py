
import psycopg2
import os
import yaml # YAML 파싱을 위해 추가
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List # 타입 힌트 추가

# --- Database Connection Details ---
# 환경 변수나 보안 관리 도구를 사용하는 것이 좋습니다.
DB_HOST = "postgresdb.lab.miraker.me"
DB_PORT = 5333
DB_NAME = "duck_agent"
DB_USER = "shacea"
DB_PASSWORD = "alfkzj9389" # 경고: 실제 비밀번호

# --- Project Root and Config File Path ---
# helpers.py의 get_project_root()를 사용하여 프로젝트 루트를 찾습니다.
# 이 파일이 src/utils/ 에 있으므로, 프로젝트 루트는 두 단계 위입니다.
try:
    PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
except NameError:
    # __file__이 정의되지 않은 경우 (예: 인터프리터에서 직접 실행)
    PROJECT_ROOT = Path('.').resolve()

CONFIG_FILE_PATH = PROJECT_ROOT / "src" / "config.yml"


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

-- 기존 테이블 삭제 (스크립트를 여러 번 실행할 경우) - 주의: 데이터 손실 발생
-- DROP TABLE IF EXISTS application_config CASCADE;
-- DROP TABLE IF EXISTS api_key_usage CASCADE;
-- DROP TABLE IF EXISTS model_rate_limits CASCADE;
-- DROP TABLE IF EXISTS api_keys CASCADE;
-- DROP TABLE IF EXISTS gemini_api_logs CASCADE; -- 추가: Gemini 로그 테이블 삭제

-- ==== API 키 테이블 ====
-- 테이블이 존재하지 않을 경우에만 생성 (IF NOT EXISTS 추가)
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    api_key TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'google',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 트리거가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_api_keys_timestamp') THEN
        CREATE TRIGGER set_api_keys_timestamp
        BEFORE UPDATE ON api_keys
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    END IF;
END $$;

COMMENT ON TABLE api_keys IS 'Stores individual API keys and their metadata.';
COMMENT ON COLUMN api_keys.api_key IS 'The actual API key string. Sensitive data.';
COMMENT ON COLUMN api_keys.provider IS 'The provider of the API key (e.g., google, anthropic).';
COMMENT ON COLUMN api_keys.description IS 'User-friendly description for the key.';
COMMENT ON COLUMN api_keys.is_active IS 'Flag to enable/disable the key for use.';


-- ==== 모델별 기본 Rate Limit 테이블 ====
-- 테이블이 존재하지 않을 경우에만 생성
CREATE TABLE IF NOT EXISTS model_rate_limits (
    id SERIAL PRIMARY KEY,
    model_name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL DEFAULT 'google',
    rpm_limit INTEGER NOT NULL,
    daily_limit INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 트리거가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_model_rate_limits_timestamp') THEN
        CREATE TRIGGER set_model_rate_limits_timestamp
        BEFORE UPDATE ON model_rate_limits
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    END IF;
END $$;

COMMENT ON TABLE model_rate_limits IS 'Stores default rate limit information per model.';
COMMENT ON COLUMN model_rate_limits.model_name IS 'Identifier for the language model.';
COMMENT ON COLUMN model_rate_limits.rpm_limit IS 'Default Requests Per Minute limit for the model.';
COMMENT ON COLUMN model_rate_limits.daily_limit IS 'Default Requests Per Day limit for the model.';


-- ==== API 키 사용량 추적 테이블 ====
-- 테이블이 존재하지 않을 경우에만 생성
CREATE TABLE IF NOT EXISTS api_key_usage (
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

-- 트리거가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_api_key_usage_timestamp') THEN
        CREATE TRIGGER set_api_key_usage_timestamp
        BEFORE UPDATE ON api_key_usage
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    END IF;
END $$;

-- 인덱스가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'idx_api_key_usage_api_key_id' AND n.nspname = 'public') THEN
        CREATE INDEX idx_api_key_usage_api_key_id ON api_key_usage(api_key_id);
    END IF;
END $$;

COMMENT ON TABLE api_key_usage IS 'Tracks the actual usage counts and timestamps for each API key.';
COMMENT ON COLUMN api_key_usage.api_key_id IS 'Foreign key referencing the api_keys table.';
COMMENT ON COLUMN api_key_usage.last_api_call_timestamp IS 'Timestamp of the last successful API call using this key.';
COMMENT ON COLUMN api_key_usage.calls_this_minute IS 'Counter for calls made within the current minute window.';
COMMENT ON COLUMN api_key_usage.minute_start_timestamp IS 'Timestamp marking the beginning of the current minute window for rate limiting.';
COMMENT ON COLUMN api_key_usage.calls_this_day IS 'Counter for calls made within the current day window.';
COMMENT ON COLUMN api_key_usage.day_start_timestamp IS 'Timestamp marking the beginning of the current day window for rate limiting.';


-- ==== 애플리케이션 설정 테이블 ====
-- 테이블이 존재하지 않을 경우에만 생성
CREATE TABLE IF NOT EXISTS application_config (
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

-- 트리거가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_application_config_timestamp') THEN
        CREATE TRIGGER set_application_config_timestamp
        BEFORE UPDATE ON application_config
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_timestamp();
    END IF;
END $$;

COMMENT ON TABLE application_config IS 'Stores application-wide configuration settings, replacing config.yml.';
COMMENT ON COLUMN application_config.profile_name IS 'Identifier for the configuration profile (e.g., default, development).';
COMMENT ON COLUMN application_config.allowed_extensions IS 'Array of allowed file extensions.';
COMMENT ON COLUMN application_config.excluded_dirs IS 'Array of directory/file patterns to exclude.';
COMMENT ON COLUMN application_config.default_ignore_list IS 'Array of default patterns to ignore.';
COMMENT ON COLUMN application_config.gemini_available_models IS 'Array of available Gemini model names.';
COMMENT ON COLUMN application_config.claude_available_models IS 'Array of available Claude model names.';
COMMENT ON COLUMN application_config.gpt_available_models IS 'Array of available GPT model names.';
COMMENT ON COLUMN application_config.gemini_temperature IS 'Generation temperature for Gemini models.';

-- ==== Gemini API 로그 테이블 ====
-- 테이블이 존재하지 않을 경우에만 생성
CREATE TABLE IF NOT EXISTS gemini_api_logs (
    id SERIAL PRIMARY KEY,
    request_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_timestamp TIMESTAMPTZ,
    model_name TEXT,
    request_prompt TEXT,
    request_attachments JSONB,
    response_text TEXT,
    response_xml TEXT,
    response_summary TEXT,
    error_message TEXT,
    elapsed_time_ms INTEGER,
    token_count INTEGER,
    api_key_id INTEGER REFERENCES api_keys(id) ON DELETE SET NULL
);

-- 인덱스가 존재하지 않을 경우에만 생성
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'idx_gemini_api_logs_request_timestamp' AND n.nspname = 'public') THEN
        CREATE INDEX idx_gemini_api_logs_request_timestamp ON gemini_api_logs(request_timestamp);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE c.relname = 'idx_gemini_api_logs_api_key_id' AND n.nspname = 'public') THEN
        CREATE INDEX idx_gemini_api_logs_api_key_id ON gemini_api_logs(api_key_id);
    END IF;
END $$;

COMMENT ON TABLE gemini_api_logs IS 'Stores logs of requests and responses to the Gemini API.';
COMMENT ON COLUMN gemini_api_logs.request_timestamp IS 'Timestamp when the request was initiated.';
COMMENT ON COLUMN gemini_api_logs.response_timestamp IS 'Timestamp when the response was received.';
COMMENT ON COLUMN gemini_api_logs.model_name IS 'The specific Gemini model used for the request.';
COMMENT ON COLUMN gemini_api_logs.request_prompt IS 'The text prompt sent to the API.';
COMMENT ON COLUMN gemini_api_logs.request_attachments IS 'JSONB data containing metadata about attached files/images (e.g., name, type, path).';
COMMENT ON COLUMN gemini_api_logs.response_text IS 'The raw text response from the Gemini API.';
COMMENT ON COLUMN gemini_api_logs.response_xml IS 'The parsed XML part of the response, if applicable.';
COMMENT ON COLUMN gemini_api_logs.response_summary IS 'The parsed summary part of the response, if applicable.';
COMMENT ON COLUMN gemini_api_logs.error_message IS 'Error message if the API call failed.';
COMMENT ON COLUMN gemini_api_logs.elapsed_time_ms IS 'Total time taken for the API call in milliseconds.';
COMMENT ON COLUMN gemini_api_logs.token_count IS 'Calculated token count for the request/response.';
COMMENT ON COLUMN gemini_api_logs.api_key_id IS 'Foreign key referencing the api_key used for the request.';

"""

def create_tables(conn):
    """Creates database tables based on the SCHEMA_SQL."""
    print("Attempting to create/update database tables...")
    try:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
        conn.commit()
        print("Tables created/updated (or already exist) successfully.")
    except psycopg2.Error as e:
        print(f"Error creating/updating tables: {e}")
        conn.rollback() # Roll back changes on error
        raise # Re-raise the exception to stop the script

def load_yaml_config(file_path: Path) -> Optional[Dict[str, Any]]:
    """Loads configuration from a YAML file."""
    if not file_path.exists():
        print(f"Error: Configuration file not found at {file_path}")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"Configuration loaded successfully from {file_path}")
        return config
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading configuration file {file_path}: {e}")
        return None

def insert_or_update_config(conn, config_data: Dict[str, Any]):
    """Inserts or updates the 'default' profile in the application_config table."""
    print("Attempting to insert/update application configuration...")
    profile_name = 'default' # Assuming we always update the default profile

    # Prepare data for insertion/update, handling potential missing keys and types
    # Convert sets from YAML (!!set) to lists for PostgreSQL TEXT[]
    allowed_extensions = list(config_data.get('allowed_extensions', set()))
    excluded_dirs = list(config_data.get('excluded_dirs', set()))
    default_ignore_list = list(config_data.get('default_ignore_list', []))
    gemini_available_models = list(config_data.get('gemini_available_models', []))
    claude_available_models = list(config_data.get('claude_available_models', []))
    gpt_available_models = list(config_data.get('gpt_available_models', []))

    # Ensure boolean values are correctly interpreted
    gemini_enable_thinking = bool(config_data.get('gemini_enable_thinking', True))
    gemini_enable_search = bool(config_data.get('gemini_enable_search', True))

    # Ensure numeric values are correctly interpreted, providing defaults
    try:
        gemini_temperature = float(config_data.get('gemini_temperature', 0.0))
    except (ValueError, TypeError):
        gemini_temperature = 0.0
    try:
        gemini_thinking_budget = int(config_data.get('gemini_thinking_budget', 24576))
    except (ValueError, TypeError):
        gemini_thinking_budget = 24576

    # SQL query using ON CONFLICT for upsert
    sql = """
        INSERT INTO application_config (
            profile_name, default_system_prompt, allowed_extensions, excluded_dirs,
            default_ignore_list, gemini_default_model, claude_default_model, gpt_default_model,
            gemini_available_models, claude_available_models, gpt_available_models,
            gemini_temperature, gemini_enable_thinking, gemini_thinking_budget, gemini_enable_search
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
    params = (
        profile_name,
        config_data.get('default_system_prompt'),
        allowed_extensions,
        excluded_dirs,
        default_ignore_list,
        config_data.get('gemini_default_model'),
        config_data.get('claude_default_model'),
        config_data.get('gpt_default_model'),
        gemini_available_models,
        claude_available_models,
        gpt_available_models,
        gemini_temperature,
        gemini_enable_thinking,
        gemini_thinking_budget,
        gemini_enable_search
    )

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        print(f"Application configuration for profile '{profile_name}' inserted/updated successfully.")
    except psycopg2.Error as e:
        print(f"Error inserting/updating application configuration: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during config update: {e}")
        conn.rollback()

def insert_or_update_api_key(conn, api_key: str, provider: str):
    """Inserts or updates an API key in the api_keys table."""
    if not api_key:
        print(f"Skipping API key insertion/update for {provider}: Key is empty.")
        return

    print(f"Attempting to insert/update API key for provider: {provider}...")
    sql = """
        INSERT INTO api_keys (api_key, provider, is_active)
        VALUES (%s, %s, %s)
        ON CONFLICT (api_key) DO UPDATE SET
            provider = EXCLUDED.provider,
            is_active = EXCLUDED.is_active,
            updated_at = NOW();
    """
    params = (api_key, provider, True) # Always set as active when loading from config

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        print(f"API key for provider '{provider}' inserted/updated successfully.")
    except psycopg2.Error as e:
        print(f"Error inserting/updating API key for {provider}: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during API key update for {provider}: {e}")
        conn.rollback()

def insert_or_update_rate_limit(conn, model_name: str, provider: str, rpm_limit: int, daily_limit: int, notes: Optional[str] = None):
    """Inserts or updates a model's rate limit in the model_rate_limits table."""
    print(f"Attempting to insert/update rate limit for model: {model_name}...")
    sql = """
        INSERT INTO model_rate_limits (model_name, provider, rpm_limit, daily_limit, notes)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (model_name) DO UPDATE SET
            provider = EXCLUDED.provider,
            rpm_limit = EXCLUDED.rpm_limit,
            daily_limit = EXCLUDED.daily_limit,
            notes = EXCLUDED.notes,
            updated_at = NOW();
    """
    params = (model_name, provider, rpm_limit, daily_limit, notes)

    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        print(f"Rate limit for model '{model_name}' inserted/updated successfully.")
    except psycopg2.Error as e:
        print(f"Error inserting/updating rate limit for {model_name}: {e}")
        conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during rate limit update for {model_name}: {e}")
        conn.rollback()

def main():
    """Main function to connect, setup/update DB schema, and load config."""
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

        # 2. Create/Update tables based on SCHEMA_SQL
        create_tables(conn)
        print("Database schema setup/update complete.")

        # 3. Load configuration from config.yml
        print(f"Loading configuration from: {CONFIG_FILE_PATH}")
        config = load_yaml_config(CONFIG_FILE_PATH)

        if config:
            # 4. Insert/Update application_config table
            insert_or_update_config(conn, config)

            # 5. Insert/Update api_keys table
            gemini_key = config.get('gemini_api_key')
            anthropic_key = config.get('anthropic_api_key')
            # openai_key = config.get('openai_api_key') # If needed in the future

            if gemini_key:
                insert_or_update_api_key(conn, gemini_key, 'google')
            if anthropic_key:
                insert_or_update_api_key(conn, anthropic_key, 'anthropic')
            # if openai_key:
            #     insert_or_update_api_key(conn, openai_key, 'openai')

            print("Configuration data loaded into database.")

            # 6. Insert/Update model_rate_limits table (based on user request)
            print("Inserting/Updating specific model rate limits...")
            insert_or_update_rate_limit(conn, 'gemini-2.5-pro-preview-03-25', 'google', 5, 25, 'Gemini Pro Preview Rate Limit')
            insert_or_update_rate_limit(conn, 'gemini-2.5-flash-preview-04-17', 'google', 10, 500, 'Gemini Flash Preview Rate Limit')
            print("Model rate limits updated.")

        else:
            print("Skipping database update due to configuration loading failure.")

    except psycopg2.OperationalError as e:
        print(f"Database connection failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
