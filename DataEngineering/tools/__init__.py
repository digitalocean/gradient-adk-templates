"""
Data Engineering Agent Tools

This module provides tools for:
- Snowflake database operations (schema exploration, queries, data quality)
- dbt pipeline management (models, tests, dependencies)
"""

from .snowflake_tools import (
    get_snowflake_connection,
    list_schemas,
    list_tables,
    get_table_schema,
    execute_query,
    sample_table_data,
    check_data_quality,
    compare_row_counts,
    get_column_statistics,
)

from .dbt_tools import (
    list_dbt_models,
    read_dbt_model,
    get_model_dependencies,
    run_dbt_command,
    get_dbt_test_results,
    analyze_dbt_logs,
    create_dbt_model,
    update_dbt_model,
    generate_model_sql,
)

# All tools available to the agent
ALL_TOOLS = [
    # Snowflake tools
    list_schemas,
    list_tables,
    get_table_schema,
    execute_query,
    sample_table_data,
    check_data_quality,
    compare_row_counts,
    get_column_statistics,
    # dbt tools
    list_dbt_models,
    read_dbt_model,
    get_model_dependencies,
    run_dbt_command,
    get_dbt_test_results,
    analyze_dbt_logs,
    create_dbt_model,
    update_dbt_model,
    generate_model_sql,
]
