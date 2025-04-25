import psycopg2
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
DROP TABLE IF EXISTS gemini_api_logs CASCADE; -- 추가: Gemini 로그 테이블 삭제

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

-- ==== Gemini API 로그 테이블 ====
CREATE TABLE gemini_api_logs (
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

CREATE INDEX idx_gemini_api_logs_request_timestamp ON gemini_api_logs(request_timestamp);
CREATE INDEX idx_gemini_api_logs_api_key_id ON gemini_api_logs(api_key_id);

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

def main():
    """Main function to connect and setup/update DB schema."""
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
