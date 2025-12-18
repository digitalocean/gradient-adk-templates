# ADK Agents that uses a DigitalOcean Knowledge Base

This example demonstrates an ADK agent that connects to a DigitalOcean Knowledge Base and queries it when necessary.


## Quickstart 
1. Create a DigitalOcean Knowledge Base (https://cloud.digitalocean.com/gen-ai/knowledge-bases) with the data source URL of: https://www.digitalocean.com/products/gradient.
2. Retrieve the Knowledge Base UUID from your Knowledge Base's URL like so: https://cloud.digitalocean.com/gen-ai/knowledge-bases/<uuid here>
1. Create and activate a virtual environment.
2. Install dependencies:

    pip install -r requirements.txt

3. Set the required enviornment variables in the .env file (`DIGITALOCEAN_API_TOKEN`, `GRADIENT_MODEL_ACCESS_KEY`, and `DIGITALOCEAN_KB_ID`). You can obtain both of these tokens via the DigitalOcean UI.

4. Set your DIGITALOCEAN_API_TOKEN (with genai:* and project:read scopes) via 

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
                "messages" : "What is the Gradient AI Platform?"
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
               "messages" : "What is the Gradient AI Platform?"
            }
        }'
    ```
