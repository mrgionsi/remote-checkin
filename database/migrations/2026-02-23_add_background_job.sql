-- Add background_job table for retryable async processing

CREATE SEQUENCE IF NOT EXISTS background_job_id_seq
    INCREMENT 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.background_job (
    id bigint DEFAULT nextval('background_job_id_seq') NOT NULL,
    job_type character varying(64) NOT NULL,
    status character varying(32) NOT NULL,
    payload_json text NOT NULL,
    result_json text,
    error_message text,
    attempts integer DEFAULT 0 NOT NULL,
    max_attempts integer DEFAULT 3 NOT NULL,
    available_at timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    started_at timestamp,
    finished_at timestamp,
    created_by_user_id bigint,
    structure_id bigint,
    worker_id character varying(128),
    created_at timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    updated_at timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    CONSTRAINT background_job_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_background_job_job_type ON public.background_job USING btree (job_type);
CREATE INDEX IF NOT EXISTS ix_background_job_status ON public.background_job USING btree (status);
CREATE INDEX IF NOT EXISTS ix_background_job_available_at ON public.background_job USING btree (available_at);
CREATE INDEX IF NOT EXISTS ix_background_job_status_available_at ON public.background_job USING btree (status, available_at);
CREATE INDEX IF NOT EXISTS ix_background_job_created_by_user_id ON public.background_job USING btree (created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_background_job_structure_id ON public.background_job USING btree (structure_id);
CREATE INDEX IF NOT EXISTS ix_background_job_created_at ON public.background_job USING btree (created_at);
