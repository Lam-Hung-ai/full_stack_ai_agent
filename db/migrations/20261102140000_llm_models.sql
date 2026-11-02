-- migrate:up
-- Chat models configured in the database instead of environment variables
-- (QD-34): system-wide, managed by superusers. A connection is one provider
-- of LangChain's init_chat_model with its client settings and API key; a model
-- is a provider model name with its own settings; an assignment lists, per
-- purpose, the models to try in order (the first is primary, the rest are
-- fallbacks). API keys are encrypted by the application (Fernet); the database
-- never sees them in clear.
CREATE TABLE chat_app.llm_connections (
    id uuid DEFAULT uuidv7() NOT NULL,
    key text NOT NULL,
    name text NOT NULL,
    provider text NOT NULL,
    client_params jsonb DEFAULT '{}'::jsonb NOT NULL,
    api_key_ciphertext text,
    api_key_hint text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_connections_pkey PRIMARY KEY (id),
    CONSTRAINT llm_connections_key_key UNIQUE (key),
    CONSTRAINT llm_connections_key_check CHECK (key ~ '^[a-z][a-z0-9_-]{0,62}$'),
    CONSTRAINT llm_connections_name_check CHECK (btrim(name) <> ''),
    CONSTRAINT llm_connections_provider_check CHECK (provider ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT llm_connections_client_params_check CHECK (jsonb_typeof(client_params) = 'object'),
    CONSTRAINT llm_connections_api_key_check CHECK ((api_key_ciphertext IS NULL) = (api_key_hint IS NULL))
);

COMMENT ON TABLE chat_app.llm_connections IS 'System-wide connections for init_chat_model (QD-34). api_key_ciphertext is Fernet-encrypted by the backend; api_key_hint keeps the last characters for display.';

CREATE TABLE chat_app.llm_models (
    id uuid DEFAULT uuidv7() NOT NULL,
    key text NOT NULL,
    connection_id uuid NOT NULL,
    model text NOT NULL,
    name text NOT NULL,
    params jsonb DEFAULT '{}'::jsonb NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_models_pkey PRIMARY KEY (id),
    CONSTRAINT llm_models_key_key UNIQUE (key),
    CONSTRAINT llm_models_key_check CHECK (key ~ '^[a-z][a-z0-9_-]{0,62}$'),
    CONSTRAINT llm_models_model_check CHECK (btrim(model) <> ''),
    CONSTRAINT llm_models_name_check CHECK (btrim(name) <> ''),
    CONSTRAINT llm_models_params_check CHECK (jsonb_typeof(params) = 'object'),
    CONSTRAINT llm_models_connection_id_fkey FOREIGN KEY (connection_id)
        REFERENCES chat_app.llm_connections(id) ON DELETE RESTRICT
);

CREATE INDEX llm_models_connection_idx ON chat_app.llm_models USING btree (connection_id);

CREATE TABLE chat_app.llm_model_assignments (
    purpose text NOT NULL,
    "position" smallint NOT NULL,
    model_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT llm_model_assignments_pkey PRIMARY KEY (purpose, "position"),
    CONSTRAINT llm_model_assignments_purpose_model_key UNIQUE (purpose, model_id),
    CONSTRAINT llm_model_assignments_purpose_check CHECK (purpose ~ '^[a-z][a-z0-9_]*$'),
    CONSTRAINT llm_model_assignments_position_check CHECK ("position" >= 0),
    CONSTRAINT llm_model_assignments_model_id_fkey FOREIGN KEY (model_id)
        REFERENCES chat_app.llm_models(id) ON DELETE RESTRICT
);

CREATE INDEX llm_model_assignments_model_idx ON chat_app.llm_model_assignments USING btree (model_id);

COMMENT ON TABLE chat_app.llm_model_assignments IS 'Models tried in order for a purpose (chat, title): position 0 is primary, the rest are fallbacks. Replaced as a whole by the backend.';

CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.llm_connections
    FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();
CREATE TRIGGER touch_updated_at BEFORE UPDATE ON chat_app.llm_models
    FOR EACH ROW EXECUTE FUNCTION chat_app.touch_updated_at();

-- migrate:down
DROP TABLE IF EXISTS chat_app.llm_model_assignments;
DROP TABLE IF EXISTS chat_app.llm_models;
DROP TABLE IF EXISTS chat_app.llm_connections;
