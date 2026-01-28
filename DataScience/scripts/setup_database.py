#!/usr/bin/env python3
"""
DigitalOcean Database Setup Script

This script:
1. Creates a PostgreSQL or MySQL database cluster on DigitalOcean
2. Waits for the cluster to be ready
3. Creates a readonly user for the agent
4. Loads the schema and sample data
5. Outputs connection details for the .env file

Usage:
    python setup_database.py --db-type postgres --region nyc1
    python setup_database.py --db-type mysql --region sfo2

Requirements:
    - DIGITALOCEAN_API_TOKEN environment variable
    - pip install requests psycopg2-binary mysql-connector-python
"""

import os
import sys
import time
import argparse
import secrets
import string
import requests
from pathlib import Path

# DigitalOcean API base URL
DO_API_BASE = "https://api.digitalocean.com/v2"


def get_api_token():
    """Get DigitalOcean API token from environment."""
    token = os.environ.get("DIGITALOCEAN_API_TOKEN")
    if not token:
        print("Error: DIGITALOCEAN_API_TOKEN environment variable not set")
        sys.exit(1)
    return token


def generate_password(length=24):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def api_request(method, endpoint, token, data=None):
    """Make a request to the DigitalOcean API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{DO_API_BASE}/{endpoint}"

    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    return response


def find_existing_cluster(token, cluster_name, db_type):
    """Find an existing database cluster by name."""
    print(f"Checking for existing cluster '{cluster_name}'...")

    response = api_request("GET", "databases", token)

    if response.status_code != 200:
        print(f"Error listing clusters: {response.status_code}")
        return None

    clusters = response.json().get("databases", [])

    # Map db_type to DigitalOcean engine
    engine_map = {
        "postgres": "pg",
        "mysql": "mysql"
    }
    engine = engine_map.get(db_type)

    for cluster in clusters:
        if cluster.get("name") == cluster_name and cluster.get("engine") == engine:
            print(f"Found existing cluster '{cluster_name}' with ID: {cluster['id']}")
            return cluster

    return None


def create_database_cluster(token, db_type, region, cluster_name):
    """Create a new database cluster on DigitalOcean, or return existing one."""

    # First check if cluster already exists
    existing = find_existing_cluster(token, cluster_name, db_type)
    if existing:
        print(f"Using existing cluster '{cluster_name}'")
        return existing

    print(f"Creating {db_type} database cluster '{cluster_name}' in {region}...")

    # Map db_type to DigitalOcean engine
    engine_map = {
        "postgres": "pg",
        "mysql": "mysql"
    }
    engine = engine_map.get(db_type)
    if not engine:
        print(f"Error: Unsupported database type: {db_type}")
        sys.exit(1)

    # Database cluster configuration
    data = {
        "name": cluster_name,
        "engine": engine,
        "version": "16" if db_type == "postgres" else "8",
        "region": region,
        "size": "db-s-1vcpu-1gb",  # Smallest size for development
        "num_nodes": 1,
        "tags": ["data-science-agent", "gradient-adk"]
    }

    response = api_request("POST", "databases", token, data)

    if response.status_code == 201:
        cluster = response.json()["database"]
        print(f"Database cluster created with ID: {cluster['id']}")
        return cluster
    elif response.status_code == 409:
        # Cluster already exists (race condition), try to find it
        print(f"Cluster '{cluster_name}' already exists, fetching details...")
        existing = find_existing_cluster(token, cluster_name, db_type)
        if existing:
            return existing
        print("Error: Could not find existing cluster")
        sys.exit(1)
    else:
        print(f"Error creating database cluster: {response.status_code}")
        print(response.json())
        sys.exit(1)


def wait_for_cluster_ready(token, cluster_id, timeout=600):
    """Wait for the database cluster to be online."""
    # First check if already online
    response = api_request("GET", f"databases/{cluster_id}", token)
    if response.status_code == 200:
        cluster = response.json()["database"]
        status = cluster.get("status")
        if status == "online":
            print("Database cluster is already online!")
            return cluster

    print("Waiting for database cluster to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = api_request("GET", f"databases/{cluster_id}", token)

        if response.status_code == 200:
            cluster = response.json()["database"]
            status = cluster.get("status")
            print(f"  Status: {status}")

            if status == "online":
                print("Database cluster is ready!")
                return cluster
        else:
            print(f"Error checking cluster status: {response.status_code}")

        time.sleep(30)  # Check every 30 seconds

    print("Timeout waiting for database cluster to be ready")
    sys.exit(1)


def find_existing_database(token, cluster_id, db_name):
    """Check if a database already exists in the cluster."""
    response = api_request("GET", f"databases/{cluster_id}/dbs", token)

    if response.status_code != 200:
        return None

    databases = response.json().get("dbs", [])
    for db in databases:
        if db.get("name") == db_name:
            return db

    return None


def create_database(token, cluster_id, db_name):
    """Create a database in the cluster, or return existing one."""
    print(f"Creating database '{db_name}'...")

    # Check if database already exists
    existing = find_existing_database(token, cluster_id, db_name)
    if existing:
        print(f"Database '{db_name}' already exists")
        return existing

    data = {"name": db_name}
    response = api_request("POST", f"databases/{cluster_id}/dbs", token, data)

    if response.status_code == 201:
        print(f"Database '{db_name}' created successfully")
        return response.json()["db"]
    elif response.status_code == 409:
        # Race condition - database was created between check and create
        print(f"Database '{db_name}' already exists")
        return {"name": db_name}
    else:
        print(f"Error creating database: {response.status_code}")
        print(response.json())
        sys.exit(1)


def find_existing_user(token, cluster_id, username):
    """Check if a user already exists in the cluster."""
    response = api_request("GET", f"databases/{cluster_id}/users/{username}", token)

    if response.status_code == 200:
        return response.json().get("user")

    return None


def create_readonly_user(token, cluster_id, username, db_type):
    """Create a readonly user for the agent, or return existing one."""
    print(f"Creating readonly user '{username}'...")

    # Check if user already exists
    existing = find_existing_user(token, cluster_id, username)
    if existing:
        print(f"User '{username}' already exists")
        return existing

    data = {
        "name": username,
        "mysql_settings": {"auth_plugin": "caching_sha2_password"} if db_type == "mysql" else None
    }

    # Remove None values
    data = {k: v for k, v in data.items() if v is not None}

    response = api_request("POST", f"databases/{cluster_id}/users", token, data)

    if response.status_code == 201:
        user = response.json()["user"]
        print(f"User '{username}' created successfully")
        return user
    elif response.status_code == 409:
        # Race condition - user was created between check and create
        print(f"User '{username}' already exists, fetching details...")
        response = api_request("GET", f"databases/{cluster_id}/users/{username}", token)
        if response.status_code == 200:
            return response.json()["user"]
        else:
            print(f"Error fetching user: {response.status_code}")
            sys.exit(1)
    else:
        print(f"Error creating user: {response.status_code}")
        print(response.json())
        sys.exit(1)


def load_schema_and_data(connection_params, db_type):
    """Load the schema and sample data into the database."""
    print("Loading schema and sample data...")

    # Get the data directory
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    schema_file = data_dir / "schema.sql"
    data_file = data_dir / "sample_data.sql"

    if not schema_file.exists():
        print(f"Error: Schema file not found: {schema_file}")
        sys.exit(1)

    schema_sql = schema_file.read_text()
    data_sql = data_file.read_text() if data_file.exists() else ""

    schema_errors = 0
    data_errors = 0

    if db_type == "postgres":
        import psycopg2
        conn = psycopg2.connect(**connection_params)
        conn.autocommit = True
        cursor = conn.cursor()

        # Execute schema (statement by statement for better error handling)
        print("  Executing schema...")
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                except psycopg2.errors.DuplicateTable:
                    print(f"  Table already exists, skipping...")
                    schema_errors += 1
                except psycopg2.errors.DuplicateObject:
                    print(f"  Object already exists, skipping...")
                    schema_errors += 1
                except Exception as e:
                    print(f"  Schema warning: {e}")
                    schema_errors += 1

        # Execute sample data
        if data_sql:
            print("  Loading sample data...")
            for statement in data_sql.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except psycopg2.errors.UniqueViolation:
                        # Data already exists, skip
                        data_errors += 1
                    except Exception as e:
                        print(f"  Data warning: {e}")
                        data_errors += 1

        cursor.close()
        conn.close()

    elif db_type == "mysql":
        import mysql.connector
        from mysql.connector import errorcode
        conn = mysql.connector.connect(**connection_params)
        cursor = conn.cursor()

        # Execute schema (split by semicolons for MySQL)
        print("  Executing schema...")
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement:
                # Adapt PostgreSQL syntax for MySQL
                statement = statement.replace('SERIAL', 'INT AUTO_INCREMENT')
                # Keep IF NOT EXISTS for CREATE TABLE
                # Convert CREATE INDEX IF NOT EXISTS to MySQL syntax
                if 'CREATE INDEX IF NOT EXISTS' in statement:
                    # MySQL 8.0+ supports IF NOT EXISTS for indexes
                    pass
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    if e.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                        print(f"  Table already exists, skipping...")
                        schema_errors += 1
                    elif e.errno == errorcode.ER_DUP_KEYNAME:
                        print(f"  Index already exists, skipping...")
                        schema_errors += 1
                    else:
                        print(f"  Schema warning: {e}")
                        schema_errors += 1

        conn.commit()

        # Execute sample data
        if data_sql:
            print("  Loading sample data...")
            for statement in data_sql.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement)
                    except mysql.connector.Error as e:
                        if e.errno == errorcode.ER_DUP_ENTRY:
                            # Data already exists, skip
                            data_errors += 1
                        else:
                            print(f"  Data warning: {e}")
                            data_errors += 1

            conn.commit()

        cursor.close()
        conn.close()

    if schema_errors > 0:
        print(f"  Schema: {schema_errors} objects already existed (OK)")
    if data_errors > 0:
        print(f"  Data: {data_errors} records already existed (OK)")
    print("Schema and data loaded successfully!")


def grant_readonly_permissions(connection_params, db_type, db_name, readonly_user):
    """Grant readonly permissions to the readonly user."""
    print(f"Granting readonly permissions to '{readonly_user}'...")

    if db_type == "postgres":
        import psycopg2
        conn = psycopg2.connect(**connection_params)
        conn.autocommit = True
        cursor = conn.cursor()

        grants = [
            f"GRANT CONNECT ON DATABASE {db_name} TO {readonly_user};",
            f"GRANT USAGE ON SCHEMA public TO {readonly_user};",
            f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {readonly_user};",
            f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {readonly_user};"
        ]

        for grant in grants:
            try:
                cursor.execute(grant)
                print(f"  Executed: {grant[:50]}...")
            except Exception as e:
                print(f"  Warning: {e}")

        cursor.close()
        conn.close()

    elif db_type == "mysql":
        import mysql.connector
        conn = mysql.connector.connect(**connection_params)
        cursor = conn.cursor()

        grant = f"GRANT SELECT ON {db_name}.* TO '{readonly_user}'@'%';"
        try:
            cursor.execute(grant)
            cursor.execute("FLUSH PRIVILEGES;")
            print(f"  Granted SELECT on {db_name} to {readonly_user}")
        except Exception as e:
            print(f"  Warning: {e}")

        conn.commit()
        cursor.close()
        conn.close()

    print("Readonly permissions granted!")


def write_env_file(env_vars, output_path):
    """Write environment variables to a file."""
    print(f"Writing connection details to {output_path}...")

    lines = [
        "# Database Configuration (generated by setup script)",
        f"DB_TYPE={env_vars['db_type']}",
        f"DB_HOST={env_vars['host']}",
        f"DB_PORT={env_vars['port']}",
        f"DB_NAME={env_vars['database']}",
        f"DB_USER={env_vars['readonly_user']}",
        f"DB_PASSWORD={env_vars['readonly_password']}",
        f"DB_SSL_MODE=require",
        "",
        "# Admin credentials (for reference only - do not use in agent)",
        f"# DB_ADMIN_USER={env_vars['admin_user']}",
        f"# DB_ADMIN_PASSWORD={env_vars['admin_password']}",
        ""
    ]

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Connection details saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Setup DigitalOcean database for Data Science Agent")
    parser.add_argument("--db-type", choices=["postgres", "mysql"], default="postgres",
                        help="Database type (default: postgres)")
    parser.add_argument("--region", default="nyc1",
                        help="DigitalOcean region (default: nyc1)")
    parser.add_argument("--cluster-name", default="data-science-agent-db",
                        help="Database cluster name")
    parser.add_argument("--db-name", default="flights_db",
                        help="Database name")
    parser.add_argument("--readonly-user", default="readonly_agent",
                        help="Readonly user name for the agent")
    parser.add_argument("--skip-create", action="store_true",
                        help="Skip cluster creation (use existing cluster)")
    parser.add_argument("--cluster-id",
                        help="Existing cluster ID (required with --skip-create)")

    args = parser.parse_args()

    token = get_api_token()

    if args.skip_create:
        if not args.cluster_id:
            print("Error: --cluster-id required when using --skip-create")
            sys.exit(1)
        cluster_id = args.cluster_id
        # Get cluster details
        response = api_request("GET", f"databases/{cluster_id}", token)
        if response.status_code != 200:
            print(f"Error fetching cluster: {response.status_code}")
            sys.exit(1)
        cluster = response.json()["database"]
    else:
        # Create new cluster
        cluster = create_database_cluster(token, args.db_type, args.region, args.cluster_name)
        cluster_id = cluster["id"]

        # Wait for cluster to be ready
        cluster = wait_for_cluster_ready(token, cluster_id)

    # Get connection details
    connection = cluster.get("connection", {})
    host = connection.get("host")
    port = connection.get("port")
    admin_user = connection.get("user")
    admin_password = connection.get("password")

    if not all([host, port, admin_user, admin_password]):
        print("Error: Could not get connection details from cluster")
        print(f"Cluster details: {cluster}")
        sys.exit(1)

    print(f"\nCluster connection details:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Admin User: {admin_user}")

    # Create the database
    create_database(token, cluster_id, args.db_name)

    # Create readonly user
    readonly_user_info = create_readonly_user(token, cluster_id, args.readonly_user, args.db_type)
    readonly_password = readonly_user_info.get("password")

    # Connection params for admin
    if args.db_type == "postgres":
        admin_conn_params = {
            "host": host,
            "port": port,
            "user": admin_user,
            "password": admin_password,
            "dbname": args.db_name,
            "sslmode": "require"
        }
    else:  # mysql
        admin_conn_params = {
            "host": host,
            "port": port,
            "user": admin_user,
            "password": admin_password,
            "database": args.db_name,
            "ssl_disabled": False
        }

    # Load schema and data
    load_schema_and_data(admin_conn_params, args.db_type)

    # Grant readonly permissions
    grant_readonly_permissions(admin_conn_params, args.db_type, args.db_name, args.readonly_user)

    # Write env file
    script_dir = Path(__file__).parent
    env_path = script_dir.parent / ".env.database"

    env_vars = {
        "db_type": args.db_type,
        "host": host,
        "port": port,
        "database": args.db_name,
        "readonly_user": args.readonly_user,
        "readonly_password": readonly_password,
        "admin_user": admin_user,
        "admin_password": admin_password
    }

    write_env_file(env_vars, env_path)

    print("\n" + "=" * 60)
    print("DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nConnection details saved to: {env_path}")
    print("\nTo use with the agent, copy these values to your .env file:")
    print(f"  DB_TYPE={args.db_type}")
    print(f"  DB_HOST={host}")
    print(f"  DB_PORT={port}")
    print(f"  DB_NAME={args.db_name}")
    print(f"  DB_USER={args.readonly_user}")
    print(f"  DB_PASSWORD={readonly_password}")
    print(f"  DB_SSL_MODE=require")
    print("\nNote: The agent uses a READONLY user for security.")
    print("It cannot modify or delete data in the database.")


if __name__ == "__main__":
    main()
