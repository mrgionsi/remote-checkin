-- Adminer 4.8.1 PostgreSQL 17.3 (Debian 17.3-1.pgdg120+1) dump

DROP TABLE IF EXISTS "admin_structure";
CREATE TABLE "public"."admin_structure" (
    "id_user" bigint NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "admin_structure_pkey" PRIMARY KEY ("id_user", "id_structure")
) WITH (oids = false);


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
    "city" character varying,
    "province" character varying,
    "cap" character varying,
    "telephone" character varying,
    "document_number" character varying,
    "cf" character varying,
    "document_type" text,
    CONSTRAINT "client_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "client_cf" ON "public"."client" USING btree ("cf");

CREATE INDEX "ix_client_id" ON "public"."client" USING btree ("id");

INSERT INTO "client" ("id", "name", "surname", "birthday", "street", "number_city", "city", "province", "cap", "telephone", "document_number", "cf", "document_type") VALUES
(8,	'Giovanni',	'Pasquariello',	'2025-02-04',	'via corsica 17',	'17',	'Recale',	'CE',	'81020',	'3454526037',	'CAA4F3432',	'PSQGNN96M08B963J',	NULL),
(9,	'Giovanni',	'Pasquariello',	'2025-02-02',	'via corsica 17',	'17',	'Recale',	'CE',	'81020',	'3454526037',	'CAA4F3432',	'PSQGNN96M08B963A',	NULL);

DROP TABLE IF EXISTS "client_reservations";
CREATE TABLE "public"."client_reservations" (
    "id_reservation" bigint NOT NULL,
    "id_client" bigint NOT NULL,
    CONSTRAINT "client_reservations_pkey" PRIMARY KEY ("id_reservation", "id_client")
) WITH (oids = false);

INSERT INTO "client_reservations" ("id_reservation", "id_client") VALUES
(1,	8),
(1,	9);

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
    CONSTRAINT "reservation_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "reservation_id_reference" ON "public"."reservation" USING btree ("id_reference");

INSERT INTO "reservation" ("id", "id_reference", "start_date", "end_date", "id_room", "status", "name_reference") VALUES
(1,	'1234',	'2025-02-14',	'2025-02-15',	2,	'Pending',	'Giovanni Pasquariello');

DROP TABLE IF EXISTS "role";
CREATE TABLE "public"."role" (
    "id" integer NOT NULL,
    "name" character varying,
    CONSTRAINT "role_pkey" PRIMARY KEY ("id")
) WITH (oids = false);


DROP TABLE IF EXISTS "room";
DROP SEQUENCE IF EXISTS room_id_seq;
CREATE SEQUENCE room_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 9223372036854775807 CACHE 1;

CREATE TABLE "public"."room" (
    "id" bigint DEFAULT nextval('room_id_seq') NOT NULL,
    "name" character varying NOT NULL,
    "capacity" integer NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "room_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_room_id" ON "public"."room" USING btree ("id");

INSERT INTO "room" ("id", "name", "capacity", "id_structure") VALUES
(2,	'Giungla',	4,	1),
(3,	'Savana',	2,	1),
(1,	'SPA',	2,	1);

DROP TABLE IF EXISTS "structure";
CREATE TABLE "public"."structure" (
    "id" bigint NOT NULL,
    "name" character varying,
    "street" character varying,
    "city" character varying,
    CONSTRAINT "structure_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_structure_id" ON "public"."structure" USING btree ("id");

INSERT INTO "structure" ("id", "name", "street", "city") VALUES
(2,	'B&B Chapeau',	'Via Torrino 14',	'Casagiove'),
(1,	'B&B Chapeau',	'Via Torrino 14',	'Casagiove');

DROP VIEW IF EXISTS "structure_reservations";
CREATE TABLE "structure_reservations" ("structure_id" bigint, "structure_name" character varying, "reservation_id" bigint, "id_reference" character varying(500), "name_reference" text, "start_date" date, "end_date" date, "status" text, "room_id" bigint, "room_name" character varying);


DROP TABLE IF EXISTS "user";
CREATE TABLE "public"."user" (
    "id" bigint NOT NULL,
    "name" character varying,
    "surname" character varying,
    "password" character varying,
    "username" character varying,
    "id_role" integer,
    CONSTRAINT "user_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_user_id" ON "public"."user" USING btree ("id");


ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_structure_fkey" FOREIGN KEY (id_structure) REFERENCES structure(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."admin_structure" ADD CONSTRAINT "admin_structure_id_user_fkey" FOREIGN KEY (id_user) REFERENCES "user"(id) NOT DEFERRABLE;

ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_client_fkey" FOREIGN KEY (id_client) REFERENCES client(id) NOT DEFERRABLE;
ALTER TABLE ONLY "public"."client_reservations" ADD CONSTRAINT "client_reservations_id_reservation_fkey" FOREIGN KEY (id_reservation) REFERENCES reservation(id) NOT DEFERRABLE;

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