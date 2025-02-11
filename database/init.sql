CREATE SEQUENCE IF NOT EXISTS room_id_seq;
CREATE SEQUENCE IF NOT EXISTS admin_structure_id_user_seq;
CREATE SEQUENCE IF NOT EXISTS role_id_seq;
CREATE SEQUENCE IF NOT EXISTS client_reservations_id_reservation_seq;
CREATE SEQUENCE IF NOT EXISTS client_id_seq;
CREATE SEQUENCE IF NOT EXISTS reservation_id_seq;
CREATE SEQUENCE IF NOT EXISTS user_id_seq;
CREATE SEQUENCE IF NOT EXISTS structure_id_seq;

CREATE TABLE IF NOT EXISTS Room (
  id bigint NOT NULL PRIMARY KEY DEFAULT nextval('room_id_seq'),
  name text,
  capacity integer,
  id_structure bigint
);

CREATE TABLE IF NOT EXISTS admin_structure (
  id_user bigint NOT NULL,
  id_structure bigint NOT NULL,
  PRIMARY KEY (id_user, id_structure)
);

CREATE TABLE IF NOT EXISTS Role (
  id integer NOT NULL PRIMARY KEY DEFAULT nextval('role_id_seq'),
  name bigint
);

CREATE TABLE IF NOT EXISTS client_reservations (
  id_reservation bigint NOT NULL,
  id_client bigint NOT NULL,
  PRIMARY KEY (id_reservation, id_client)
);

CREATE TABLE IF NOT EXISTS Client (
  id bigint NOT NULL PRIMARY KEY DEFAULT nextval('client_id_seq'),
  name text,
  surname text,
  birthday date,
  street text,
  number_city text,
  city text,
  province text,
  cap text,
  telephone text,
  document_number text,
  cf text
);

COMMENT ON TABLE Client IS 'Images will be stored in a specific path, with id as folder name';

CREATE TABLE IF NOT EXISTS Reservation (
  id bigint NOT NULL PRIMARY KEY DEFAULT nextval('reservation_id_seq'),
  id_reference varchar(500) NOT NULL,
  start_date date,
  end_date date,
  id_room bigint
);

COMMENT ON COLUMN Reservation.id_reference IS 'booking or airbnb';

CREATE TABLE IF NOT EXISTS "User" (
  id bigint NOT NULL PRIMARY KEY DEFAULT nextval('user_id_seq'),
  name text,
  surname text,
  password text,
  username text,
  id_role integer NOT NULL
);

CREATE TABLE IF NOT EXISTS Structure (
  id bigint NOT NULL PRIMARY KEY DEFAULT nextval('structure_id_seq'),
  name bigint,
  street bigint,
  city bigint
);

ALTER TABLE admin_structure ADD CONSTRAINT admin_structure_id_structure_fk FOREIGN KEY (id_structure) REFERENCES Structure (id);
ALTER TABLE admin_structure ADD CONSTRAINT admin_structure_id_user_fk FOREIGN KEY (id_user) REFERENCES "User" (id);
ALTER TABLE client_reservations ADD CONSTRAINT client_reservations_id_client_fk FOREIGN KEY (id_client) REFERENCES Client (id);
ALTER TABLE Reservation ADD CONSTRAINT Reservation_id_fk FOREIGN KEY (id) REFERENCES client_reservations (id_reservation);
ALTER TABLE Reservation ADD CONSTRAINT Reservation_id_room_fk FOREIGN KEY (id_room) REFERENCES Room (id);
ALTER TABLE Room ADD CONSTRAINT Room_id_structure_fk FOREIGN KEY (id_structure) REFERENCES Structure (id);
ALTER TABLE "User" ADD CONSTRAINT User_id_role_fk FOREIGN KEY (id_role) REFERENCES Role (id);