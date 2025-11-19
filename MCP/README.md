# ADK Agents that use Tools via MCP

This example demonstrates an ADK agent that connects to tools exposed via MCP servers. Two of the common challenges that LLMs face are their inability to know about events that transpired after their cutoff dates, and being unable to perform complex mathematical calculations with high levels of accuracy. 

This example agent enhances an LLM with the ability to both search the web, and use a calculator inorder to overcome those limitations. The example `main.py` creates a `MultiServerMCPClient` with two tool endpoints:

- `search` — the [Tavily MCP server](https://docs.tavily.com/documentation/mcp), which is a cloud-hosted remote MCP server that enables LLMs to search the web
- `calculator` — a locally running MCP tool invoked with a `python -m mcp_server_calculator` command

The runtime builds a LangGraph `StateGraph` where the model is bound to the tools discovered from the MCP client and will call them when appropriate. The agent is powered by DigitalOcean Gradient AI's serverless inference capabilties. 


## Quickstart 

1. Create and activate a virtual environment.
2. Install dependencies:

    pip install -r Templates/MCP/requirements.txt

3. Set the required enviornment variables in the .env file (`TAVILY_API_KEY` and `DIGITALOCEAN_INFERENCE_KEY`). You can obtain a Tavily API key for free at [this link](https://app.tavily.com/home). 

4. Set your DIGITALOCEAN_API_TOKEN via 

    '''
    export DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On MacOS/Linux
    set DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On Windows
    '''

5. Run your agent locally via

    `gradient agent run`

    You can invoke it with
    ```
    curl --location 'http://localhost:8080/run' \
        --header 'Content-Type: application/json' \
        --data '{
            "prompt" : {
                "messages" : "What is sqrt(5) + sqrt(7) times the age of the current pope?"
            }
        }'
    ```

6. Change the name of the agent if you need to in `gradient/agent.yaml` and then deploy with 

    ```
    gradient agent deploy
    ```

    You can the invoke the agent via the same curl command, just using your deployed agent's URL instead
    
    ```
    curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
        --header 'Content-Type: application/json' \
        --data '{
            "prompt" : {
                "messages" : "What is sqrt(5) + sqrt(7) times the age of the current pope?"
            }
        }'
    ```
