#!/usr/bin/env bash
# ============================================================================
# setup.sh — Deploy the sample serverless function and configure the agent
#
# Usage:
#   bash setup.sh
#
# Prerequisites:
#   - doctl CLI installed (https://docs.digitalocean.com/reference/doctl/how-to/install/)
#   - Authenticated with: doctl auth init
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMPLE_DIR="$SCRIPT_DIR/sample_function"
AGENT_DIR="$SCRIPT_DIR/../Agent"
ENV_FILE="$AGENT_DIR/.env"
PACKAGE="converter"
FUNCTION="convert"

echo "============================================"
echo "  DigitalOcean Function Calling Agent Setup"
echo "============================================"
echo ""

# ---- Check doctl ----
if ! command -v doctl &> /dev/null; then
    echo "ERROR: doctl CLI is not installed."
    echo ""
    echo "Install it from: https://docs.digitalocean.com/reference/doctl/how-to/install/"
    echo "Then run:  doctl auth init"
    exit 1
fi

# ---- Check serverless support ----
if ! doctl serverless status &> /dev/null 2>&1; then
    echo "Installing serverless support for doctl..."
    doctl serverless install
    echo ""
fi

# ---- Ensure connected to a namespace ----
if ! doctl serverless status 2>/dev/null | grep -q "Connected"; then
    echo "No serverless namespace connected."
    echo "Creating namespace 'function-calling-agent' in nyc1..."
    echo ""
    doctl serverless namespaces create --label "function-calling-agent" --region nyc1
    doctl serverless connect
    echo ""
fi

# ---- Deploy the sample function ----
echo "Deploying sample function ($PACKAGE/$FUNCTION)..."
echo ""
doctl serverless deploy "$SAMPLE_DIR"
echo ""

# ---- Get the function URL ----
FUNCTION_URL=$(doctl serverless functions get "$PACKAGE/$FUNCTION" --url)

echo "Function deployed successfully!"
echo "URL: $FUNCTION_URL"
echo ""

# ---- Write URL to .env ----
if [ -f "$ENV_FILE" ]; then
    if grep -q "^FUNCTION_URL=" "$ENV_FILE"; then
        sed -i "s|^FUNCTION_URL=.*|FUNCTION_URL=$FUNCTION_URL|" "$ENV_FILE"
    else
        echo "FUNCTION_URL=$FUNCTION_URL" >> "$ENV_FILE"
    fi
else
    cp "$AGENT_DIR/.env.example" "$ENV_FILE"
    sed -i "s|^FUNCTION_URL=.*|FUNCTION_URL=$FUNCTION_URL|" "$ENV_FILE"
fi

echo "FUNCTION_URL saved to Agent/.env"
echo ""

# ---- Quick test ----
echo "Testing the function..."
TEST_RESULT=$(curl -s -X POST "$FUNCTION_URL" \
    -H "Content-Type: application/json" \
    -d '{"value": 100, "from_unit": "celsius", "to_unit": "fahrenheit"}')
echo "  100°C -> °F = $TEST_RESULT"
echo ""

echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Set your credentials in Agent/.env:"
echo "       DIGITALOCEAN_API_TOKEN=your_token"
echo "       DIGITALOCEAN_INFERENCE_KEY=your_key"
echo ""
echo "  2. Run the agent locally:"
echo "       cd ../Agent"
echo "       gradient agent run"
echo ""
echo "  3. Try it out:"
echo "       curl http://localhost:8080/run \\"
echo "         -H 'Content-Type: application/json' \\"
echo "         -d '{\"prompt\": \"Convert 72 fahrenheit to celsius\"}'"
echo ""
