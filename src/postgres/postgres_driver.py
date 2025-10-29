from os import environ

import asyncpg


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        database=environ.get("POSTGRES_DATABASE", "spotify"),
        host=environ.get("POSTGRES_HOST", "localhost"),
        port=environ.get("POSTGRES_PORT", 5432),
        user=environ.get("POSTGRES_USER", "postgres"),
        password=environ.get("POSTGRES_PASSWORD"),
        max_size=50,
    )


class PostgresDriver:
    @classmethod
    async def count_table_size(cls, pool: asyncpg.Pool, table_name: str) -> int:
        async with pool.acquire() as conn:
            return await conn.fetchval(
                'SELECT COUNT(*) FROM "%s";' % table_name.replace('"', '""')
            )

    @classmethod
    async def execute_basic_procedure(
            cls, pool: asyncpg.Pool, procedure_name: str
    ) -> None:
        """Runs a procedure, passes no arguments and returns nothing"""
        async with pool.acquire() as conn:
            await conn.execute(
                'SELECT * FROM "%s"();' % procedure_name.replace('"', '""')
            )

    @classmethod
    async def execute_procedure(
            cls, pool: asyncpg.Pool, procedure_name: str, *args
    ) -> list[asyncpg.Record]:
        """Runs a procedure, can pass as many arguments as defined and returns the procedure's output"""
        async with pool.acquire() as conn:
            procedure_statement = "SELECT * FROM %s" % await cls._add_arguments(
                conn, procedure_name
            )
            return await conn.fetch(procedure_statement, *args)

    @classmethod
    async def _add_arguments(cls, conn: asyncpg.Connection, procedure_name: str):
        proc_args = await cls._get_procedures_arguments(conn, procedure_name)
        return '"%s"(%s)' % (
            procedure_name.replace('"', '""'),
            await cls._concatenate_arguments(conn, proc_args),
        )

    @staticmethod
    async def _get_procedures_arguments(conn, procedure_name):
        args = await conn.fetchval("select proargtypes from pg_proc where proname=$1;", procedure_name)
        return args

    @staticmethod
    async def _concatenate_arguments(conn, proc_args):
        count = 1
        args = []
        for proc_arg in proc_args:
            arg_type = await conn.fetchval(
                "select typname from pg_type where oid=$1;", proc_arg
            )
            args.append("$%i::%s" % (count, arg_type))
            count += 1
        return ", ".join(args)
