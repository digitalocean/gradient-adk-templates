# Crew AI Trivia Generator Template

This template shows a small Crew AI application that spins up two agents (a researcher and a trivia generator) to find news articles on a given date and topic, then produce interesting trivia facts. It demonstrates how you can deploy agents built with any framework onto the DigitalOcean Gradient AI Platform.

The agent uses [Serper](https://serper.dev), which is a fast Google search API in order to retrieve news articles for a particular date. Even though the agent is built with Crew AI, it can run on the DigitalOcean Gradient AI platform seamlessly, and uses DigitalOcean Gradient AI serverless inference for the underlying Large Language Model. 

## Quickstart 

1. Create and activate a virtual environment.
2. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Set the required enviornment variables in the .env file (`SERPER_API_KEY` and `DIGITALOCEAN_INFERENCE_KEY`). You can obtain a Serper API key for free at [this link](https://serper.dev/api-keys). 

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
            "date" : "16th November 2025", 
            "topic" : "AI Laws and Regulations"
        }'
    ```

6. Change the name of the agent if you need to in `.gradient/agent.yaml` and then deploy with 

    ```
    gradient agent deploy
    ```

    You can the invoke the agent via the same curl command, just using your deployed agent's URL instead
    
    ```
    curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
        --header 'Content-Type: application/json' \
        --data '{
            "date" : "16th November 2025", 
            "topic" : "AI Laws and Regulations"
        }'
    ```

## Notes
- The agent can take a while to respond, with a typical request taking 30 to 40 seconds to complete. 
- Native viewing of logs and traces of Crew AI agents is not currently supported on the DigitalOcean GradientAI platform.
