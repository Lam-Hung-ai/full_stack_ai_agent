-- migrate:up
-- Search a user's chats by title and by the text of questions and answers,
-- ignoring case and Vietnamese accents (use case C09, QD-31). Trigram indexes
-- serve `LIKE '%term%'` on the same expressions the backend queries.
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;

-- unaccent() is only STABLE (its dictionary could change); naming the
-- dictionary makes the result fixed, so it can back an index. Index builds
-- run with a restricted search_path (PostgreSQL 17+) and the committed schema
-- dump drops `public.`, so the function fixes its own path.
CREATE FUNCTION chat_app.search_key(p_text text) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
    SET search_path = public, pg_catalog
    AS $$
    SELECT lower(public.unaccent('public.unaccent'::regdictionary, p_text));
$$;

COMMENT ON FUNCTION chat_app.search_key(text) IS 'Lower-case, accent-free form compared by chat search (C09). Change it only together with the indexes built on it.';

-- The words a message shows: string content of user and assistant messages
-- and the text parts of a question with files. Reasoning, tool calls and
-- activities are left out.
CREATE FUNCTION chat_app.message_text(p_content jsonb) RETURNS text
    LANGUAGE sql IMMUTABLE PARALLEL SAFE
    AS $$
    SELECT coalesce(string_agg(part, ' '), '')
    FROM (
        SELECT m.value ->> 'content' AS part
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        WHERE m.value ->> 'role' IN ('user', 'assistant')
          AND jsonb_typeof(m.value -> 'content') = 'string'
        UNION ALL
        SELECT p.value ->> 'text'
        FROM jsonb_array_elements(
            CASE WHEN jsonb_typeof(p_content) = 'array' THEN p_content ELSE '[]'::jsonb END
        ) AS m
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(m.value -> 'content') = 'array' THEN m.value -> 'content' ELSE '[]'::jsonb END
        ) AS p
        WHERE m.value ->> 'role' = 'user' AND p.value ->> 'type' = 'text'
    ) AS parts;
$$;

COMMENT ON FUNCTION chat_app.message_text(jsonb) IS 'Searchable text of a message AG-UI bundle (C09): user/assistant text only, never reasoning or tool payloads.';

CREATE INDEX messages_search_idx ON chat_app.messages
    USING gin (chat_app.search_key(chat_app.message_text(content)) public.gin_trgm_ops);

CREATE INDEX conversations_title_search_idx ON chat_app.conversations
    USING gin (chat_app.search_key(title) public.gin_trgm_ops);

-- migrate:down
DROP INDEX IF EXISTS chat_app.conversations_title_search_idx;
DROP INDEX IF EXISTS chat_app.messages_search_idx;
DROP FUNCTION IF EXISTS chat_app.message_text(jsonb);
DROP FUNCTION IF EXISTS chat_app.search_key(text);
DROP EXTENSION IF EXISTS unaccent;
DROP EXTENSION IF EXISTS pg_trgm;
