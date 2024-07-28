CREATE TABLE votos_mesa (
  id integer NOT NULL,
  mesa_id integer,
  candidatura_id integer,
  votos integer
);
CREATE TABLE mesa (
  id integer NOT NULL,
  comuna_id integer,
  nombre text,
  nombre_local text,
  nombre_circunscripcion_electoral text
);
CREATE TABLE eleccion (
  id integer NOT NULL,
  tipo_eleccion_id integer,
  fecha date,
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
  num_en_papeleta integer,
  independiente boolean
);
CREATE TABLE candidato (
  id integer NOT NULL,
  nombre__emb_openai_small USER-DEFINED,
  nombre text
);
CREATE TABLE geography_columns (
  coord_dimension integer,
  srid integer,
  type text,
  f_table_catalog name,
  f_geography_column name,
  f_table_schema name,
  f_table_name name
);
CREATE TABLE geometry_columns (
  coord_dimension integer,
  srid integer,
  type character varying(30),
  f_table_catalog character varying(256),
  f_geometry_column name,
  f_table_schema name,
  f_table_name name
);
CREATE TABLE spatial_ref_sys (
  srid integer NOT NULL,
  auth_srid integer,
  auth_name character varying(256),
  srtext character varying(2048),
  proj4text character varying(2048)
);
CREATE TABLE comuna (
  id integer NOT NULL,
  codigo integer,
  region_id integer,
  geom USER-DEFINED,
  nombre text
);