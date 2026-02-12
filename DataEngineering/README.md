# Data Engineering Agent Template

A data engineering agent built with LangGraph that helps you build and manage Snowflake data pipelines using dbt. This agent can create transformation pipelines, troubleshoot issues, ensure data quality, and explore your data warehouse.

## Key Features

### Pipeline Development
- Build and modify dbt pipelines following the medallion architecture
- Create staging, intermediate, and mart models
- Design data transformations with clean SQL
- Manage model dependencies and DAGs
- Generate properly documented dbt models

### Troubleshooting
- Diagnose pipeline failures and errors
- Analyze dbt logs and test results
- Fix compilation errors and broken models
- Debug data transformation issues
- Identify performance bottlenecks

### Data Quality
- Run comprehensive data quality checks
- Validate data transformations
- Compare source and target row counts
- Identify nulls, duplicates, and anomalies
- Check data freshness and completeness

### Data Exploration
- Explore database schemas and tables
- Sample data to understand structure
- Analyze column statistics and distributions
- Understand the existing data model

## How It Works

This agent is a **code assistant** for your data pipeline, not a direct data manipulator. Understanding this workflow is important:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR REQUEST                                   │
│            "Add a customer_tenure_days field to dim_customers"          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGENT ACTIONS                                    │
│  1. Reads existing model: dbt_project/models/marts/core/dim_customers.sql│
│  2. Modifies the SQL to add the new field                               │
│  3. Writes the updated file back to disk                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     YOU RUN: dbt run                                     │
│  dbt executes the SQL and creates/updates tables in Snowflake           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SNOWFLAKE TABLES UPDATED                              │
│  The dim_customers table now has the new customer_tenure_days column    │
└─────────────────────────────────────────────────────────────────────────┘
```

### What the Agent Can and Cannot Do

| Action | Can Do? | How |
|--------|---------|-----|
| Query Snowflake data | Yes | Executes SELECT queries directly |
| Create/edit dbt models | Yes | Writes to `dbt_project/models/*.sql` |
| Run dbt commands | Yes | Via `run_dbt_command` tool (if dbt is configured) |
| Create tables in Snowflake | No | Must go through dbt for version control |
| Run INSERT/UPDATE/DELETE | No | Only SELECT queries allowed for safety |
| Remember conversation history | Yes | Via `thread_id` parameter |

### Conversation History

The agent supports multi-turn conversations. Pass a `thread_id` to maintain context across requests:

```bash
# First request - get a thread_id back
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me the raw_customers table schema"}'

# Response includes: {"response": "...", "thread_id": "abc12345"}

# Follow-up request - use the same thread_id
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Now show me sample data from that table", "thread_id": "abc12345"}'

# The agent remembers you were looking at raw_customers
```

**How it works:**
- Without `thread_id`: Each request starts fresh (new conversation)
- With `thread_id`: Agent recalls previous messages and builds on them
- The agent can reference previous findings, continue work, and avoid repeating information

**Use cases for conversation history:**
- Iterative exploration: "Show me customers" → "Filter to just California" → "Now sort by order count"
- Building on analysis: "Check data quality" → "Tell me more about those nulls" → "How should I fix them?"
- Multi-step pipeline work: "Create a staging model" → "Add a new column" → "Now create a test for it"

### Why This Design?

Using dbt as the intermediary (rather than executing DDL directly) provides:
- **Version control** - All transformations are SQL files you can commit to git
- **Testing** - dbt can run data quality tests before deploying changes
- **Documentation** - Models are self-documenting with YAML schema files
- **Dependency management** - dbt handles the order of table creation
- **Idempotency** - Running `dbt run` multiple times is safe

---

## Agent Architecture

```
                    +--------------+
                    |   __start__  |
                    +--------------+
                           |
                           v
                   +---------------+
                   | route_request |  <-- Classifies task type
                   +---------------+
                           |
                           v
                  +----------------+
                  | gather_context |  <-- Gathers relevant data
                  +----------------+
                           |
                           v
                   +--------------+
                   | execute_task |  <-- Specialist agent works
                   +--------------+
                           |
                           v
                  +-----------------+
                  | format_response |
                  +-----------------+
                           |
                           v
                     +---------+
                     | __end__ |
                     +---------+
```

---

## Quick Setup

### 1. Prerequisites

- Python 3.9+
- A Snowflake account (free trial: https://signup.snowflake.com/)
- DigitalOcean account with Gradient AI access

### 2. Install Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```bash
# DigitalOcean Gradient AI
DIGITALOCEAN_INFERENCE_KEY=your_key_here

# Snowflake Connection
SNOWFLAKE_ACCOUNT=your_account.region    # e.g., abc12345.us-east-1
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=DATA_ENGINEERING_WH
SNOWFLAKE_DATABASE=DATA_ENGINEERING_DB
SNOWFLAKE_SCHEMA=RAW
SNOWFLAKE_ROLE=DATA_ENGINEERING_ROLE     # or your role
```

### 4. Run the Setup Script

The setup script creates the Snowflake database with sample data and initializes a dbt project:

```bash
# Set up everything (Snowflake + dbt project)
python setup/setup.py --all

# Or set up individually:
python setup/setup.py --snowflake  # Only Snowflake
python setup/setup.py --dbt        # Only dbt project

# To reset and start fresh (drops database and removes dbt project):
python setup/setup.py --reset
python setup/setup.py --all        # Then re-run setup
```

This creates:
- **Snowflake**: Database with medallion architecture schemas (RAW, STAGING, INTERMEDIATE, MARTS)
- **Sample Data**: E-commerce data (customers, orders, products, inventory, web events)
- **dbt Project**: Complete dbt project with staging models, tests, and macros

### 5. Test dbt Connection

The dbt profile is already configured in `dbt_project/profiles.yml` and uses your environment variables automatically.

Test the dbt connection:

```bash
cd dbt_project
dbt debug
```

### 6. Run the Agent Locally

```bash
export DIGITALOCEAN_API_TOKEN=<your-token>
gradient agent run
```

---

## Understanding the Data Pipeline

This section walks you through the data pipeline to see how raw, messy data gets transformed into clean, analytics-ready tables.

### Step 1: See the Problems in Raw Data

First, let's look at the raw data and its quality issues:

```bash
# Check the raw customers data - notice the problems
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me sample data from raw_customers and identify any data quality issues"}'
```

You'll see issues like:
- **Duplicate customer C001** (appears twice with different emails)
- **Invalid customer C013** (empty name, invalid email)
- **Inconsistent email casing** (some uppercase, some lowercase)
- **Null phone numbers**
- **Dates stored as strings**

```bash
# Run a data quality report to quantify the issues
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Run data quality checks on raw_customers and tell me what percentage of records have issues"}'
```

### Step 2: Build the Pipeline (Run dbt)

Before comparing, you need to run dbt to create the transformed tables:

```bash
cd dbt_project
dbt run
```

This executes all the transformations: staging → intermediate → marts.

### Step 3: See How Staging Cleans the Data

Now compare raw vs staged data:

```bash
# Compare raw vs staged customers
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare raw_customers to stg_customers. Show me how many rows are in each and explain what the staging model fixed."}'
```

The staging layer:
- **Removes duplicates** (14 raw → 12 staged customers)
- **Filters invalid records** (C013 with empty name is excluded)
- **Normalizes emails** (all lowercase)
- **Converts types** (strings → proper timestamps/booleans)
- **Handles nulls** (empty strings → NULL)

```bash
# See the actual transformation logic
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me the stg_customers model code and explain what each transformation does"}'
```

### Step 4: See How Intermediate Models Add Business Logic

```bash
# Explore the intermediate customer orders model
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me what int_customer_orders calculates. What business metrics does it add on top of the staged data?"}'
```

The intermediate layer:
- **Joins data** (customers + orders)
- **Calculates metrics** (total_orders, lifetime_value, avg_order_value)
- **Adds derived fields** (days_since_last_order)

### Step 5: See the Final Analytics-Ready Marts

```bash
# Query the final customer dimension
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Query dim_customers in the MARTS schema and show me customers segmented by value tier. How many are High Value vs Low Value?"}'

# Query the product dimension with inventory status
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Query dim_products and show me which products are low on stock or out of stock"}'

# See the RFM marketing segmentation
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Query customer_rfm and show me the customer segments. Which customers are Champions vs At Risk?"}'
```

The marts provide:
- **dim_customers**: Customer value tiers, recency segments
- **dim_products**: Stock status, performance tiers, margins
- **fct_orders**: Order facts with calculated discount percentages
- **customer_rfm**: Marketing segments for targeting campaigns

### Step 6: Make Changes and See the Impact

Now try extending the pipeline:

```bash
# Add a new metric to an existing model
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a days_as_customer field to dim_customers that shows how long each customer has been with us"}'

# Create a new mart for inventory alerts
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a new mart called inventory_alerts that shows products where quantity_available is below reorder_point"}'
```

After making changes, run dbt again to apply them:

```bash
cd dbt_project
dbt run
```

---

## Example Prompts

### Pipeline Development

```bash
# Create a new staging model
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a staging model for raw_customers that cleans the data and standardizes the email format"}'

# Add a new mart
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a customer lifetime value mart that calculates total spend and order frequency per customer"}'

# Modify an existing model
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a customer_tenure_days column to the dim_customers model"}'
```

### Troubleshooting

```bash
# Diagnose failures
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Why is my dbt run failing? Check the logs and test results"}'

# Fix specific errors
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "The stg_orders model is throwing a type mismatch error. Help me fix it"}'
```

### Data Quality

```bash
# Run quality checks
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Run data quality checks on the raw_customers table"}'

# Compare transformations
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Compare row counts between raw_orders and stg_orders to validate the transformation"}'

# Find anomalies
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Check for duplicate customer IDs in the staging layer"}'
```

### Data Exploration

```bash
# Explore schemas
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me all available tables and their schemas"}'

# Sample data
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me sample data from the raw_orders table"}'

# Analyze columns
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What are the most common values in the order_status column?"}'
```

### Multi-Turn Conversation Example

```bash
# Start a conversation - save the thread_id from the response
RESPONSE=$(curl -s -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me the raw_customers table"}')
echo $RESPONSE
THREAD_ID=$(echo $RESPONSE | jq -r '.thread_id')

# Continue the conversation with follow-ups
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"How many of those have null phone numbers?\", \"thread_id\": \"$THREAD_ID\"}"

curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Create a staging model that filters out invalid records\", \"thread_id\": \"$THREAD_ID\"}"

curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"Add a test to check for duplicate customer IDs\", \"thread_id\": \"$THREAD_ID\"}"
```

---

## Sample Data Overview

The setup script creates an e-commerce dataset perfect for learning data engineering:

### RAW Schema (Source Data)
| Table | Description | Rows |
|-------|-------------|------|
| raw_customers | Customer profiles from CRM | 14 |
| raw_orders | E-commerce orders | 13 |
| raw_order_items | Order line items | 20 |
| raw_products | Product catalog | 12 |
| raw_inventory | Inventory levels | 13 |
| raw_web_events | Clickstream data | 10 |

### Data Quality Challenges (Intentional)
The raw data includes realistic data quality issues for the agent to help you handle:
- **Duplicate records** (C001 appears twice with different emails)
- **Invalid data** (C013 has empty/invalid fields)
- **Type inconsistencies** (dates and numbers stored as strings)
- **Null values** (some customers missing phone numbers)
- **Case inconsistencies** (emails in different cases)

### dbt Project Structure
```
dbt_project/
├── models/
│   ├── staging/           # Source data cleaning
│   │   ├── stg_customers.sql
│   │   ├── stg_orders.sql
│   │   ├── stg_products.sql
│   │   ├── stg_order_items.sql
│   │   └── stg_inventory.sql
│   ├── intermediate/      # Business logic
│   │   ├── int_customer_orders.sql
│   │   └── int_product_performance.sql
│   └── marts/            # Analytics tables
│       ├── core/
│       │   ├── dim_customers.sql
│       │   ├── dim_products.sql
│       │   └── fct_orders.sql
│       └── marketing/
│           └── customer_rfm.sql
├── macros/               # Reusable SQL functions
├── tests/                # Custom data tests
└── dbt_project.yml
```

---

## Deployment

### Deploy to DigitalOcean Gradient AI

1. Update the agent name in `.gradient/agent.yml` if desired:

```yaml
agent_environment: main
agent_name: data-engineering-agent
entrypoint_file: main.py
```

2. Deploy:

```bash
gradient agent deploy
```

3. Test the deployed agent:

```bash
curl -X POST 'https://agents.do-ai.run/<AGENT_ID>/main/run' \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Show me the current dbt models in the pipeline"}'
```

### Deployment Caveats

**Single Warehouse Configuration**

This agent is designed to connect to a **single Snowflake warehouse** configured via environment variables. All requests share the same:
- Snowflake connection (account, user, password, warehouse, database)
- dbt project folder (`dbt_project/`)
- dbt profile configuration

**Conversation History Persistence**

The agent uses `MemorySaver` for conversation history, which stores state **in memory**:
- Conversations persist as long as the agent process is running
- **Restarting the agent clears all conversation history**
- In production with multiple instances, conversations may not be shared across instances

For production deployments requiring persistent conversations, consider:
- Using `SqliteSaver` for single-instance persistence
- Using a Redis or PostgreSQL backend for multi-instance deployments
- Implementing a custom checkpointer with your preferred storage

**Multi-User Interference**

When deployed, **all users share the same dbt project folder**. This means:
- User A creates a model → User B can see and modify it
- User A and User B editing the same model simultaneously may overwrite each other's changes
- Running `dbt run` affects everyone's view of the data

This template is best suited for:
- **Single-user development** environments
- **Team demos** where one person drives
- **Learning and experimentation**

### Improving for Multi-User Production Use

To support multiple concurrent users, consider these enhancements:

**Option 1: User-Isolated dbt Projects**
```
dbt_projects/
├── user_abc123/
│   └── models/...
├── user_def456/
│   └── models/...
```

Modify the agent to:
1. Accept a `user_id` parameter in requests
2. Create/use a separate dbt project folder per user
3. Use user-specific schemas in Snowflake (e.g., `STAGING_ABC123`)

**Option 2: Session-Based Workspaces**
- Generate a unique session ID for each conversation
- Clone the base dbt project to a session-specific folder
- Clean up old sessions periodically

**Option 3: Git-Based Workflow**
- Store dbt projects in a git repository
- Each user works on a branch
- Agent commits changes and opens pull requests
- Merging to main triggers `dbt run` in production

**Option 4: Read-Only Deployed Mode**
- Deploy the agent in read-only mode (exploration and troubleshooting only)
- Disable model creation/modification tools in production
- Keep pipeline development in local environments

---

## Project Structure

```
DataEngineering/
├── main.py                 # LangGraph agent workflow
├── tools/
│   ├── __init__.py
│   ├── snowflake_tools.py  # Snowflake operations
│   └── dbt_tools.py        # dbt pipeline management
├── setup/
│   ├── setup.py            # Automated setup script
│   └── setup_snowflake.sql # Snowflake DDL and sample data
├── dbt_project/            # Sample dbt project (created by setup)
│   ├── models/
│   ├── macros/
│   ├── tests/
│   └── dbt_project.yml
├── .gradient/
│   └── agent.yml           # Gradient AI configuration
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── README.md
```

---

## Security Notes

- The agent only executes SELECT queries directly on Snowflake
- DDL/DML operations go through dbt for proper version control
- Use a service role with minimal required permissions
- Never commit `.env` files to version control
- The setup script creates a dedicated role with appropriate permissions

---

## Troubleshooting

### Connection Issues
```bash
# Test Snowflake connection
python -c "from tools.snowflake_tools import get_snowflake_connection; c = get_snowflake_connection(); print('Connected!'); c.close()"

# Test dbt connection
cd dbt_project && dbt debug
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "Account not found" | Check SNOWFLAKE_ACCOUNT format (account.region) |
| "Warehouse suspended" | Warehouse auto-resumes, or manually resume in Snowflake |
| "dbt not found" | Run `pip install dbt-snowflake` |
| "Profile not found" | Run dbt commands from the dbt_project directory |

---

## Learn More

- [dbt Documentation](https://docs.getdbt.com/)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [DigitalOcean Gradient AI](https://www.digitalocean.com/products/gradient)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
