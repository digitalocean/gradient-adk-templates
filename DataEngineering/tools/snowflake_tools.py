"""
Snowflake tools for data engineering operations.

These tools provide direct access to Snowflake for schema exploration,
query execution, and data quality checks.
"""

import os
import logging
import traceback
from typing import Optional
from langchain_core.tools import tool
import snowflake.connector
from snowflake.connector import DictCursor

# Configure logging for Snowflake tools
logger = logging.getLogger(__name__)


def get_snowflake_connection():
    """Create a Snowflake connection using environment variables."""
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "DATA_ENGINEERING_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
    role = os.getenv("SNOWFLAKE_ROLE")

    logger.debug(f"[Snowflake] Connecting: account={account}, user={user}, warehouse={warehouse}, database={database}, schema={schema}, role={role}")

    return snowflake.connector.connect(
        account=account,
        user=user,
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=warehouse,
        database=database,
        schema=schema,
        role=role,
    )


@tool
def list_schemas() -> str:
    """List all schemas in the data engineering database.

    Returns the schemas following the medallion architecture:
    - RAW: Raw data from source systems
    - STAGING: Cleaned and standardized data
    - INTERMEDIATE: Business logic and transformations
    - MARTS: Final analytics-ready tables
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        cursor.execute(f"SHOW SCHEMAS IN DATABASE {db}")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"No schemas found in database {db}."

        lines = ["Schema | Description"]
        lines.append("-" * 50)
        for row in results:
            schema_name = row[1]
            comment = row[4] if len(row) > 4 and row[4] else ""
            lines.append(f"{schema_name} | {comment}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing schemas: {str(e)}"


@tool
def list_tables(schema_name: str = "RAW") -> str:
    """List all tables in a specified schema.

    Args:
        schema_name: Schema name (RAW, STAGING, INTERMEDIATE, MARTS). Default: RAW

    Returns table names, row counts, and comments.
    """
    logger.info(f"[list_tables] Listing tables in schema: {schema_name}")
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        sql = f"SHOW TABLES IN {db}.{schema_name}"
        logger.info(f"[list_tables] Executing: {sql}")
        cursor.execute(sql)
        results = cursor.fetchall()
        logger.info(f"[list_tables] Found {len(results)} tables")
        cursor.close()
        conn.close()

        if not results:
            return f"No tables found in {db}.{schema_name}."

        lines = [f"Tables in {schema_name}:", "-" * 50]
        for row in results:
            table_name = row[1]
            rows = row[5] if len(row) > 5 else "N/A"
            comment = row[6] if len(row) > 6 and row[6] else ""
            lines.append(f"- {table_name} ({rows} rows) {comment}")
            logger.debug(f"[list_tables]   - {table_name}")

        return "\n".join(lines)
    except Exception as e:
        error_msg = f"Error listing tables: {str(e)}"
        logger.error(f"[list_tables] {error_msg}")
        logger.error(f"[list_tables] Traceback:\n{traceback.format_exc()}")
        return error_msg


@tool
def get_table_schema(table_name: str, schema_name: str = "RAW") -> str:
    """Get the detailed schema of a table including column types and constraints.

    Args:
        table_name: Name of the table to describe.
        schema_name: Schema name (RAW, STAGING, INTERMEDIATE, MARTS). Default: RAW

    Returns column names, data types, and nullability.
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        full_name = f"{db}.{schema_name}.{table_name}"

        cursor.execute(f"DESCRIBE TABLE {full_name}")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        if not results:
            return f"No schema found for {full_name}."

        lines = [f"Schema for {schema_name}.{table_name}:", "-" * 60, "Column | Type | Nullable | Default"]
        lines.append("-" * 60)

        for row in results:
            col_name = row[0]
            col_type = row[1]
            nullable = "YES" if row[3] == "Y" else "NO"
            default = row[4] if len(row) > 4 and row[4] else ""
            lines.append(f"{col_name} | {col_type} | {nullable} | {default}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting table schema: {str(e)}"


@tool
def execute_query(sql: str, limit: int = 100) -> str:
    """Execute a SQL query and return results.

    Only SELECT queries are allowed for safety.

    Args:
        sql: The SQL query to execute.
        limit: Maximum rows to return (default 100).

    Returns formatted query results.
    """
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        logger.warning(f"[execute_query] Blocked non-SELECT query: {sql[:50]}...")
        return "Error: Only SELECT queries allowed. Use Snowflake console for DDL/DML."

    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(DictCursor)

        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {limit}"

        logger.info(f"[execute_query] Executing: {sql[:100]}...")
        cursor.execute(sql)
        results = cursor.fetchall()
        logger.info(f"[execute_query] Returned {len(results)} rows")
        cursor.close()
        conn.close()

        if not results:
            return "Query executed. No rows returned."

        columns = list(results[0].keys())
        lines = [" | ".join(columns), "-" * len(" | ".join(columns))]

        for row in results[:limit]:
            values = [str(row.get(col, "NULL"))[:40] for col in columns]
            lines.append(" | ".join(values))

        lines.append(f"\n({len(results)} row{'s' if len(results) != 1 else ''} returned)")
        return "\n".join(lines)
    except Exception as e:
        error_msg = f"Query error: {str(e)}"
        logger.error(f"[execute_query] {error_msg}")
        logger.error(f"[execute_query] SQL was: {sql}")
        logger.error(f"[execute_query] Traceback:\n{traceback.format_exc()}")
        return error_msg


@tool
def sample_table_data(table_name: str, schema_name: str = "RAW", num_rows: int = 5) -> str:
    """Get a sample of rows from a table to understand its data.

    Args:
        table_name: Name of the table to sample.
        schema_name: Schema name. Default: RAW
        num_rows: Number of sample rows (default 5).

    Returns sample rows from the table.
    """
    try:
        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        sql = f"SELECT * FROM {db}.{schema_name}.{table_name} LIMIT {num_rows}"
        return execute_query.invoke({"sql": sql, "limit": num_rows})
    except Exception as e:
        return f"Error sampling table: {str(e)}"


@tool
def check_data_quality(table_name: str, schema_name: str = "RAW") -> str:
    """Run data quality checks on a table.

    Checks for:
    - Row count
    - Null counts per column
    - Duplicate detection
    - Data freshness

    Args:
        table_name: Name of the table to check.
        schema_name: Schema name. Default: RAW

    Returns data quality report.
    """
    logger.info(f"[check_data_quality] Starting check for {schema_name}.{table_name}")
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(DictCursor)
        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        full_name = f"{db}.{schema_name}.{table_name}"
        logger.info(f"[check_data_quality] Full table name: {full_name}")

        report = [f"Data Quality Report: {schema_name}.{table_name}", "=" * 50]

        # Row count
        count_sql = f"SELECT COUNT(*) as cnt FROM {full_name}"
        logger.info(f"[check_data_quality] Executing: {count_sql}")
        cursor.execute(count_sql)
        result = cursor.fetchone()
        logger.info(f"[check_data_quality] Row count result: {result}")

        # Handle both dict and tuple results
        if isinstance(result, dict):
            row_count = result.get("CNT") or result.get("cnt") or 0
        else:
            row_count = result[0] if result else 0
        logger.info(f"[check_data_quality] Parsed row count: {row_count}")
        report.append(f"\nTotal Rows: {row_count:,}")

        # Get columns
        describe_sql = f"DESCRIBE TABLE {full_name}"
        logger.info(f"[check_data_quality] Executing: {describe_sql}")
        cursor.execute(describe_sql)
        describe_results = cursor.fetchall()
        logger.info(f"[check_data_quality] DESCRIBE returned {len(describe_results)} columns")

        # DESCRIBE returns tuples even with DictCursor, extract column names
        columns = []
        for row in describe_results:
            if isinstance(row, dict):
                col_name = row.get("name") or row.get("NAME") or list(row.values())[0]
            else:
                col_name = row[0]
            columns.append(col_name)
        logger.info(f"[check_data_quality] Columns: {columns[:5]}...")

        # Null counts
        report.append("\nNull Counts:")
        null_sql = ", ".join([f"SUM(CASE WHEN \"{col}\" IS NULL THEN 1 ELSE 0 END) as \"{col}_NULLS\"" for col in columns[:10]])
        full_null_sql = f"SELECT {null_sql} FROM {full_name}"
        logger.info(f"[check_data_quality] Null check SQL: {full_null_sql[:200]}...")
        cursor.execute(full_null_sql)
        null_result = cursor.fetchone()
        logger.info(f"[check_data_quality] Null result type: {type(null_result)}, value: {null_result}")

        for col in columns[:10]:
            key = f"{col}_NULLS"
            if isinstance(null_result, dict):
                null_count = null_result.get(key) or null_result.get(key.upper()) or 0
            else:
                # Handle tuple result
                idx = columns[:10].index(col)
                null_count = null_result[idx] if null_result and idx < len(null_result) else 0

            pct = (null_count / row_count * 100) if row_count > 0 else 0
            if null_count > 0:
                report.append(f"  - {col}: {null_count:,} ({pct:.1f}%)")

        # Check for _loaded_at column for freshness
        upper_columns = [c.upper() for c in columns]
        if "_LOADED_AT" in upper_columns:
            logger.info("[check_data_quality] Checking data freshness...")
            cursor.execute(f"SELECT MAX(_loaded_at) as latest, MIN(_loaded_at) as earliest FROM {full_name}")
            freshness = cursor.fetchone()
            report.append(f"\nData Freshness:")
            if isinstance(freshness, dict):
                report.append(f"  - Latest load: {freshness.get('LATEST') or freshness.get('latest')}")
                report.append(f"  - Earliest load: {freshness.get('EARLIEST') or freshness.get('earliest')}")
            else:
                report.append(f"  - Latest load: {freshness[0] if freshness else 'N/A'}")
                report.append(f"  - Earliest load: {freshness[1] if freshness else 'N/A'}")

        cursor.close()
        conn.close()

        logger.info("[check_data_quality] Quality check completed successfully")
        return "\n".join(report)
    except Exception as e:
        error_msg = f"Error running quality checks: {str(e)}"
        logger.error(f"[check_data_quality] {error_msg}")
        logger.error(f"[check_data_quality] Traceback:\n{traceback.format_exc()}")
        return error_msg


@tool
def compare_row_counts(source_table: str, target_table: str, source_schema_name: str = "RAW", target_schema_name: str = "STAGING") -> str:
    """Compare row counts between source and target tables.

    Useful for validating data pipeline transformations.

    Args:
        source_table: Source table name.
        target_table: Target table name.
        source_schema_name: Source schema (default: RAW).
        target_schema_name: Target schema (default: STAGING).

    Returns comparison of row counts.
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(DictCursor)
        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")

        cursor.execute(f"SELECT COUNT(*) as cnt FROM {db}.{source_schema_name}.{source_table}")
        source_count = cursor.fetchone()["CNT"]

        cursor.execute(f"SELECT COUNT(*) as cnt FROM {db}.{target_schema_name}.{target_table}")
        target_count = cursor.fetchone()["CNT"]

        cursor.close()
        conn.close()

        diff = target_count - source_count
        pct_diff = ((target_count - source_count) / source_count * 100) if source_count > 0 else 0

        lines = [
            "Row Count Comparison",
            "-" * 40,
            f"Source ({source_schema_name}.{source_table}): {source_count:,}",
            f"Target ({target_schema_name}.{target_table}): {target_count:,}",
            f"Difference: {diff:+,} ({pct_diff:+.1f}%)",
        ]

        if diff < 0:
            lines.append("\nNote: Target has fewer rows. Check for filtering in transformation.")
        elif diff > 0:
            lines.append("\nNote: Target has more rows. Check for duplicates or fan-out joins.")

        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing tables: {str(e)}"


@tool
def get_column_statistics(table_name: str, column_name: str, schema_name: str = "RAW") -> str:
    """Get detailed statistics for a specific column.

    Args:
        table_name: Name of the table.
        column_name: Name of the column to analyze.
        schema_name: Schema name (default: RAW).

    Returns column statistics including distinct count, min, max, and top values.
    """
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor(DictCursor)
        db = os.getenv("SNOWFLAKE_DATABASE", "DATA_ENGINEERING_DB")
        full_name = f"{db}.{schema_name}.{table_name}"

        # Basic stats
        stats_sql = f"""
        SELECT
            COUNT(*) as total_rows,
            COUNT({column_name}) as non_null_count,
            COUNT(DISTINCT {column_name}) as distinct_count,
            MIN({column_name}) as min_value,
            MAX({column_name}) as max_value
        FROM {full_name}
        """
        cursor.execute(stats_sql)
        stats = cursor.fetchone()

        # Top values
        top_sql = f"""
        SELECT {column_name}, COUNT(*) as cnt
        FROM {full_name}
        WHERE {column_name} IS NOT NULL
        GROUP BY {column_name}
        ORDER BY cnt DESC
        LIMIT 5
        """
        cursor.execute(top_sql)
        top_values = cursor.fetchall()

        cursor.close()
        conn.close()

        null_count = stats["TOTAL_ROWS"] - stats["NON_NULL_COUNT"]
        null_pct = (null_count / stats["TOTAL_ROWS"] * 100) if stats["TOTAL_ROWS"] > 0 else 0

        lines = [
            f"Column Statistics: {schema_name}.{table_name}.{column_name}",
            "-" * 50,
            f"Total Rows: {stats['TOTAL_ROWS']:,}",
            f"Non-Null Count: {stats['NON_NULL_COUNT']:,}",
            f"Null Count: {null_count:,} ({null_pct:.1f}%)",
            f"Distinct Values: {stats['DISTINCT_COUNT']:,}",
            f"Min Value: {stats['MIN_VALUE']}",
            f"Max Value: {stats['MAX_VALUE']}",
            "",
            "Top 5 Values:",
        ]

        for row in top_values:
            lines.append(f"  - {row[column_name]}: {row['CNT']:,}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting column statistics: {str(e)}"
