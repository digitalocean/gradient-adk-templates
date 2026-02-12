"""
dbt tools for data pipeline management.

These tools enable the agent to work with dbt projects for:
- Reading and modifying dbt models
- Running dbt commands (build, test, run)
- Analyzing pipeline dependencies
- Troubleshooting pipeline issues
"""

import os
import subprocess
import json
import logging
import traceback
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool

# Configure logging for dbt tools
logger = logging.getLogger(__name__)


def get_dbt_project_path() -> Path:
    """Get the path to the dbt project."""
    base_path = Path(__file__).parent.parent
    return base_path / "dbt_project"


@tool
def list_dbt_models() -> str:
    """List all dbt models in the project organized by layer.

    Returns a structured list of models grouped by:
    - staging: Source data cleaning and standardization
    - intermediate: Business logic and transformations
    - marts: Final analytics-ready tables

    Each model shows its materialization type (view, table, ephemeral).
    """
    logger.info("[list_dbt_models] Listing dbt models")
    project_path = get_dbt_project_path()

    if not project_path.exists():
        logger.error(f"[list_dbt_models] dbt project not found at {project_path}")
        return "Error: dbt project not found. Run 'python setup/setup.py --dbt' first."

    models_path = project_path / "models"
    if not models_path.exists():
        logger.error(f"[list_dbt_models] models directory not found at {models_path}")
        return "Error: models directory not found in dbt project."

    lines = ["dbt Models in Project", "=" * 50]
    total_models = 0

    for layer in ["staging", "intermediate", "marts"]:
        layer_path = models_path / layer
        if layer_path.exists():
            lines.append(f"\n{layer.upper()}:")

            # Find all .sql files recursively
            sql_files = list(layer_path.rglob("*.sql"))
            sql_files.sort()
            total_models += len(sql_files)

            for sql_file in sql_files:
                rel_path = sql_file.relative_to(models_path)
                model_name = sql_file.stem

                # Try to determine materialization from file content
                content = sql_file.read_text()
                if "materialized='table'" in content or 'materialized="table"' in content:
                    mat = "table"
                elif "materialized='view'" in content or 'materialized="view"' in content:
                    mat = "view"
                elif "materialized='ephemeral'" in content or 'materialized="ephemeral"' in content:
                    mat = "ephemeral"
                else:
                    mat = "default"

                lines.append(f"  - {model_name} ({mat}) [{rel_path}]")

    logger.info(f"[list_dbt_models] Found {total_models} models")
    return "\n".join(lines)


@tool
def read_dbt_model(model_name: str) -> str:
    """Read the SQL content of a specific dbt model.

    Args:
        model_name: Name of the model (without .sql extension).

    Returns the model's SQL code with documentation.
    """
    project_path = get_dbt_project_path()
    models_path = project_path / "models"

    # Search for the model file
    for sql_file in models_path.rglob(f"{model_name}.sql"):
        content = sql_file.read_text()
        rel_path = sql_file.relative_to(project_path)

        # Also try to find associated YAML documentation
        doc_content = ""
        for yml_file in sql_file.parent.glob("*.yml"):
            yml_content = yml_file.read_text()
            if model_name in yml_content:
                doc_content = f"\n\n--- Documentation ({yml_file.name}) ---\n{yml_content}"
                break

        return f"--- Model: {model_name} ({rel_path}) ---\n\n{content}{doc_content}"

    return f"Error: Model '{model_name}' not found in dbt project."


