-- Adminer 5.4.1 PostgreSQL 17.7 dump

DROP DATABASE IF EXISTS "remotecheckin";
CREATE DATABASE "remotecheckin";
\connect "remotecheckin";

DROP TABLE IF EXISTS "admin_structure";
CREATE TABLE "public"."admin_structure" (
    "id_user" bigint NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "admin_structure_pkey" PRIMARY KEY ("id_user", "id_structure")
)
WITH (oids = false);


DROP TABLE IF EXISTS "client";
DROP SEQUENCE IF EXISTS client_id_seq;
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


DROP TABLE IF EXISTS "client_reservations";
CREATE TABLE "public"."client_reservations" (
    "id_reservation" bigint NOT NULL,
    "id_client" bigint NOT NULL,
    CONSTRAINT "client_reservations_pkey" PRIMARY KEY ("id_reservation", "id_client")
)
WITH (oids = false);


DROP TABLE IF EXISTS "email_config";
DROP SEQUENCE IF EXISTS email_config_id_seq;
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
    "created_at" timestamp DEFAULT '(now() AT TIME ZONE ''utc'')' NOT NULL,
    "updated_at" timestamp DEFAULT '(now() AT TIME ZONE ''utc'')' NOT NULL,
    CONSTRAINT "email_config_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);

CREATE UNIQUE INDEX ux_email_config_user_id ON public.email_config USING btree (user_id);

CREATE INDEX ix_email_config_is_active ON public.email_config USING btree (is_active);

CREATE INDEX ix_email_config_provider_type ON public.email_config USING btree (provider_type);


DROP TABLE IF EXISTS "reservation";
DROP SEQUENCE IF EXISTS reservation_id_seq;
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
    "number_of_people" integer DEFAULT '1',
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


DROP TABLE IF EXISTS "role";
CREATE TABLE "public"."role" (
    "id" integer NOT NULL,
    "name" character varying,
    CONSTRAINT "role_pkey" PRIMARY KEY ("id")
)
WITH (oids = false);


DROP TABLE IF EXISTS "room";
DROP SEQUENCE IF EXISTS room_id_seq;
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

INSERT INTO "room" ("id", "name", "capacity", "id_structure", "is_active") VALUES
(2,	'Giungla',	4,	1,	true),
(3,	'Savana',	2,	1,	true),
(1,	'SPA',	2,	1,	true);

DROP TABLE IF EXISTS "structure";
DROP SEQUENCE IF EXISTS structure_id_seq;
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


DROP VIEW IF EXISTS "structure_reservations";
CREATE TABLE "structure_reservations" ("structure_id" bigint, "structure_name" character varying, "reservation_id" bigint, "id_reference" character varying(500), "name_reference" text, "start_date" date, "end_date" date, "status" text, "room_id" bigint, "room_name" character varying);


DROP TABLE IF EXISTS "user";
DROP SEQUENCE IF EXISTS user_id_seq;
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


ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_structure_fkey" FOREIGN KEY (id_structure) REFERENCES structure(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_user_fkey" FOREIGN KEY (id_user) REFERENCES "user"(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_client_fkey" FOREIGN KEY (id_client) REFERENCES client(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_reservation_fkey" FOREIGN KEY (id_reservation) REFERENCES reservation(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."email_config" ADD CONSTRAINT "email_config_user_id_fkey" FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE NOT DEFERRABLE;

ALTER TABLE ONLY "public"."reservation" ADD CONSTRAINT "reservation_id_room_fkey" FOREIGN KEY (id_room) REFERENCES room(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."room" ADD CONSTRAINT "room_id_structure_fkey" FOREIGN KEY (id_structure) REFERENCES structure(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."user" ADD CONSTRAINT "user_id_role_fkey" FOREIGN KEY (id_role) REFERENCES role(id) NOT DEFERRABLE;

DROP TABLE IF EXISTS "structure_reservations";
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

-- 2025-03-02 12:41:05.596171+00
