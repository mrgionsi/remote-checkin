-- Adminer 5.4.1 PostgreSQL 17.7 dump
-- NOTE:
-- - \connect is a psql meta-command and fails in Adminer.
-- - PostgreSQL has no plain-SQL `CREATE DATABASE IF NOT EXISTS`.
-- - Bootstrap in Adminer:
--   1) Connect to database `postgres`
--   2) Run once: CREATE DATABASE "remotecheckin";
--   3) Switch connection to database `remotecheckin`
--   4) Run the rest of this script

-- psql only:
-- \connect "remotecheckin"

DROP VIEW IF EXISTS "structure_reservations" CASCADE;

DROP TABLE IF EXISTS "admin_structure" CASCADE;
CREATE TABLE "public"."admin_structure" (
    "id_user" bigint NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "admin_structure_pkey" PRIMARY KEY ("id_user", "id_structure")
)
WITH (oids = false);


DROP TABLE IF EXISTS "client" CASCADE;
DROP SEQUENCE IF EXISTS client_id_seq CASCADE;
CREATE SEQUENCE client_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."client" (
    "id" bigint DEFAULT nextval('client_id_seq') NOT NULL,
    "name" character varying,
    "surname" character varying,
    "birthday" date,
    "street" character varying,
    "number_city" character varying,
    "cap" character varying,
    "telephone" character varying,
    "document_number" character varying,
    "cf" character varying,
    "document_type" text,
    "sesso" character varying(1),
    "nazionalita" character varying(9),
    "email" character varying(255),
    "comune_nascita" character varying(100),
    "provincia_nascita" character varying(2),
    "stato_nascita" character varying(9),
    "cittadinanza" character varying(9),
    "luogo_emissione" character varying(100),
    "data_emissione" date,
    "data_scadenza" date,
    "autorita_rilascio" character varying(100),
    "comune_residenza" character varying(100),
    "provincia_residenza" character varying(2),
    "stato_residenza" character varying(9),
    CONSTRAINT "client_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "client_sesso_check" CHECK ((sesso)::text = ANY ((ARRAY['1'::character varying, '2'::character varying])::text[]))
)
WITH (oids = false);

COMMENT ON TABLE "public"."client" IS 'Client table - removed duplicated city and province fields, kept only in Portale Alloggi section';

COMMENT ON COLUMN "public"."client"."sesso" IS 'Gender: 1=Male, 2=Female (Portale Alloggi format)';

COMMENT ON COLUMN "public"."client"."nazionalita" IS 'Nationality as Alloggiati Web country code (9 characters, e.g., 100000100 for ITALIA)';

COMMENT ON COLUMN "public"."client"."email" IS 'Email address for guest communication';

COMMENT ON COLUMN "public"."client"."comune_nascita" IS 'Birth municipality name or code';

COMMENT ON COLUMN "public"."client"."provincia_nascita" IS 'Birth province acronym (e.g., NA, MI) for Portale Alloggiati Web';

COMMENT ON COLUMN "public"."client"."stato_nascita" IS 'Birth country as Alloggiati Web country code (9 characters)';

COMMENT ON COLUMN "public"."client"."cittadinanza" IS 'Citizenship as Alloggiati Web country code (9 characters)';

COMMENT ON COLUMN "public"."client"."luogo_emissione" IS 'Document issue place name';

COMMENT ON COLUMN "public"."client"."data_emissione" IS 'Document issue date';

COMMENT ON COLUMN "public"."client"."data_scadenza" IS 'Document expiration date';

COMMENT ON COLUMN "public"."client"."autorita_rilascio" IS 'Document issuing authority name';

COMMENT ON COLUMN "public"."client"."comune_residenza" IS 'Residence municipality name';

COMMENT ON COLUMN "public"."client"."provincia_residenza" IS 'Residence province acronym (e.g., NA, MI) for Portale Alloggiati Web';

