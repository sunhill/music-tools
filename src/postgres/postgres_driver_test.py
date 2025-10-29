import os
import unittest
from unittest.mock import patch, AsyncMock

import asyncpg

from postgres.postgres_driver import (
    PostgresDriver,
    create_pool,
)

PATCH_LOCATION = "storage_drivers.postgres.postgres_driver"


@patch(f"{PATCH_LOCATION}.asyncpg", new_callable=AsyncMock)
class PostgresCreatePoolTest(unittest.IsolatedAsyncioTestCase):
    async def test_uses_defaults_to_create_connection_pool(self, asyncpg_spy):
        with patch.dict(os.environ, {"POSTGRES_PASSWORD": "not-a-real-password"}):
            await create_pool()

            asyncpg_spy.create_pool.assert_called_with(
                database="illuminate",
                host="localhost",
                port=5432,
                user="postgres",
                password="not-a-real-password",
                max_size=50,
            )

    async def test_passes_environment_variables_to_create_connection_pool(
        self, asyncpg_spy
    ):
        with patch.dict(
            os.environ,
            {
                "POSTGRES_DATABASE": "not_illuminate",
                "POSTGRES_HOST": "not_localhost",
                "POSTGRES_PORT": 54320,
                "POSTGRES_USER": "not_postgres",
                "POSTGRES_PASSWORD": "not-a-real-password",
            },
            clear=True,
        ):
            await create_pool()

            asyncpg_spy.create_pool.assert_called_with(
                database="not_illuminate",
                host="not_localhost",
                port=54320,
                user="not_postgres",
                password="not-a-real-password",
                max_size=50,
            )

            yield  # Needed to clear the env vars properly after the test


ENV_VARS = {"POSTGRES_PASSWORD": "not-a-real-password"}
PROCEDURE_NAME = "SomeProcedure"


class PostgresDriverTest(unittest.IsolatedAsyncioTestCase):
    async def test_counts_table_size(self):
        with (
            patch(f"{PATCH_LOCATION}.asyncpg.Pool", spec=asyncpg.Pool) as mock_pool,
            patch.dict(os.environ, ENV_VARS),
        ):
            conn = AsyncMock()
            conn.fetchval.return_value = 5
            mock_pool.acquire().__aenter__.return_value = conn

            self.assertEqual(
                5, await PostgresDriver.count_table_size(mock_pool, "SomeTable")
            )

    async def test_executes_basic_procedure_without_args_nor_return(self):
        with (
            patch(f"{PATCH_LOCATION}.asyncpg.Pool", spec=asyncpg.Pool) as mock_pool,
            patch.dict(os.environ, ENV_VARS),
        ):
            conn = AsyncMock()
            conn.execute.return_value = None
            mock_pool.acquire().__aenter__.return_value = conn

            await PostgresDriver.execute_basic_procedure(mock_pool, PROCEDURE_NAME)

            conn.execute.assert_called_with('SELECT * FROM "SomeProcedure"();')

    async def test_executes_procedure_with_single_arg(self):
        with (
            patch(f"{PATCH_LOCATION}.asyncpg.Pool", spec=asyncpg.Pool) as mock_pool,
            patch.dict(os.environ, ENV_VARS),
        ):
            conn_attrs = {
                "fetch.return_value": [],
                "fetchval.side_effect": [["maximum"], "integer"],
            }
            conn = AsyncMock(**conn_attrs)
            mock_pool.acquire().__aenter__.return_value = conn

            await PostgresDriver.execute_procedure(mock_pool, PROCEDURE_NAME, 1000)

            conn.fetch.assert_called_with(
                'SELECT * FROM "SomeProcedure"($1::integer)', 1000
            )

    async def test_executes_procedure_and_returns_output(self):
        with (
            patch(f"{PATCH_LOCATION}.asyncpg.Pool", spec=asyncpg.Pool) as mock_pool,
            patch.dict(os.environ, ENV_VARS),
        ):
            conn_attrs = {
                "fetch.return_value": [("output_1", "output_2")],
                "fetchval.side_effect": [["maximum"], "integer"],
            }
            conn = AsyncMock(**conn_attrs)
            mock_pool.acquire().__aenter__.return_value = conn

            self.assertEqual(
                [("output_1", "output_2")],
                await PostgresDriver.execute_procedure(mock_pool, PROCEDURE_NAME, 1000),
            )

    async def test_executes_procedure_with_multiple_args_of_different_types(self):
        with (
            patch(f"{PATCH_LOCATION}.asyncpg.Pool", spec=asyncpg.Pool) as mock_pool,
            patch.dict(os.environ, ENV_VARS),
        ):
            conn_attrs = {
                "fetch.return_value": [
                    ("output_1a", "output_1b"),
                    ("output_2a", "output_2b"),
                ],
                "fetchval.side_effect": [
                    ["maximum", "text_field", "boolean_field"],
                    "integer",
                    "text",
                    "boolean",
                ],
            }
            conn = AsyncMock(**conn_attrs)
            mock_pool.acquire().__aenter__.return_value = conn

            output = await PostgresDriver.execute_procedure(
                mock_pool, PROCEDURE_NAME, 1000, "some_text", False
            )

            conn.fetch.assert_called_with(
                'SELECT * FROM "SomeProcedure"($1::integer, $2::text, $3::boolean)',
                1000,
                "some_text",
                False,
            )
            self.assertEqual(
                [("output_1a", "output_1b"), ("output_2a", "output_2b")], output
            )
