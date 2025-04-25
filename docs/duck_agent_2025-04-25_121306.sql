--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4 (Debian 17.4-1.pgdg120+2)
-- Dumped by pg_dump version 17.4 (Ubuntu 17.4-1.pgdg24.04+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: trigger_set_timestamp(); Type: FUNCTION; Schema: public; Owner: shacea
--

CREATE FUNCTION public.trigger_set_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.trigger_set_timestamp() OWNER TO shacea;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: api_key_usage; Type: TABLE; Schema: public; Owner: shacea
--

CREATE TABLE public.api_key_usage (
    id integer NOT NULL,
    api_key_id integer NOT NULL,
    last_api_call_timestamp timestamp with time zone,
    calls_this_minute integer DEFAULT 0 NOT NULL,
    minute_start_timestamp timestamp with time zone,
    calls_this_day integer DEFAULT 0 NOT NULL,
    day_start_timestamp timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_key_usage OWNER TO shacea;

--
-- Name: TABLE api_key_usage; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON TABLE public.api_key_usage IS 'Tracks the actual usage counts and timestamps for each API key.';


--
-- Name: COLUMN api_key_usage.api_key_id; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.api_key_id IS 'Foreign key referencing the api_keys table.';


--
-- Name: COLUMN api_key_usage.last_api_call_timestamp; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.last_api_call_timestamp IS 'Timestamp of the last successful API call using this key.';


--
-- Name: COLUMN api_key_usage.calls_this_minute; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.calls_this_minute IS 'Counter for calls made within the current minute window.';


--
-- Name: COLUMN api_key_usage.minute_start_timestamp; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.minute_start_timestamp IS 'Timestamp marking the beginning of the current minute window for rate limiting.';


--
-- Name: COLUMN api_key_usage.calls_this_day; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.calls_this_day IS 'Counter for calls made within the current day window.';


--
-- Name: COLUMN api_key_usage.day_start_timestamp; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_key_usage.day_start_timestamp IS 'Timestamp marking the beginning of the current day window for rate limiting.';


--
-- Name: api_key_usage_id_seq; Type: SEQUENCE; Schema: public; Owner: shacea
--

CREATE SEQUENCE public.api_key_usage_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_key_usage_id_seq OWNER TO shacea;

--
-- Name: api_key_usage_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shacea
--

ALTER SEQUENCE public.api_key_usage_id_seq OWNED BY public.api_key_usage.id;


--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: shacea
--

CREATE TABLE public.api_keys (
    id integer NOT NULL,
    api_key text NOT NULL,
    provider text DEFAULT 'google'::text NOT NULL,
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_keys OWNER TO shacea;

--
-- Name: TABLE api_keys; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON TABLE public.api_keys IS 'Stores individual API keys and their metadata.';


--
-- Name: COLUMN api_keys.api_key; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_keys.api_key IS 'The actual API key string. Sensitive data.';


--
-- Name: COLUMN api_keys.provider; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_keys.provider IS 'The provider of the API key (e.g., google, anthropic).';


--
-- Name: COLUMN api_keys.description; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_keys.description IS 'User-friendly description for the key.';


--
-- Name: COLUMN api_keys.is_active; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.api_keys.is_active IS 'Flag to enable/disable the key for use.';


--
-- Name: api_keys_id_seq; Type: SEQUENCE; Schema: public; Owner: shacea
--

CREATE SEQUENCE public.api_keys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.api_keys_id_seq OWNER TO shacea;

--
-- Name: api_keys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shacea
--

ALTER SEQUENCE public.api_keys_id_seq OWNED BY public.api_keys.id;


--
-- Name: application_config; Type: TABLE; Schema: public; Owner: shacea
--

CREATE TABLE public.application_config (
    id integer NOT NULL,
    profile_name text DEFAULT 'default'::text NOT NULL,
    default_system_prompt text,
    allowed_extensions text[],
    excluded_dirs text[],
    default_ignore_list text[],
    gemini_default_model text,
    claude_default_model text,
    gpt_default_model text,
    gemini_available_models text[],
    claude_available_models text[],
    gpt_available_models text[],
    gemini_temperature numeric(3,2) DEFAULT 0.0,
    gemini_enable_thinking boolean DEFAULT true,
    gemini_thinking_budget integer DEFAULT 24576,
    gemini_enable_search boolean DEFAULT true,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.application_config OWNER TO shacea;

--
-- Name: TABLE application_config; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON TABLE public.application_config IS 'Stores application-wide configuration settings, replacing config.yml.';


--
-- Name: COLUMN application_config.profile_name; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.profile_name IS 'Identifier for the configuration profile (e.g., default, development).';


--
-- Name: COLUMN application_config.allowed_extensions; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.allowed_extensions IS 'Array of allowed file extensions.';


--
-- Name: COLUMN application_config.excluded_dirs; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.excluded_dirs IS 'Array of directory/file patterns to exclude.';


--
-- Name: COLUMN application_config.default_ignore_list; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.default_ignore_list IS 'Array of default patterns to ignore.';


--
-- Name: COLUMN application_config.gemini_available_models; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.gemini_available_models IS 'Array of available Gemini model names.';


--
-- Name: COLUMN application_config.claude_available_models; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.claude_available_models IS 'Array of available Claude model names.';


--
-- Name: COLUMN application_config.gpt_available_models; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.gpt_available_models IS 'Array of available GPT model names.';


--
-- Name: COLUMN application_config.gemini_temperature; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.application_config.gemini_temperature IS 'Generation temperature for Gemini models.';


--
-- Name: application_config_id_seq; Type: SEQUENCE; Schema: public; Owner: shacea
--

CREATE SEQUENCE public.application_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.application_config_id_seq OWNER TO shacea;

--
-- Name: application_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shacea
--

ALTER SEQUENCE public.application_config_id_seq OWNED BY public.application_config.id;


--
-- Name: gemini_api_logs; Type: TABLE; Schema: public; Owner: shacea
--

CREATE TABLE public.gemini_api_logs (
    id integer NOT NULL,
    request_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    response_timestamp timestamp with time zone,
    model_name text,
    request_prompt text,
    request_attachments jsonb,
    response_text text,
    response_xml text,
    response_summary text,
    error_message text,
    elapsed_time_ms integer,
    token_count integer,
    api_key_id integer
);


ALTER TABLE public.gemini_api_logs OWNER TO shacea;

--
-- Name: TABLE gemini_api_logs; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON TABLE public.gemini_api_logs IS 'Stores logs of requests and responses to the Gemini API.';


--
-- Name: COLUMN gemini_api_logs.request_timestamp; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.request_timestamp IS 'Timestamp when the request was initiated.';


--
-- Name: COLUMN gemini_api_logs.response_timestamp; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.response_timestamp IS 'Timestamp when the response was received.';


--
-- Name: COLUMN gemini_api_logs.model_name; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.model_name IS 'The specific Gemini model used for the request.';


--
-- Name: COLUMN gemini_api_logs.request_prompt; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.request_prompt IS 'The text prompt sent to the API.';


--
-- Name: COLUMN gemini_api_logs.request_attachments; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.request_attachments IS 'JSONB data containing metadata about attached files/images (e.g., name, type, path).';


--
-- Name: COLUMN gemini_api_logs.response_text; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.response_text IS 'The raw text response from the Gemini API.';


--
-- Name: COLUMN gemini_api_logs.response_xml; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.response_xml IS 'The parsed XML part of the response, if applicable.';


--
-- Name: COLUMN gemini_api_logs.response_summary; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.response_summary IS 'The parsed summary part of the response, if applicable.';


--
-- Name: COLUMN gemini_api_logs.error_message; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.error_message IS 'Error message if the API call failed.';


--
-- Name: COLUMN gemini_api_logs.elapsed_time_ms; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.elapsed_time_ms IS 'Total time taken for the API call in milliseconds.';


--
-- Name: COLUMN gemini_api_logs.token_count; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.token_count IS 'Calculated token count for the request/response.';


--
-- Name: COLUMN gemini_api_logs.api_key_id; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.gemini_api_logs.api_key_id IS 'Foreign key referencing the api_key used for the request.';


--
-- Name: gemini_api_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: shacea
--

CREATE SEQUENCE public.gemini_api_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.gemini_api_logs_id_seq OWNER TO shacea;

--
-- Name: gemini_api_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shacea
--

ALTER SEQUENCE public.gemini_api_logs_id_seq OWNED BY public.gemini_api_logs.id;


--
-- Name: model_rate_limits; Type: TABLE; Schema: public; Owner: shacea
--

CREATE TABLE public.model_rate_limits (
    id integer NOT NULL,
    model_name text NOT NULL,
    provider text DEFAULT 'google'::text NOT NULL,
    rpm_limit integer NOT NULL,
    daily_limit integer NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.model_rate_limits OWNER TO shacea;

--
-- Name: TABLE model_rate_limits; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON TABLE public.model_rate_limits IS 'Stores default rate limit information per model.';


--
-- Name: COLUMN model_rate_limits.model_name; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.model_rate_limits.model_name IS 'Identifier for the language model.';


--
-- Name: COLUMN model_rate_limits.rpm_limit; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.model_rate_limits.rpm_limit IS 'Default Requests Per Minute limit for the model.';


--
-- Name: COLUMN model_rate_limits.daily_limit; Type: COMMENT; Schema: public; Owner: shacea
--

COMMENT ON COLUMN public.model_rate_limits.daily_limit IS 'Default Requests Per Day limit for the model.';


--
-- Name: model_rate_limits_id_seq; Type: SEQUENCE; Schema: public; Owner: shacea
--

CREATE SEQUENCE public.model_rate_limits_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.model_rate_limits_id_seq OWNER TO shacea;

--
-- Name: model_rate_limits_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: shacea
--

ALTER SEQUENCE public.model_rate_limits_id_seq OWNED BY public.model_rate_limits.id;


--
-- Name: api_key_usage id; Type: DEFAULT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_key_usage ALTER COLUMN id SET DEFAULT nextval('public.api_key_usage_id_seq'::regclass);


--
-- Name: api_keys id; Type: DEFAULT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_keys ALTER COLUMN id SET DEFAULT nextval('public.api_keys_id_seq'::regclass);


--
-- Name: application_config id; Type: DEFAULT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.application_config ALTER COLUMN id SET DEFAULT nextval('public.application_config_id_seq'::regclass);


--
-- Name: gemini_api_logs id; Type: DEFAULT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.gemini_api_logs ALTER COLUMN id SET DEFAULT nextval('public.gemini_api_logs_id_seq'::regclass);


--
-- Name: model_rate_limits id; Type: DEFAULT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.model_rate_limits ALTER COLUMN id SET DEFAULT nextval('public.model_rate_limits_id_seq'::regclass);


--
-- Data for Name: api_key_usage; Type: TABLE DATA; Schema: public; Owner: shacea
--

COPY public.api_key_usage (id, api_key_id, last_api_call_timestamp, calls_this_minute, minute_start_timestamp, calls_this_day, day_start_timestamp, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: api_keys; Type: TABLE DATA; Schema: public; Owner: shacea
--

COPY public.api_keys (id, api_key, provider, description, is_active, created_at, updated_at) FROM stdin;
1	AIzaSyC5uUtef7uQnLiP2ioBM7OqIF9EaxAnGQE	google	\N	t	2025-04-25 03:12:15.567062+00	2025-04-25 03:12:15.567062+00
2	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	anthropic	\N	t	2025-04-25 03:12:15.580406+00	2025-04-25 03:12:15.580406+00
\.


--
-- Data for Name: application_config; Type: TABLE DATA; Schema: public; Owner: shacea
--

COPY public.application_config (id, profile_name, default_system_prompt, allowed_extensions, excluded_dirs, default_ignore_list, gemini_default_model, claude_default_model, gpt_default_model, gemini_available_models, claude_available_models, gpt_available_models, gemini_temperature, gemini_enable_thinking, gemini_thinking_budget, gemini_enable_search, created_at, updated_at) FROM stdin;
1	default	resources/prompts/system/xml_prompt_guide_python_en.md	{}	{.gitignore,__pycache__/,*.log,.venv/,dist/,.vscode/,node_modules/,.DS_Store,build/,.idea/,.git/}	{*.egg-info/,*.pyc,.cursorrules,.git/,.gitignore,.idea/,.vscode/,.windsurfrules,__pycache__/,build/,dist/}	gemini-2.5-pro-preview-03-25	claude-3-7-sonnet-20250219	gpt-4o	{gemini-2.5-pro-preview-03-25,gemini-2.5-flash-preview-04-17}	{claude-3-7-sonnet-20250219}	{gpt-4o,gpt-4-turbo,gpt-3.5-turbo}	0.00	f	0	f	2025-04-25 03:12:15.553225+00	2025-04-25 03:12:15.553225+00
\.


--
-- Data for Name: gemini_api_logs; Type: TABLE DATA; Schema: public; Owner: shacea
--

COPY public.gemini_api_logs (id, request_timestamp, response_timestamp, model_name, request_prompt, request_attachments, response_text, response_xml, response_summary, error_message, elapsed_time_ms, token_count, api_key_id) FROM stdin;
\.


--
-- Data for Name: model_rate_limits; Type: TABLE DATA; Schema: public; Owner: shacea
--

COPY public.model_rate_limits (id, model_name, provider, rpm_limit, daily_limit, notes, created_at, updated_at) FROM stdin;
\.


--
-- Name: api_key_usage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shacea
--

SELECT pg_catalog.setval('public.api_key_usage_id_seq', 1, false);


--
-- Name: api_keys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shacea
--

SELECT pg_catalog.setval('public.api_keys_id_seq', 2, true);


--
-- Name: application_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shacea
--

SELECT pg_catalog.setval('public.application_config_id_seq', 1, true);


--
-- Name: gemini_api_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shacea
--

SELECT pg_catalog.setval('public.gemini_api_logs_id_seq', 1, false);


--
-- Name: model_rate_limits_id_seq; Type: SEQUENCE SET; Schema: public; Owner: shacea
--

SELECT pg_catalog.setval('public.model_rate_limits_id_seq', 1, false);


--
-- Name: api_key_usage api_key_usage_api_key_id_key; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_key_usage
    ADD CONSTRAINT api_key_usage_api_key_id_key UNIQUE (api_key_id);


--
-- Name: api_key_usage api_key_usage_pkey; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_key_usage
    ADD CONSTRAINT api_key_usage_pkey PRIMARY KEY (id);


--
-- Name: api_keys api_keys_api_key_key; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_api_key_key UNIQUE (api_key);


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: application_config application_config_pkey; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.application_config
    ADD CONSTRAINT application_config_pkey PRIMARY KEY (id);


--
-- Name: application_config application_config_profile_name_key; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.application_config
    ADD CONSTRAINT application_config_profile_name_key UNIQUE (profile_name);


--
-- Name: gemini_api_logs gemini_api_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.gemini_api_logs
    ADD CONSTRAINT gemini_api_logs_pkey PRIMARY KEY (id);


--
-- Name: model_rate_limits model_rate_limits_model_name_key; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.model_rate_limits
    ADD CONSTRAINT model_rate_limits_model_name_key UNIQUE (model_name);


--
-- Name: model_rate_limits model_rate_limits_pkey; Type: CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.model_rate_limits
    ADD CONSTRAINT model_rate_limits_pkey PRIMARY KEY (id);


--
-- Name: idx_api_key_usage_api_key_id; Type: INDEX; Schema: public; Owner: shacea
--

CREATE INDEX idx_api_key_usage_api_key_id ON public.api_key_usage USING btree (api_key_id);


--
-- Name: idx_gemini_api_logs_api_key_id; Type: INDEX; Schema: public; Owner: shacea
--

CREATE INDEX idx_gemini_api_logs_api_key_id ON public.gemini_api_logs USING btree (api_key_id);


--
-- Name: idx_gemini_api_logs_request_timestamp; Type: INDEX; Schema: public; Owner: shacea
--

CREATE INDEX idx_gemini_api_logs_request_timestamp ON public.gemini_api_logs USING btree (request_timestamp);


--
-- Name: api_key_usage set_api_key_usage_timestamp; Type: TRIGGER; Schema: public; Owner: shacea
--

CREATE TRIGGER set_api_key_usage_timestamp BEFORE UPDATE ON public.api_key_usage FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- Name: api_keys set_api_keys_timestamp; Type: TRIGGER; Schema: public; Owner: shacea
--

CREATE TRIGGER set_api_keys_timestamp BEFORE UPDATE ON public.api_keys FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- Name: application_config set_application_config_timestamp; Type: TRIGGER; Schema: public; Owner: shacea
--

CREATE TRIGGER set_application_config_timestamp BEFORE UPDATE ON public.application_config FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- Name: model_rate_limits set_model_rate_limits_timestamp; Type: TRIGGER; Schema: public; Owner: shacea
--

CREATE TRIGGER set_model_rate_limits_timestamp BEFORE UPDATE ON public.model_rate_limits FOR EACH ROW EXECUTE FUNCTION public.trigger_set_timestamp();


--
-- Name: api_key_usage api_key_usage_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.api_key_usage
    ADD CONSTRAINT api_key_usage_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.api_keys(id) ON DELETE CASCADE;


--
-- Name: gemini_api_logs gemini_api_logs_api_key_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: shacea
--

ALTER TABLE ONLY public.gemini_api_logs
    ADD CONSTRAINT gemini_api_logs_api_key_id_fkey FOREIGN KEY (api_key_id) REFERENCES public.api_keys(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

