# Streaming Agents and using Python Functions as Tools

This example demonstrates an ADK agent that streams responses and uses a tool that is a Python function. Using Langgraph's `tool` decorator, we can construct an agent that can execute python functions as a tool. In this example, we use the Tavily search libary to enable our agent to search the web.
The runtime builds a LangGraph `StateGraph` where the first node decides if tools need to be used. If so, the agent queries the tools and then passes along the results from the tool to a final answer node. If a tool is not required, the answer node responds directly.
```
        +-----------+       
        | __start__ |       
        +-----------+       
              *             
              *             
              *             
   +---------------------+  
   | decision_model_call |  
   +---------------------+  
         ..        ..       
       ..            .      
      .               ..    
+-------+               .   
| tools |             ..    
+-------+            .      
         **        ..       
           **    ..         
             *  .           
    +-------------------+   
    | answer_model_call |   
    +-------------------+   
              *             
              *             
              *             
         +---------+        
         | __end__ |        
         +---------+   
```

Additionally, this agent yields streaming outputs instead of providing an entire response. Enabling streaming responses from your agent can help improve the user experience by allowing users of the agent to start getting a response quickly without waiting for the entire response to complete. 


## Quickstart 

1. Create and activate a virtual environment.
2. Install dependencies:

    pip install -r Templates/ToolCalling/requirements.txt

3. Set the required enviornment variables in the .env file (`TAVILY_API_KEY` and `DIGITALOCEAN_INFERENCE_KEY`). You can obtain a Tavily API key for free at [this link](https://app.tavily.com/home). 

4. Set your DIGITALOCEAN_API_TOKEN via 

    ```
    export DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On MacOS/Linux

    set DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On Windows
    ```

5. Run your agent locally via

    `gradient agent run`

    Since this agent produces streaming responses, you can invoke the agent via code to see the streaming

    ```python
    import requests
    import json

    def stream_endpoint(url: str, body : dict, headers: dict = {}, chunk_size: int = 1024):
        payload = json.dumps(body)
        with requests.post(url, data = payload, headers=headers, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:  # filter keep-alive chunks
                    yield chunk

    if __name__ == "__main__":
        body = {
            "prompt" : {
                "messages" : "Who were winners and runners up of the women's 2025 cricket world cup?"
            }
        }

        buffer = ""
        for chunk in stream_endpoint("http://localhost:8080/run", body=body):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
            response = json.loads(line)
            print(response["response"], end="", flush=True)

    ```

6. Change the name of the agent if you need to in `gradient/agent.yaml` and then deploy with 

    ```
    gradient agent deploy
    ```

    You can the invoke the agent via the same script, just using your deployed agent's URL instead. Make sure you include your API key for authorization

    ```python
    import requests
    import json

    def stream_endpoint(url: str, body : dict, headers: dict = {}, chunk_size: int = 1024):
        payload = json.dumps(body)
        with requests.post(url, data = payload, headers=headers, stream=True) as resp:
            resp.raise_for_status()
            for chunk in resp.iter_content(chunk_size=chunk_size):
                if chunk:  # filter keep-alive chunks
                    yield chunk

    if __name__ == "__main__":
        body = {
            "prompt" : {
                "messages" : "Who were winners and runners up of the women's 2025 cricket world cup?"
            }
        }

        headers = {'Authorization': 'Bearer <YOUR DIGITALOCEAN API KEY>'}

        buffer = ""
        for chunk in stream_endpoint('https://agents.do-ai.run/<DEPLOYED_AGENT_ID>/main/run', body=body, headers=headers):
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
            response = json.loads(line)
            print(response["response"], end="", flush=True)
    ```