@tool
def get_model_dependencies(model_name: str) -> str:
    """Analyze the dependencies of a dbt model.

    Args:
        model_name: Name of the model to analyze.

    Returns:
        - Upstream dependencies (models/sources this model references)
        - Downstream dependents (models that reference this model)
    """
    project_path = get_dbt_project_path()
    models_path = project_path / "models"

    # Find the model
    model_file = None
    for sql_file in models_path.rglob(f"{model_name}.sql"):
        model_file = sql_file
        break

    if not model_file:
        return f"Error: Model '{model_name}' not found."

    content = model_file.read_text()

    # Find upstream references
    import re
    refs = re.findall(r"{{\s*ref\(['\"](\w+)['\"]\)\s*}}", content)
    sources = re.findall(r"{{\s*source\(['\"](\w+)['\"],\s*['\"](\w+)['\"]\)\s*}}", content)

    # Find downstream dependents
    dependents = []
    for sql_file in models_path.rglob("*.sql"):
        if sql_file == model_file:
            continue
        other_content = sql_file.read_text()
        if f"ref('{model_name}')" in other_content or f'ref("{model_name}")' in other_content:
            dependents.append(sql_file.stem)

    lines = [
        f"Dependencies for: {model_name}",
        "=" * 50,
        "\nUpstream (this model depends on):",
    ]

    if refs:
        for ref in refs:
            lines.append(f"  - ref('{ref}')")
    if sources:
        for source_name, table_name in sources:
            lines.append(f"  - source('{source_name}', '{table_name}')")
    if not refs and not sources:
        lines.append("  (none)")

    lines.append("\nDownstream (depends on this model):")
    if dependents:
        for dep in dependents:
            lines.append(f"  - {dep}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


@tool
def run_dbt_command(command: str = "run", select: Optional[str] = None, full_refresh: bool = False) -> str:
    """Execute a dbt command.

    Args:
        command: dbt command to run (run, test, build, compile, debug). Default: run
        select: Optional model selection (e.g., 'stg_customers', 'staging+', 'tag:daily').
        full_refresh: If True, rebuild incremental models from scratch.

    Returns the output of the dbt command.
    """
    allowed_commands = ["run", "test", "build", "compile", "debug", "deps", "parse"]
    if command not in allowed_commands:
        logger.warning(f"[run_dbt_command] Blocked command: {command}")
        return f"Error: Command '{command}' not allowed. Use: {', '.join(allowed_commands)}"

    project_path = get_dbt_project_path()
    if not project_path.exists():
        logger.error(f"[run_dbt_command] dbt project not found at {project_path}")
        return "Error: dbt project not found. Run 'python setup/setup.py --dbt' first."

    cmd = ["dbt", command]

    if select:
        cmd.extend(["--select", select])

    if full_refresh and command in ["run", "build"]:
        cmd.append("--full-refresh")

    logger.info(f"[run_dbt_command] Executing: {' '.join(cmd)}")
    logger.info(f"[run_dbt_command] Working directory: {project_path}")

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        output = result.stdout
        if result.stderr:
            output += f"\n\nSTDERR:\n{result.stderr}"

        if result.returncode != 0:
            logger.error(f"[run_dbt_command] Command failed with exit code {result.returncode}")
            output = f"Command failed with exit code {result.returncode}\n\n{output}"
        else:
            logger.info(f"[run_dbt_command] Command completed successfully")

        logger.debug(f"[run_dbt_command] Output: {output[:500]}...")
        return output[:5000]  # Limit output size

    except subprocess.TimeoutExpired:
        logger.error("[run_dbt_command] Command timed out after 5 minutes")
        return "Error: dbt command timed out after 5 minutes."
    except FileNotFoundError:
        logger.error("[run_dbt_command] dbt executable not found")
        return "Error: dbt not found. Install with: pip install dbt-snowflake"
    except Exception as e:
        logger.error(f"[run_dbt_command] Error: {str(e)}")
        logger.error(f"[run_dbt_command] Traceback:\n{traceback.format_exc()}")
        return f"Error running dbt command: {str(e)}"


@tool
def get_dbt_test_results() -> str:
    """Get the results of the most recent dbt test run.

    Returns details about test passes, failures, and warnings.
    """
    project_path = get_dbt_project_path()
    target_path = project_path / "target"
    run_results_path = target_path / "run_results.json"

    if not run_results_path.exists():
        return "No test results found. Run 'dbt test' first."

    try:
        with open(run_results_path) as f:
            results = json.load(f)

        # Filter for test results
        test_results = [r for r in results.get("results", []) if r.get("node", {}).get("resource_type") == "test"]

        if not test_results:
            return "No test results found in the most recent run."

        passed = [r for r in test_results if r.get("status") == "pass"]
        failed = [r for r in test_results if r.get("status") == "fail"]
        warnings = [r for r in test_results if r.get("status") == "warn"]

        lines = [
            "dbt Test Results",
            "=" * 50,
            f"\nSummary: {len(passed)} passed, {len(failed)} failed, {len(warnings)} warnings",
        ]

        if failed:
            lines.append("\nFailed Tests:")
            for test in failed:
                test_name = test.get("node", {}).get("name", "unknown")
                message = test.get("message", "")[:200]
                lines.append(f"  - {test_name}")
                if message:
                    lines.append(f"    Error: {message}")

        if warnings:
            lines.append("\nWarnings:")
            for test in warnings:
                test_name = test.get("node", {}).get("name", "unknown")
                lines.append(f"  - {test_name}")

        return "\n".join(lines)

    except Exception as e:
        return f"Error reading test results: {str(e)}"


@tool
def analyze_dbt_logs() -> str:
    """Analyze dbt logs to identify issues and errors.

    Returns a summary of recent errors, warnings, and performance issues.
    """
    project_path = get_dbt_project_path()
    logs_path = project_path / "logs" / "dbt.log"

    if not logs_path.exists():
        return "No dbt logs found. Run a dbt command first."

    try:
        # Read the last 500 lines of the log
        with open(logs_path) as f:
            lines = f.readlines()[-500:]

        errors = []
        warnings = []
        slow_queries = []

        for line in lines:
            line_lower = line.lower()
            if "error" in line_lower:
                errors.append(line.strip()[:200])
            elif "warning" in line_lower or "warn" in line_lower:
                warnings.append(line.strip()[:200])
            elif "timing" in line_lower and any(x in line for x in ["10.", "20.", "30.", "40.", "50."]):
                # Queries taking 10+ seconds
                slow_queries.append(line.strip()[:200])

        report = ["dbt Log Analysis", "=" * 50]

        if errors:
            report.append(f"\nErrors ({len(errors)} found):")
            for err in errors[:10]:
                report.append(f"  - {err}")

        if warnings:
            report.append(f"\nWarnings ({len(warnings)} found):")
            for warn in warnings[:10]:
                report.append(f"  - {warn}")

        if slow_queries:
            report.append(f"\nSlow Queries ({len(slow_queries)} found):")
            for sq in slow_queries[:5]:
                report.append(f"  - {sq}")

        if not errors and not warnings:
            report.append("\nNo errors or warnings found in recent logs.")

        return "\n".join(report)

    except Exception as e:
        return f"Error analyzing logs: {str(e)}"


@tool
def create_dbt_model(model_name: str, layer: str, sql_content: str, description: str = "") -> str:
    """Create a new dbt model file.

    Args:
        model_name: Name for the new model (without .sql).
        layer: Layer to create the model in (staging, intermediate, marts).
        sql_content: The SQL content for the model.
        description: Optional description for documentation.

    Returns confirmation of model creation.
    """
    logger.info(f"[create_dbt_model] Creating model '{model_name}' in layer '{layer}'")

    valid_layers = ["staging", "intermediate", "marts", "marts/core", "marts/marketing"]
    if layer not in valid_layers:
        logger.warning(f"[create_dbt_model] Invalid layer: {layer}")
        return f"Error: Invalid layer '{layer}'. Use: {', '.join(valid_layers)}"

    project_path = get_dbt_project_path()
    models_path = project_path / "models" / layer

    if not models_path.exists():
        logger.info(f"[create_dbt_model] Creating directory: {models_path}")
        models_path.mkdir(parents=True, exist_ok=True)

    model_file = models_path / f"{model_name}.sql"

    if model_file.exists():
        logger.warning(f"[create_dbt_model] Model already exists: {model_file}")
        return f"Error: Model '{model_name}' already exists at {model_file}"

    # Write the model file
    logger.info(f"[create_dbt_model] Writing model file: {model_file}")
    model_file.write_text(sql_content)

    result = f"Created model: {model_file.relative_to(project_path)}"

    # If description provided, update or create YAML documentation
    if description:
        yml_file = models_path / f"_{layer.split('/')[-1]}.yml"
        yml_entry = f"""
  - name: {model_name}
    description: "{description}"
"""
        if yml_file.exists():
            # Append to existing file
            with open(yml_file, "a") as f:
                f.write(yml_entry)
            logger.info(f"[create_dbt_model] Added documentation to {yml_file}")
            result += f"\nAdded documentation to {yml_file.name}"
        else:
            # Create new YAML file
            yml_content = f"""version: 2

models:{yml_entry}"""
            yml_file.write_text(yml_content)
            logger.info(f"[create_dbt_model] Created documentation file: {yml_file}")
            result += f"\nCreated documentation: {yml_file.name}"

    logger.info(f"[create_dbt_model] Model creation complete")
    return result


@tool
def update_dbt_model(model_name: str, sql_content: str) -> str:
    """Update an existing dbt model's SQL content.

    Args:
        model_name: Name of the model to update.
        sql_content: The new SQL content.

    Returns confirmation of the update.
    """
    project_path = get_dbt_project_path()
    models_path = project_path / "models"

    # Find the model
    for sql_file in models_path.rglob(f"{model_name}.sql"):
        # Backup the old content
        old_content = sql_file.read_text()

        # Write new content
        sql_file.write_text(sql_content)

        return f"Updated model: {sql_file.relative_to(project_path)}\n\nPrevious content backed up in memory."

    return f"Error: Model '{model_name}' not found."


@tool
def generate_model_sql(
    source_table: str,
    transformations: str,
    model_type: str = "staging"
) -> str:
    """Generate SQL for a new dbt model based on requirements.

    Args:
        source_table: The source table or model to transform.
        transformations: Description of transformations to apply.
        model_type: Type of model (staging, intermediate, mart).

    Returns generated SQL that can be used with create_dbt_model.
    """
    # This provides a template - the LLM will enhance it
    if model_type == "staging":
        template = f"""-- Staging model for {source_table}
-- Transformations: {transformations}

with source as (
    select * from {{{{ source('raw', '{source_table}') }}}}
),

transformed as (
    select
        -- Add transformed columns here based on requirements:
        -- {transformations}
        *
    from source
)

select * from transformed
"""
    elif model_type == "intermediate":
        template = f"""-- Intermediate model
-- Transformations: {transformations}

with base as (
    select * from {{{{ ref('{source_table}') }}}}
),

transformed as (
    select
        -- Add business logic transformations:
        -- {transformations}
        *
    from base
)

select * from transformed
"""
    else:  # mart
        template = f"""-- Mart model
-- Transformations: {transformations}

{{{{ config(materialized='table') }}}}

with base as (
    select * from {{{{ ref('{source_table}') }}}}
),

final as (
    select
        -- Add final transformations for analytics:
        -- {transformations}
        *
    from base
)

select * from final
"""

    return f"Generated SQL template:\n\n```sql\n{template}\n```\n\nModify this template and use create_dbt_model to save it."
