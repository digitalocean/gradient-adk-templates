# ADK Agents that use Tools via LangGraph create_agent

This example demonstrates an ADK agent that connects to a single tool that searches the Web via DuckDuckGo.

This example leverages the create_agent function from LangChain to call LLMs and tools. These LLM and tool calls input and outputs will get logged automatically in the Gradient AI traces store after your agent is deployed via `gradient agent deploy`.


## Quickstart 

1. Create and activate a virtual environment.
2. Install dependencies:

    pip install -r requirements.txt

3. Set the required enviornment variables in the .env file (`DIGITALOCEAN_API_TOKEN` and `DIGITALOCEAN_INFERENCE_KEY`). You can obtain both of these tokens via the DigitalOcean UI.

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
        "prompt" : "Who was the 2025 MLB baseball MVP?"
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
            "prompt" : "Who was the 2025 MLB baseball MVP?"
        }'
    ```
