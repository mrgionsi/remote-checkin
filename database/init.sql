-- Adminer 4.8.1 PostgreSQL 17.2 (Debian 17.2-1.pgdg120+1) dump

DROP TABLE IF EXISTS "admin_structure";
CREATE TABLE "public"."admin_structure" (
    "id_user" bigint NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "admin_structure_pkey" PRIMARY KEY ("id_user", "id_structure")
) WITH (oids = false);

INSERT INTO "admin_structure" ("id_user", "id_structure") VALUES
(1,	1);

DROP TABLE IF EXISTS "client";
CREATE TABLE "public"."client" (
    "id" bigint NOT NULL,
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
    CONSTRAINT "client_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_client_id" ON "public"."client" USING btree ("id");


DROP TABLE IF EXISTS "client_reservations";
CREATE TABLE "public"."client_reservations" (
    "id_reservation" bigint NOT NULL,
    "id_client" bigint NOT NULL,
    CONSTRAINT "client_reservations_pkey" PRIMARY KEY ("id_reservation", "id_client")
) WITH (oids = false);


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
    CONSTRAINT "reservation_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_reservation_id" ON "public"."reservation" USING btree ("id");

INSERT INTO "reservation" ("id", "id_reference", "start_date", "end_date", "id_room", "status") VALUES
(1,	'1234',	'2025-02-11',	'2025-02-12',	1,	'Pending'),
(2,	'REF1001',	'2025-01-01',	'2025-01-03',	1,	'Pending'),
(3,	'REF1002',	'2025-01-05',	'2025-01-07',	2,	'Pending'),
(4,	'REF1003',	'2025-01-10',	'2025-01-12',	3,	'Pending'),
(5,	'REF1004',	'2025-01-15',	'2025-01-17',	1,	'Pending'),
(6,	'REF1005',	'2025-01-20',	'2025-01-22',	2,	'Pending'),
(7,	'REF1006',	'2025-01-25',	'2025-01-27',	3,	'Pending'),
(8,	'REF1007',	'2025-01-30',	'2025-02-01',	1,	'Pending'),
(9,	'REF1008',	'2025-02-02',	'2025-02-04',	2,	'Pending'),
(10,	'REF1009',	'2025-02-06',	'2025-02-08',	3,	'Pending'),
(11,	'REF1010',	'2025-02-09',	'2025-02-11',	1,	'Pending'),
(12,	'REF1011',	'2025-02-11',	'2025-02-13',	2,	'Pending');

DROP TABLE IF EXISTS "role";
CREATE TABLE "public"."role" (
    "id" integer NOT NULL,
    "name" character varying,
    CONSTRAINT "role_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

INSERT INTO "role" ("id", "name") VALUES
(1,	'user'),
(2,	'admin'),
(3,	'superuser');

DROP TABLE IF EXISTS "room";
CREATE TABLE "public"."room" (
    "id" bigint NOT NULL,
    "name" character varying NOT NULL,
    "capacity" integer NOT NULL,
    "id_structure" bigint NOT NULL,
    CONSTRAINT "room_pkey" PRIMARY KEY ("id")
) WITH (oids = false);

CREATE INDEX "ix_room_id" ON "public"."room" USING btree ("id");

INSERT INTO "room" ("id", "name", "capacity", "id_structure") VALUES
(1,	'SPA',	2,	1),
(2,	'Giungla',	4,	1),
(3,	'Savana',	2,	1);

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
(1,	'B&B Chapeau',	'Via Torrino 14',	'Casagiove');

DROP VIEW IF EXISTS "structure_reservations";
CREATE TABLE "structure_reservations" ("structure_id" bigint, "structure_name" character varying, "reservation_id" bigint, "id_reference" character varying(500), "start_date" date, "end_date" date, "status" text, "room_id" bigint, "room_name" character varying);


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

INSERT INTO "user" ("id", "name", "surname", "password", "username", "id_role") VALUES
(1,	'Giovanni',	'Pasquariello',	'password',	'gionsi',	3);

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
    r.start_date,
    r.end_date,
    r.status,
    rm.id AS room_id,
    rm.name AS room_name
   FROM ((reservation r
     JOIN room rm ON ((r.id_room = rm.id)))
     JOIN structure s ON ((rm.id_structure = s.id)));

-- 2025-02-11 19:39:46.455727+00