DROP DATABASE itemcatalog;
DROP USER catalog;

CREATE ROLE catalog WITH login PASSWORD 'catalog';
-- \du

CREATE DATABASE itemcatalog WITH OWNER catalog;
-- \l

\c itemcatalog
REVOKE ALL ON SCHEMA public FROM public;
GRANT ALL ON SCHEMA public TO catalog;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON tables TO catalog;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, USAGE ON sequences TO catalog;
-- \z
