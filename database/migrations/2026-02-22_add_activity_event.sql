-- Add activity_event table for admin/superadmin timeline

CREATE SEQUENCE IF NOT EXISTS activity_event_id_seq
    INCREMENT 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

CREATE TABLE IF NOT EXISTS public.activity_event (
    id integer DEFAULT nextval('activity_event_id_seq') NOT NULL,
    event_type character varying(64) NOT NULL,
    entity_type character varying(64) NOT NULL,
    entity_id bigint,
    structure_id bigint,
    actor_user_id bigint,
    actor_role character varying(32),
    description character varying(255) NOT NULL,
    metadata_json text,
    created_at timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    CONSTRAINT activity_event_pkey PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS ix_activity_event_created_at ON public.activity_event USING btree (created_at);
CREATE INDEX IF NOT EXISTS ix_activity_event_structure_id ON public.activity_event USING btree (structure_id);
CREATE INDEX IF NOT EXISTS ix_activity_event_actor_user_id ON public.activity_event USING btree (actor_user_id);
