# Data Science Agent

A data science agent built with Gradient ADK and LangGraph that can query databases, analyze data, and generate visualizations using natural language.

## Features

- **Natural Language to SQL (NL2SQL)**: Ask questions in plain English and get SQL queries automatically generated and executed
- **Auto-Retry with Self-Healing**: If a SQL query fails, the agent automatically analyzes the error and retries with a corrected query (configurable, default: 5 retries)
- **Data Analysis**: Perform statistical analysis and data exploration with Python code execution
- **Visualizations**: Generate charts and graphs from your data
- **Multi-Database Support**: Works with PostgreSQL and MySQL on DigitalOcean Managed Databases
- **Security-First**: Uses readonly database credentials to prevent data modification

## Architecture

```
┌─────────────────┐
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Intent Classifier│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────────┐
│Schema │ │  NL2SQL   │
│ Info  │ │   Agent   │
└───────┘ └─────┬─────┘
                │
                ▼
         ┌──────────────┐
         │ Data Analyst │
         │    Agent     │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │  Response    │
         │ (+ Images)   │
         └──────────────┘
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up DigitalOcean Database

The setup script will create a managed database cluster on DigitalOcean, load sample data, and configure a readonly user.

```bash
# Set your DigitalOcean API token
export DIGITALOCEAN_API_TOKEN=your_token_here

# Run setup script
python scripts/setup_database.py --db-type postgres --region nyc1
```

Options:
- `--db-type`: `postgres` (default) or `mysql`
- `--region`: DigitalOcean region (default: `nyc1`)
- `--cluster-name`: Database cluster name (default: `data-science-agent-db`)
- `--db-name`: Database name (default: `flights_db`)
- `--readonly-user`: Readonly username (default: `readonly_agent`)

The script outputs connection details to `.env.database` which you can copy to your `.env` file.

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `DIGITALOCEAN_INFERENCE_KEY`: Your Gradient model access key
- `DB_TYPE`: `postgres` or `mysql`
- `DB_HOST`: Database hostname
- `DB_PORT`: Database port
- `DB_NAME`: Database name
- `DB_USER`: Readonly username
- `DB_PASSWORD`: Readonly user password
- `DB_SSL_MODE`: SSL mode (usually `require`)

### 4. Deploy to Gradient

```bash
gradient-adk deploy
```

## Usage

### Basic Queries

```python
from main import main

# Query data
result = main({"message": "How many flights were delayed last month?"})
print(result["summary"])
print(result["data_table"])

# Get schema information
result = main({"message": "What tables are in the database?"})
print(result["summary"])
```

### Analysis with Visualizations

```python
# Request analysis with visualization
result = main({"message": "Create a chart showing flight delays by day of week"})

# Access the generated image
if result.get("images"):
    for img in result["images"]:
        # Base64 encoded PNG
        print(f"Image saved to: {img['path']}")
        # img['base64'] contains the base64-encoded image data
```

### Query Retry Configuration

If a generated SQL query fails, the agent will automatically attempt to fix and retry it. By default, it retries up to 5 times.

```python
# Configure max retries (default: 5)
result = main({
    "message": "Show me the average revenue per customer segment",
    "max_query_retries": 3  # Retry up to 3 times on failure
})

# Disable retries
result = main({
    "message": "List all flights",
    "max_query_retries": 0  # No retries, fail immediately on error
})
```

### Example Questions

**Data Queries:**
- "Show me all flights from JFK to LAX"
- "How many customers are in each loyalty tier?"
- "What are the top 10 routes by revenue?"

**Analysis:**
- "What's the average delay by departure airport?"
- "Find the correlation between booking lead time and ticket price"
- "Which month has the most cancellations?"

**Visualizations:**
- "Create a bar chart of revenue by month"
- "Plot flight delays over time"
- "Show a heatmap of flights by hour and day of week"

## Database Schema

The sample database contains airline data:

- **airports**: Airport information (IATA codes, locations)
- **aircraft**: Fleet information (models, capacity)
- **customers**: Customer profiles and loyalty data
- **flights**: Flight schedules and actual times
- **tickets**: Ticket bookings and pricing
- **flight_history**: Historical flight data for analytics
- **ticket_sales_history**: Sales data with booking patterns

## Security

The agent uses a **readonly database user** that can only execute SELECT queries. This prevents:
- Data modification (INSERT, UPDATE, DELETE)
- Schema changes (CREATE, ALTER, DROP)
- Permission changes (GRANT, REVOKE)

Additional safety measures:
- SQL query validation before execution
- Keyword blocking for dangerous operations
- Sandboxed Python code execution

## Local Development

Run the agent locally:

```bash
# With a question
python main.py "What are the busiest airports?"

# Interactive mode
python main.py
```

## Project Structure

```
DataScience/
├── .gradient/
│   └── agent.yml          # Gradient agent configuration
├── agents/
│   ├── __init__.py
│   ├── nl2sql.py          # Natural language to SQL translation
│   └── data_analyst.py    # Data analysis and visualization
├── tools/
│   ├── __init__.py
│   └── database.py        # Database connection and queries
├── data/
│   ├── schema.sql         # Database schema
│   └── sample_data.sql    # Sample data for testing
├── scripts/
│   └── setup_database.py  # DigitalOcean database setup
├── outputs/               # Generated visualizations (gitignored)
├── main.py                # Main workflow and entrypoint
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore
└── README.md
```

## Troubleshooting

### Connection Issues

1. Verify environment variables are set correctly
2. Check that your IP is in the database trusted sources
3. Ensure SSL mode matches database requirements

### Query Errors

1. Check the generated SQL in the response
2. Verify table and column names exist
3. Review the error message for syntax issues

### Visualization Issues

1. Ensure matplotlib and seaborn are installed
2. Check the `outputs/` directory for saved images
3. Review the analysis code in the response
