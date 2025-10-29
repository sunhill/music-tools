dropdb spotify --host=127.0.0.1 --port=5432 --username=postgres
createdb spotify --host=127.0.0.1 --port=5432 --username=postgres
psql spotify -f src/postgres/schema/tables.sql --host=127.0.0.1 --port=5432 --username=postgres
