# DataScience - Natural Language to SQL Agent

A data science agent that converts natural language questions into SQL queries, executes them against your database, analyzes results, and generates visualizations. Features self-healing queries that automatically retry on failure.

## Use Case

Enable non-technical users to query databases using plain English. This template demonstrates NL2SQL conversion, automatic error recovery, data analysis with Python, and chart generation - all through a conversational interface.

**When to use this template:**
- You need a natural language interface to databases
- You want to connect agents to DigitalOcean Managed Databases
- You need code execution (Python) within agent workflows

## Key Concepts

**Connecting to managed resources** is essential for production agents. This template shows how to securely connect to DigitalOcean Managed Databases (PostgreSQL or MySQL) using readonly credentials. The included setup script provisions a database cluster and creates sample data, demonstrating the full workflow from infrastructure to agent deployment.

**Code execution within agents** enables powerful data analysis. After generating and executing SQL queries, the agent runs Python code to analyze results and create visualizations using matplotlib and pandas. This pattern - combining LLM reasoning with code execution - lets agents perform complex computations that would be difficult with prompting alone.

The agent also features **self-healing queries**: when a SQL query fails, the agent analyzes the error, fixes the query, and retries automatically (up to 5 times), making it resilient to schema mismatches and syntax errors.

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                      DataScience Agent Pipeline                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Input: { message }                                                    │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────┐                               │
│  │       Intent Classifier             │                               │
│  │                                     │                               │
│  │  - query: SQL questions             │                               │
│  │  - analyze: statistical analysis    │                               │
│  │  - visualize: chart requests        │                               │
│  │  - schema: table info requests      │                               │
│  │  - help: usage questions            │                               │
│  └──────────────┬──────────────────────┘                               │
│                 │                                                      │
│        ┌────────┴────────┬────────────────┐                            │
│        │                 │                │                            │
│        ▼                 ▼                ▼                            │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐                       │
│  │  NL2SQL   │    │  Schema   │    │   Help    │                       │
│  │  Agent    │    │   Info    │    │  Handler  │                       │
│  └─────┬─────┘    └───────────┘    └───────────┘                       │
│        │                                                               │
│        ▼                                                               │
│  ┌─────────────────────────────────────┐                               │
│  │        Query Execution              │                               │
│  │                                     │                               │
│  │  ┌─────────────────────────────┐    │                               │
│  │  │    Execute SQL Query        │    │                               │
│  │  └──────────┬──────────────────┘    │                               │
│  │             │                       │                               │
│  │       (success?)                    │                               │
│  │        ┌────┴────┐                  │                               │
│  │        │         │                  │                               │
│  │       yes        no                 │                               │
│  │        │         │                  │                               │
│  │        │    ┌────▼────┐             │                               │
│  │        │    │ Analyze │             │                               │
│  │        │    │  Error  │             │                               │
│  │        │    └────┬────┘             │                               │
│  │        │         │                  │                               │
│  │        │    ┌────▼────┐             │                               │
│  │        │    │  Fix &  │◄── (retry   │                               │
│  │        │    │  Retry  │    up to 5x)│                               │
│  │        │    └─────────┘             │                               │
│  └────────┼────────────────────────────┘                               │
│           │                                                            │
│           ▼                                                            │
│  ┌─────────────────────────────────────┐                               │
│  │       Data Analyst Agent            │                               │
│  │                                     │                               │
│  │  - Statistical analysis             │                               │
│  │  - Python code execution            │                               │
│  │  - Chart generation (matplotlib)    │                               │
│  └──────────────┬──────────────────────┘                               │
│                 │                                                      │
│                 ▼                                                      │
│  Output: { summary, data_table, sql_query, images }                    │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- DigitalOcean account
- PostgreSQL or MySQL database (DigitalOcean Managed Database recommended)

### Getting API Keys

1. **DigitalOcean API Token**:
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token with read/write access

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key

## Setup

### 1. Create Virtual Environment

```bash
cd DataScience
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Database

Use the included setup script to create a DigitalOcean Managed Database with sample data:

```bash
export DIGITALOCEAN_API_TOKEN=your_token

# Create PostgreSQL database
python scripts/setup_database.py --db-type postgres --region nyc1

# Or create MySQL database
python scripts/setup_database.py --db-type mysql --region nyc1
```

The script will:
- Create a managed database cluster
- Create a readonly user for the agent
- Load sample airline data (flights, airports, customers)
- Output connection details to `.env.database`

### 4. Configure Environment

```bash
cp .env.example .env
```

Copy the values from `.env.database` to your `.env`:

```
DIGITALOCEAN_INFERENCE_KEY=your_inference_key
DB_TYPE=postgres
DB_HOST=your-db-host.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=flights_db
DB_USER=readonly_agent
DB_PASSWORD=your_readonly_password
DB_SSL_MODE=require
```

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

**Simple query:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "message": "How many flights were delayed last month?"
    }'
```

**With visualization:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "message": "Create a bar chart showing flight delays by day of week"
    }'
```

**Schema information:**

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "message": "What tables are in the database?"
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-data-science-agent
```

### 2. Deploy

```bash
gradient agent deploy
```

### 3. Invoke Deployed Agent

