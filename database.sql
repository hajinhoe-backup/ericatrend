CREATE DATABASE notebook_db;

USE notebook_db;

CREATE TABLE product (
  newegg_id VARCHAR(20),
  brand text,
  model text,
  PRIMARY KEY (newegg_id)
);

CREATE TABLE review (
  id INTEGER auto_increment,
  newegg_id VARCHAR(20),
  star TINYINT,
  title TEXT,
  date DATETIME,
  pros TEXT,
  cons TEXT,
  others TEXT,
  helpful SMALLINT,
  unhelpful SMALLINT,
  PRIMARY KEY (id),
  FOREIGN KEY (newegg_id) REFERENCES product(newegg_id)
);


CREATE TABLE price (
  newegg_id VARCHAR(20),
  date DATETIME,
  price DOUBLE,
  PRIMARY KEY (newegg_id, date),
  FOREIGN KEY (newegg_id) REFERENCES product(newegg_id)
);

CREATE TABLE newegg_id_to_asin (
  newegg_id VARCHAR(20),
  asin CHAR(10),
  PRIMARY KEY (newegg_id),
  FOREIGN KEY (newegg_id) REFERENCES product(newegg_id)
);