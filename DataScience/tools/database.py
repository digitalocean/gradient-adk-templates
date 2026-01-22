"""
Database connection and query execution tool.

Provides readonly access to PostgreSQL or MySQL databases with proper
connection pooling and error handling.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Database connection manager for PostgreSQL and MySQL.

    Uses readonly credentials to ensure the agent cannot modify data.
    """

    def __init__(
        self,
        db_type: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        ssl_mode: Optional[str] = None
    ):
        """
        Initialize database connection with credentials.

        If parameters are not provided, they are read from environment variables.
        """
        self.db_type = db_type or os.environ.get("DB_TYPE", "postgres")
        self.host = host or os.environ.get("DB_HOST")
        self.port = port or int(os.environ.get("DB_PORT", "25060"))
        self.database = database or os.environ.get("DB_NAME")
        self.user = user or os.environ.get("DB_USER")
        self.password = password or os.environ.get("DB_PASSWORD")
        self.ssl_mode = ssl_mode or os.environ.get("DB_SSL_MODE", "require")

        self._connection = None
        self._validate_config()

    def _validate_config(self):
        """Validate that all required configuration is present."""
        missing = []
        if not self.host:
            missing.append("DB_HOST")
        if not self.database:
            missing.append("DB_NAME")
        if not self.user:
            missing.append("DB_USER")
        if not self.password:
            missing.append("DB_PASSWORD")

        if missing:
            raise ValueError(f"Missing required database configuration: {', '.join(missing)}")

    def connect(self):
        """Establish database connection."""
        if self._connection is not None:
            return self._connection

        logger.info(f"Connecting to {self.db_type} database at {self.host}:{self.port}/{self.database}")

        if self.db_type == "postgres":
            import psycopg2
            self._connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password,
                sslmode=self.ssl_mode
            )
        elif self.db_type == "mysql":
            import mysql.connector
            self._connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                ssl_disabled=(self.ssl_mode == "disable")
            )
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

        logger.info("Database connection established")
        return self._connection

    def close(self):
        """Close the database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")

    @contextmanager
    def cursor(self):
        """Get a database cursor within a context manager."""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL SELECT query to execute
            params: Optional query parameters

        Returns:
            Dictionary with columns and rows
        """
        # Security check: only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for security reasons")

        # Additional safety checks
        dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "REVOKE"]
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        logger.info(f"Executing query: {query[:100]}...")

        with self.cursor() as cursor:
            cursor.execute(query, params)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch results
            rows = cursor.fetchall()

            logger.info(f"Query returned {len(rows)} rows")

            return {
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get database schema information including tables and columns.

        Returns:
            Dictionary with table information
        """
        tables = {}

        if self.db_type == "postgres":
            # Get tables
            table_query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            result = self.execute_query(table_query)

            for (table_name,) in result["rows"]:
                # Get columns for each table
                column_query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position
                """
                col_result = self.execute_query(column_query, (table_name,))

                tables[table_name] = {
                    "columns": [
                        {
                            "name": row[0],
                            "type": row[1],
                            "nullable": row[2] == "YES",
                            "default": row[3]
                        }
                        for row in col_result["rows"]
                    ]
                }

        elif self.db_type == "mysql":
            # Get tables
            table_query = f"""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{self.database}'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """
            result = self.execute_query(table_query)

            for (table_name,) in result["rows"]:
                # Get columns for each table
                column_query = f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = '{self.database}' AND table_name = '{table_name}'
                    ORDER BY ordinal_position
                """
                col_result = self.execute_query(column_query)

                tables[table_name] = {
                    "columns": [
                        {
                            "name": row[0],
                            "type": row[1],
                            "nullable": row[2] == "YES",
                            "default": row[3]
                        }
                        for row in col_result["rows"]
                    ]
                }

        return {"tables": tables}

    def get_sample_data(self, table_name: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get sample data from a table.

        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return

        Returns:
            Dictionary with sample data
        """
        # Validate table name to prevent SQL injection
        if not table_name.isidentifier():
            raise ValueError(f"Invalid table name: {table_name}")

        query = f"SELECT * FROM {table_name} LIMIT {int(limit)}"
        return self.execute_query(query)


# Global database connection instance
_db_connection: Optional[DatabaseConnection] = None


def get_database() -> DatabaseConnection:
    """Get or create the global database connection."""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def execute_sql(query: str) -> Dict[str, Any]:
    """
    Execute a SQL query and return results.

    This is the main tool function for agents to use.

    Args:
        query: SQL SELECT query to execute

    Returns:
        Dictionary with columns, rows, and row_count
    """
    db = get_database()
    return db.execute_query(query)


def get_schema() -> Dict[str, Any]:
    """
    Get the database schema information.

    Returns:
        Dictionary with table and column information
    """
    db = get_database()
    return db.get_schema_info()


def format_results_as_table(result: Dict[str, Any], max_rows: int = 20) -> str:
    """
    Format query results as a text table for display.

    Args:
        result: Query result dictionary
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not result.get("columns") or not result.get("rows"):
        return "No results"

    columns = result["columns"]
    rows = result["rows"][:max_rows]

    # Calculate column widths
    widths = [len(str(col)) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val) if val is not None else "NULL"))

    # Build table
    lines = []

    # Header
    header = " | ".join(str(col).ljust(widths[i]) for i, col in enumerate(columns))
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for row in rows:
        line = " | ".join(
            str(val if val is not None else "NULL").ljust(widths[i])
            for i, val in enumerate(row)
        )
        lines.append(line)

    if len(result["rows"]) > max_rows:
        lines.append(f"... ({len(result['rows']) - max_rows} more rows)")

    lines.append(f"\nTotal: {result['row_count']} rows")

    return "\n".join(lines)
