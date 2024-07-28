CREATE TABLE votos_mesa (
  id integer NOT NULL,
  mesa_id integer,
  candidatura_id integer,
  votos integer
);
CREATE TABLE mesa (
  id integer NOT NULL,
  comuna_id integer,
);
CREATE TABLE eleccion (
  id integer NOT NULL,
  tipo_eleccion_id integer,
  nombre text
);
CREATE TABLE pacto (
  id integer NOT NULL,
  nombre text,
  codigo text
);
CREATE TABLE partido (
  id integer NOT NULL,
  nombre text
);
CREATE TABLE region (
  id integer NOT NULL,
  codigo integer,
  nombre text
);
CREATE TABLE subpacto (
  id integer NOT NULL,
  nombre text
);
CREATE TABLE tipo_eleccion (
  id integer NOT NULL,
  nombre text
);
CREATE TABLE candidatura (
  id integer NOT NULL,
  candidato_id integer,
  eleccion_id integer,
  partido_id integer,
  pacto_id integer,
  subpacto_id integer,
  independiente boolean
);
CREATE TABLE candidato (
  id integer NOT NULL,
  nombre text
);
CREATE TABLE comuna (
  id integer NOT NULL,
  codigo integer,
  region_id integer,
  nombre text
);