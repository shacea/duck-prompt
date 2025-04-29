### api_keys

| Column                  | Type                     | Comment                                                | PK  | Nullable | Default        |
| :---------------------- | :----------------------- | :----------------------------------------------------- | :-- | :------- | :------------- |
| id                      | integer                  |                                                        | YES | NO       |                |
| api_key                 | text                     | The actual API key string. Sensitive data.             |     | NO       |                |
| provider                | text                     | The provider of the API key (e.g., google, anthropic). |     | NO       | 'google'::text |
| description             | text                     | User-friendly description for the key.                 |     | YES      |                |
| is_active               | boolean                  | Flag to enable/disable the key for use.                |     | NO       | true           |
| created_at              | timestamp with time zone |                                                        |     | NO       | now()          |
| updated_at              | timestamp with time zone |                                                        |     | NO       | now()          |
| last_api_call_timestamp | timestamp with time zone |                                                        |     | YES      |                |
| calls_this_minute       | integer                  |                                                        |     | NO       | 0              |
| minute_start_timestamp  | timestamp with time zone |                                                        |     | YES      |                |
| calls_this_day          | integer                  |                                                        |     | NO       | 0              |
| day_start_timestamp     | timestamp with time zone |                                                        |     | YES      |                |

### application_config

| Column                  | Type                     | Comment                                                                | PK  | Nullable | Default         |
| :---------------------- | :----------------------- | :--------------------------------------------------------------------- | :-- | :------- | :-------------- |
| id                      | integer                  |                                                                        | YES | NO       |                 |
| profile_name            | text                     | Identifier for the configuration profile (e.g., default, development). |     | NO       | 'default'::text |
| default_system_prompt   | text                     |                                                                        |     | YES      |                 |
| allowed_extensions      | text[]                   | Array of allowed file extensions.                                      |     | YES      |                 |
| excluded_dirs           | text[]                   | Array of directory/file patterns to exclude.                           |     | YES      |                 |
| default_ignore_list     | text[]                   | Array of default patterns to ignore.                                   |     | YES      |                 |
| gemini_default_model    | text                     |                                                                        |     | YES      |                 |
| claude_default_model    | text                     |                                                                        |     | YES      |                 |
| gpt_default_model       | text                     |                                                                        |     | YES      |                 |
| gemini_available_models | text[]                   | Array of available Gemini model names.                                 |     | YES      |                 |
| claude_available_models | text[]                   | Array of available Claude model names.                                 |     | YES      |                 |
| gpt_available_models    | text[]                   | Array of available GPT model names.                                    |     | YES      |                 |
| gemini_temperature      | numeric(3,2)             | Generation temperature for Gemini models.                              |     | YES      | 0.0             |
| gemini_enable_thinking  | boolean                  |                                                                        |     | YES      | true            |
| gemini_thinking_budget  | integer                  |                                                                        |     | YES      | 24576           |
| gemini_enable_search    | boolean                  |                                                                        |     | YES      | true            |
| created_at              | timestamp with time zone |                                                                        |     | NO       | now()           |
| updated_at              | timestamp with time zone |                                                                        |     | NO       | now()           |

### gemini_api_logs

| Column              | Type                     | Comment                                                                              | PK  | Nullable | Default |
| :------------------ | :----------------------- | :----------------------------------------------------------------------------------- | :-- | :------- | :------ |
| id                  | integer                  |                                                                                      | YES | NO       |         |
| request_timestamp   | timestamp with time zone | Timestamp when the request was initiated.                                            |     | NO       | now()   |
| response_timestamp  | timestamp with time zone | Timestamp when the response was received.                                            |     | YES      |         |
| model_name          | text                     | The specific Gemini model used for the request.                                      |     | YES      |         |
| request_prompt      | text                     | The text prompt sent to the API.                                                     |     | YES      |         |
| request_attachments | jsonb                    | JSONB data containing metadata about attached files/images (e.g., name, type, path). |     | YES      |         |
| response_text       | text                     | The raw text response from the Gemini API.                                           |     | YES      |         |
| response_xml        | text                     | The parsed XML part of the response, if applicable.                                  |     | YES      |         |
| response_summary    | text                     | The parsed summary part of the response, if applicable.                              |     | YES      |         |
| error_message       | text                     | Error message if the API call failed.                                                |     | YES      |         |
| elapsed_time_ms     | integer                  | Total time taken for the API call in milliseconds.                                   |     | YES      |         |
| token_count         | integer                  | Calculated token count for the request/response.                                     |     | YES      |         |
| api_key_id          | integer                  | Foreign key referencing the api_key used for the request.                            |     | YES      |         |

### model_rate_limits

| Column      | Type                     | Comment                                          | PK  | Nullable | Default        |
| :---------- | :----------------------- | :----------------------------------------------- | :-- | :------- | :------------- |
| id          | integer                  |                                                  | YES | NO       |                |
| model_name  | text                     | Identifier for the language model.               |     | NO       |                |
| provider    | text                     |                                                  |     | NO       | 'google'::text |
| rpm_limit   | integer                  | Default Requests Per Minute limit for the model. |     | NO       |                |
| daily_limit | integer                  | Default Requests Per Day limit for the model.    |     | NO       |                |
| notes       | text                     |                                                  |     | YES      |                |
| created_at  | timestamp with time zone |                                                  |     | NO       | now()          |
| updated_at  | timestamp with time zone |                                                  |     | NO       | now()          |