```bash
curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
    --header 'Content-Type: application/json' \
    --header 'Authorization: Bearer <DIGITALOCEAN_API_TOKEN>' \
    --data '{
        "message": "Show me the top 10 routes by revenue"
    }'
```

## Sample Input/Output

### Input

```json
{
    "message": "What are the busiest airports by flight count?"
}
```

### Output

```json
{
    "success": true,
    "summary": "The busiest airports by flight count are LAX (Los Angeles) with 1,247 flights, followed by JFK (New York) with 1,189 flights, and ORD (Chicago O'Hare) with 1,156 flights.",
    "sql_query": "SELECT a.iata_code, a.name, COUNT(f.id) as flight_count FROM airports a JOIN flights f ON a.id = f.departure_airport_id GROUP BY a.id ORDER BY flight_count DESC LIMIT 10",
    "data_table": "| IATA | Airport Name | Flight Count |\n|------|--------------|-------------|\n| LAX | Los Angeles International | 1247 |\n| JFK | John F Kennedy International | 1189 |\n| ORD | Chicago O'Hare | 1156 |",
    "row_count": 10
}
```

### Input with Visualization

```json
{
    "message": "Create a chart showing average ticket prices by month"
}
```

### Output

```json
{
    "success": true,
    "summary": "Ticket prices show seasonal variation, with peaks in June-July and December.",
    "sql_query": "SELECT DATE_TRUNC('month', purchase_date) as month, AVG(price) as avg_price FROM tickets GROUP BY month ORDER BY month",
    "images": [
        {
            "path": "outputs/ticket_prices_by_month.png",
            "base64": "iVBORw0KGgoAAAANSUhEUgAAA..."
        }
    ]
}
```

## Project Structure

```
DataScience/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── agents/
│   ├── __init__.py
│   ├── nl2sql.py          # NL to SQL conversion with retry logic
│   └── data_analyst.py    # Data analysis and visualization
├── tools/
│   ├── __init__.py
│   └── database.py        # Database connection and schema
├── scripts/
│   └── setup_database.py  # DigitalOcean DB provisioning
├── data/
│   ├── schema.sql         # Database schema
│   └── sample_data.sql    # Sample airline data
├── outputs/                # Generated visualizations
├── main.py                 # LangGraph workflow
├── requirements.txt
├── .env.example
└── README.md
```

## Query Retry Configuration

The agent automatically retries failed queries with intelligent error correction:

```bash
# Default: 5 retries
curl -d '{"message": "Show revenue by customer segment"}'

# Custom retry count
curl -d '{"message": "Show revenue by customer segment", "max_query_retries": 3}'

# Disable retries
curl -d '{"message": "List all flights", "max_query_retries": 0}'
```

## Sample Database Schema

The setup script creates these tables with airline data:

| Table | Description |
|-------|-------------|
| `airports` | Airport codes, names, locations |
| `aircraft` | Fleet information, capacity |
| `customers` | Customer profiles, loyalty tiers |
| `flights` | Schedules, actual times, delays |
| `tickets` | Bookings, pricing, seat assignments |
| `flight_history` | Historical data for analytics |
| `ticket_sales_history` | Sales patterns, booking lead times |

## Customization

### Connecting to Your Database

Update `.env` with your database credentials:

```
DB_TYPE=postgres  # or mysql
DB_HOST=your-database-host
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_readonly_user
DB_PASSWORD=your_password
DB_SSL_MODE=require
```

### Adding Analysis Functions

Extend `agents/data_analyst.py`:

```python
def analyze_trends(data: pd.DataFrame) -> dict:
    """Custom trend analysis."""
    # Add moving averages
    data['ma_7'] = data['value'].rolling(7).mean()

    # Detect anomalies
    anomalies = detect_anomalies(data)

    return {
        "trends": data.to_dict(),
        "anomalies": anomalies
    }
```

### Customizing Visualization Styles

Edit `agents/data_analyst.py`:

```python
import seaborn as sns

# Set custom theme
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 12

# Custom color palette
colors = ['#0077B6', '#00B4D8', '#90E0EF', '#CAF0F8']
```

### Adding New Intent Types

Extend the intent classifier in `main.py`:

```python
INTENTS = {
    "query": "SQL database query",
    "analyze": "Statistical analysis",
    "visualize": "Chart generation",
    "schema": "Schema information",
    "help": "Usage help",
    # Add new intent
    "predict": "Predictive analytics"
}

# Add handler
def handle_predict(state):
    # ML prediction logic
    pass
```

## Security

The agent uses readonly database credentials by design:

- **Allowed**: SELECT queries only
- **Blocked**: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, GRANT

Additional safeguards:
- SQL keyword validation before execution
- Query timeout limits
- Sandboxed Python code execution for analysis

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check DB host, port, and firewall rules |
| Permission denied | Verify readonly user has SELECT permissions |
| Query keeps failing | Check the error in response, may be schema mismatch |
| No visualizations | Ensure `matplotlib` and `seaborn` are installed |
| SSL errors | Set `DB_SSL_MODE=require` for DigitalOcean DBs |

## Resources

- [DigitalOcean Managed Databases](https://docs.digitalocean.com/products/databases/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
