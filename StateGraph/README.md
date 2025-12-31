# StateGraph ADK Agent

A joke generator with a spicy twist! 🌶️

An example Gradient ADK agent orchestrated with LangGraph that chains multiple LLM calls to craft, improve, and polish jokes. If the provided topic includes the word "spicy", the flow branches to add extra instructions so the joke comes back sassier.

## Features

- Graph-driven workflow using LangGraph's `StateGraph`.
- Single optional `topic` string input (defaults to "new years eve" when omitted).
- Optional boolean `spicy` flag to force (or suppress) the sassy path regardless of the topic wording.
- Punchline quality gate that short-circuits bland jokes.

## Node & Edge Flow

```
                 START
                   |
        +--------------------+
        |   generate_joke    |
        +--------------------+
           |              |
           |              +--> (Punchline FAIL) --> END
           |
     (Punchline PASS)
           |
        +-------------+
        | spice_router |
        +-------------+
          |         |
     (Spicy)   (NotSpicy)
          |         |
   +--------------+  |
   | add_spicy_note| |
   +--------------+  |
           \        /
            \      /
        +----------------+
        |  improve_joke  |
        +----------------+
                  |
        +----------------+
        |  polish_joke   |
        +----------------+
                  |
                 END
```

## Quickstart

1. Create and activate a virtual environment.
2. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Set the required enviornment variables in the .env file (`DIGITALOCEAN_API_TOKEN` and `GRADIENT_MODEL_ACCESS_KEY`). You can obtain both of these tokens via the DigitalOcean UI.

4. Set your DIGITALOCEAN_API_TOKEN via 

    '''
    export DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On MacOS/Linux
    set DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On Windows
    '''

5. Run the agent locally:

	```
	gradient agent run
	```

6. Invoke it via HTTP (both `topic` and `spicy` are optional; `topic` defaults to "new years eve" and `spicy` defaults to auto-detection):

  ```
  curl --location 'http://localhost:8080/run' \
      --header 'Content-Type: application/json' \
      --data '{
          "topic": "new years eve",
          "spicy": true
      }'
  ```

7. When ready, adjust `gradient/agent.yaml` as desired and deploy:

	```
	gradient agent deploy
	```

	After deployment you can hit the hosted endpoint:

	```
	curl --location 'https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run' \
		  --header 'Content-Type: application/json' \
		  --data '{
			"topic": "Tell me a networking joke"
		  }'
	```

## References

- [Building Effective Agents with LangGraph](https://www.youtube.com/watch?v=aHCDrAbH_go)