COMMENT ON COLUMN "public"."client"."stato_residenza" IS 'Residence country as Alloggiati Web country code (9 characters)';

CREATE INDEX ix_client_id ON public.client USING btree (id);

CREATE INDEX client_cf ON public.client USING btree (cf);

CREATE INDEX idx_client_email ON public.client USING btree (email);

CREATE INDEX idx_client_data_scadenza ON public.client USING btree (data_scadenza);

CREATE INDEX idx_client_nazionalita ON public.client USING btree (nazionalita);

CREATE INDEX idx_client_provincia_nascita ON public.client USING btree (provincia_nascita);

CREATE INDEX idx_client_provincia_residenza ON public.client USING btree (provincia_residenza);


DROP TABLE IF EXISTS "client_reservations" CASCADE;
CREATE TABLE "public"."client_reservations" (
    "id_reservation" bigint NOT NULL,
    "id_client" bigint NOT NULL,
    CONSTRAINT "client_reservations_pkey" PRIMARY KEY ("id_reservation", "id_client")
)
WITH (oids = false);


DROP TABLE IF EXISTS "email_config" CASCADE;
DROP SEQUENCE IF EXISTS email_config_id_seq CASCADE;
CREATE SEQUENCE email_config_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."email_config" (
    "id" integer DEFAULT nextval('email_config_id_seq') NOT NULL,
    "user_id" bigint NOT NULL,
    "mail_server" character varying NOT NULL,
    "mail_port" integer NOT NULL,
    "mail_use_tls" boolean DEFAULT true NOT NULL,
    "mail_use_ssl" boolean DEFAULT false NOT NULL,
    "mail_username" character varying NOT NULL,
    "mail_password" character varying NOT NULL,
    "mail_default_sender_name" character varying,
    "mail_default_sender_email" character varying NOT NULL,
    "provider_type" character varying DEFAULT 'smtp' NOT NULL,
    "provider_config" text,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    "updated_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    CONSTRAINT "email_config_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX ux_email_config_user_id ON public.email_config USING btree (user_id);

CREATE INDEX ix_email_config_is_active ON public.email_config USING btree (is_active);

CREATE INDEX ix_email_config_provider_type ON public.email_config USING btree (provider_type);


DROP TABLE IF EXISTS "activity_event" CASCADE;
DROP SEQUENCE IF EXISTS activity_event_id_seq CASCADE;
CREATE SEQUENCE activity_event_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."activity_event" (
    "id" bigint DEFAULT nextval('activity_event_id_seq') NOT NULL,
    "event_type" character varying(64) NOT NULL,
    "entity_type" character varying(64) NOT NULL,
    "entity_id" bigint,
    "structure_id" bigint,
    "actor_user_id" bigint,
    "actor_role" character varying(32),
    "description" character varying(255) NOT NULL,
    "metadata_json" text,
    "created_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    CONSTRAINT "activity_event_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX ix_activity_event_created_at ON public.activity_event USING btree (created_at);
CREATE INDEX ix_activity_event_structure_id ON public.activity_event USING btree (structure_id);
CREATE INDEX ix_activity_event_actor_user_id ON public.activity_event USING btree (actor_user_id);
CREATE INDEX ix_activity_event_event_type ON public.activity_event USING btree (event_type);

DROP TABLE IF EXISTS "background_job" CASCADE;
DROP SEQUENCE IF EXISTS background_job_id_seq CASCADE;
CREATE SEQUENCE background_job_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."background_job" (
    "id" bigint DEFAULT nextval('background_job_id_seq') NOT NULL,
    "job_type" character varying(64) NOT NULL,
    "status" character varying(32) NOT NULL,
    "payload_json" text NOT NULL,
    "result_json" text,
    "error_message" text,
    "attempts" integer DEFAULT 0 NOT NULL,
    "max_attempts" integer DEFAULT 3 NOT NULL,
    "available_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    "started_at" timestamp,
    "finished_at" timestamp,
    "created_by_user_id" bigint,
    "structure_id" bigint,
    "worker_id" character varying(128),
    "created_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    "updated_at" timestamp DEFAULT (now() AT TIME ZONE 'utc') NOT NULL,
    CONSTRAINT "background_job_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX ix_background_job_job_type ON public.background_job USING btree (job_type);
CREATE INDEX ix_background_job_status ON public.background_job USING btree (status);
CREATE INDEX ix_background_job_available_at ON public.background_job USING btree (available_at);
CREATE INDEX ix_background_job_status_available_at ON public.background_job USING btree (status, available_at);
CREATE INDEX ix_background_job_created_by_user_id ON public.background_job USING btree (created_by_user_id);
CREATE INDEX ix_background_job_structure_id ON public.background_job USING btree (structure_id);
CREATE INDEX ix_background_job_created_at ON public.background_job USING btree (created_at);


DROP TABLE IF EXISTS "reservation" CASCADE;
DROP SEQUENCE IF EXISTS reservation_id_seq CASCADE;
CREATE SEQUENCE reservation_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."reservation" (
    "id" bigint DEFAULT nextval('reservation_id_seq') NOT NULL,
    "id_reference" character varying(500) NOT NULL,
    "start_date" date,
    "end_date" date,
    "id_room" bigint,
    "status" text DEFAULT 'Pending',
    "name_reference" text DEFAULT 'Not available',
    "email" text,
    "telephone" text,
    "number_of_people" integer DEFAULT 1,
    "portale_alloggi_sent" boolean DEFAULT false NOT NULL,
    "portale_alloggi_sent_at" timestamp,
    "portale_alloggi_response" text,
    CONSTRAINT "reservation_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

COMMENT ON COLUMN "public"."reservation"."portale_alloggi_sent" IS 'Tracks if data has been successfully sent to Portale Alloggi';

COMMENT ON COLUMN "public"."reservation"."portale_alloggi_sent_at" IS 'Timestamp when data was sent to Portale Alloggi';

COMMENT ON COLUMN "public"."reservation"."portale_alloggi_response" IS 'Response received from Portale Alloggi after submission';

CREATE INDEX reservation_id_reference ON public.reservation USING btree (id_reference);

CREATE INDEX idx_reservation_portale_sent ON public.reservation USING btree (portale_alloggi_sent);


DROP TABLE IF EXISTS "role" CASCADE;
CREATE TABLE "public"."role" (
    "id" integer NOT NULL,
    "name" character varying,
    CONSTRAINT "role_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

INSERT INTO "role" ("id", "name") VALUES
(2, 'superadmin');


DROP TABLE IF EXISTS "room" CASCADE;
DROP SEQUENCE IF EXISTS room_id_seq CASCADE;
CREATE SEQUENCE room_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."room" (
    "id" bigint DEFAULT nextval('room_id_seq') NOT NULL,
    "name" character varying NOT NULL,
    "capacity" integer NOT NULL,
    "id_structure" bigint NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    CONSTRAINT "room_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE INDEX ix_room_id ON public.room USING btree (id);

DROP TABLE IF EXISTS "structure" CASCADE;
DROP SEQUENCE IF EXISTS structure_id_seq CASCADE;
CREATE SEQUENCE structure_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."structure" (
    "id" bigint DEFAULT nextval('structure_id_seq') NOT NULL,
    "name" character varying,
    "street" character varying,
    "city" character varying,
    "cin" character varying,
    "is_active" boolean DEFAULT true NOT NULL,
    CONSTRAINT "structure_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

COMMENT ON COLUMN "public"."structure"."cin" IS 'CIN (Codice Identificativo Nazionale) of the structure';

CREATE INDEX ix_structure_id ON public.structure USING btree (id);

CREATE INDEX idx_structure_cin ON public.structure USING btree (cin);

INSERT INTO "structure" ("id", "name", "street", "city", "cin", "is_active") VALUES
(1, 'Default Structure', NULL, NULL, NULL, true);

SELECT setval('structure_id_seq', 1, true);

INSERT INTO "room" ("id", "name", "capacity", "id_structure", "is_active") VALUES
(2, 'Room 2', 4, 1, true),
(3, 'Room 3', 2, 1, true),
(1, 'Room 1', 2, 1, true);

SELECT setval('room_id_seq', 3, true);


DROP TABLE IF EXISTS "structure_reservations" CASCADE;


DROP TABLE IF EXISTS "user" CASCADE;
DROP SEQUENCE IF EXISTS user_id_seq CASCADE;
CREATE SEQUENCE user_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."user" (
    "id" bigint DEFAULT nextval('user_id_seq') NOT NULL,
    "name" character varying,
    "surname" character varying,
    "password" character varying,
    "username" character varying,
    "id_role" integer,
    "email" character varying,
    "telephone" character varying,
    "portale_username" character varying,
    "portale_password" character varying,
    "portale_wskey" character varying,
    CONSTRAINT "user_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

COMMENT ON COLUMN "public"."user"."email" IS 'User email address';

COMMENT ON COLUMN "public"."user"."telephone" IS 'User telephone number';

COMMENT ON COLUMN "public"."user"."portale_username" IS 'Username for Portale Alloggi authentication';

COMMENT ON COLUMN "public"."user"."portale_password" IS 'Encrypted password for Portale Alloggi authentication';

COMMENT ON COLUMN "public"."user"."portale_wskey" IS 'Web Service Key for Portale Alloggi API access';

CREATE INDEX ix_user_id ON public."user" USING btree (id);

CREATE INDEX idx_user_email ON public."user" USING btree (email);

CREATE INDEX ix_user_portale_username ON public."user" USING btree (portale_username);

INSERT INTO "user" ("id", "name", "surname", "password", "username", "id_role", "email", "telephone", "portale_username", "portale_password", "portale_wskey") VALUES
(1, 'Admin', 'User', 'scrypt:32768:8:1$JSTCdcjvXvmsobaT$ddce21e49fed8dcbef901023c1c5c22ebb7f3a6fc5606d4000986174ccf313d0069dc609ca39e745c1bb30f87107401755ee10e4ee7b4768899f3603bcb23540', 'superadmin', 2, 'superadmin@example.com', NULL, NULL, NULL, NULL);

SELECT setval('user_id_seq', 2, true);


ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_structure_fkey" FOREIGN KEY (id_structure) REFERENCES structure(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_user_fkey" FOREIGN KEY (id_user) REFERENCES "user"(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_client_fkey" FOREIGN KEY (id_client) REFERENCES client(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_reservation_fkey" FOREIGN KEY (id_reservation) REFERENCES reservation(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."email_config" ADD CONSTRAINT "email_config_user_id_fkey" FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE NOT DEFERRABLE;

ALTER TABLE ONLY "public"."reservation" ADD CONSTRAINT "reservation_id_room_fkey" FOREIGN KEY (id_room) REFERENCES room(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."room" ADD CONSTRAINT "room_id_structure_fkey" FOREIGN KEY (id_structure) REFERENCES structure(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user" ADD CONSTRAINT "user_id_role_fkey" FOREIGN KEY (id_role) REFERENCES role(id) NOT DEFERRABLE;

DROP TABLE IF EXISTS "structure_reservations" CASCADE;
DROP VIEW IF EXISTS "structure_reservations" CASCADE;
CREATE VIEW "structure_reservations" AS SELECT s.id AS structure_id,
    s.name AS structure_name,
    r.id AS reservation_id,
    r.id_reference,
    r.name_reference,
    r.start_date,
    r.end_date,
    r.status,
    rm.id AS room_id,
    rm.name AS room_name
   FROM ((reservation r
     JOIN room rm ON ((r.id_room = rm.id)))
     JOIN structure s ON ((rm.id_structure = s.id)));
