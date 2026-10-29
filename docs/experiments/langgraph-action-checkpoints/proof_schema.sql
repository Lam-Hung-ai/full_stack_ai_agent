-- Experiment bootstrap only. Use the approved phase-4 application schema.
-- psql resolves this include relative to this file.
\ir ../../database_decisions/phase-4-schema.sql
BEGIN;
-- Evidence-only instrumentation, not proposed application tables.
CREATE SCHEMA checkpoint_probe;
CREATE SCHEMA probe_evidence;
CREATE TABLE probe_evidence.effects (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message_id uuid NOT NULL,
    name text NOT NULL
);
COMMIT;
