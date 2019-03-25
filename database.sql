CREATE DATABASE notebook_db;

CREATE TABLE review (
  id INTEGER,
  newegg_id CHAR(14) AUTO_INCREMENT,
  data DATETIME,
  title TEXT,
  pros TEXT,
  cons TEXT,
  others TEXT,
  helpful SMALLINT,
  unhelpful SMALLINT,
  PRIMARY KEY (id),
  FOREIGN KEY (newegg_id)  REFERENCES product(newegg_id)
);

CREATE TABLE product (
  newegg_id CHAR(14),
  brand text,
  model text,
  PRIMARY KEY (newegg_id)
);

CREATE TABLE price (
  newegg_id  CHAR(14),
  date DATETIME,
  price DOUBLE,
  PRIMARY KEY (newegg_id, date),
  FOREIGN KEY (newegg_id)  REFERENCES product(newegg_id)
);

CREATE TABLE newegg_id_to_asin (
  newegg_id CHAR(14),
  asin CHAR(10),
  PRIMARY KEY (newegg_id)
);