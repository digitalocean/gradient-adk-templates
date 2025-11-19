# RAG (Retrieval-Augmented Generation) Template

This template demonstrates a multi-agent RAG Question Answering agent built with LangGraph and LangChain, that can easily be deployed to DigitalOcean's Gradient AI platform. It uses an in-memory retriever (over local PDFs) as a tool and has dedicated sub agents to rewrite queries and generate answers. This agent graph is defined in `main.py` and the ADK entrypoint is exposed via the `@entrypoint` decorator.


Key features
- Multi-node LangGraph workflow that decides whether to retrieve documents or respond directly
- In-memory retriever created via `tools.doc_retriever.create_retriever` (points at `./pdfs` by default)
- Dedicated agents to rewrite the query for better retrieval results and answer generation 
- All agents use DigitalOcean Gradient AI's serverless inference capabilities for the underlying LLMs.


## Agent Graph
```

                                  +-----------+                         
                                  | __start__ |                         
                                  +-----------+                         
                                        *                               
                                        *                               
                                        *                               
                          +---------------------------+                 
                          | generate_query_or_respond |                 
                          +---------------------------+                 
                       .....            *            .....              
                  .....                 *                 .....         
               ...                      *                      .....    
    +----------+                        *                           ... 
    | retrieve |..                      *                             . 
    +----------+  .....                 *                             . 
          .            .....            *                             . 
          .                 .....       *                             . 
          .                      ...    *                             . 
+-----------------+           +------------------+                  ... 
| generate_answer |           | rewrite_question |             .....    
+-----------------+****       +------------------+        .....         
                       *****                         .....              
                            *****               .....                   
                                 ***         ...                        
                                  +---------+                           
                                  | __end__ |                           
                                  +---------+                         
```

## Quickstart 

1. Create and activate a virtual environment.
2. Install dependencies:

    `pip install -r requirements.txt`

3. Set the required enviornment variables in the .env file (`OPENAI_API_KEY` and `DIGITALOCEAN_INFERENCE_KEY`). Note that both an OpenAI API key and a serverless inference key are required, because the Gradient AI platform does not yet support serverless embeddings. The OpenAI key is used to construct embeddings for the data that is indexed. 

4. Copy over all the PDFs you want to your agent to index into the `./pdfs` folder. The template provides some fact sheets about the Hubble Space Telescope by default.

5. Set your DIGITALOCEAN_API_TOKEN via 

    ```
    export DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On MacOS/Linux
    set DIGITALOCEAN_API_TOKEN=<Your DigitalOcean API Token> # On Windows
    ```

5. Run your agent locally via

    `gradient agent run`

    You can invoke it with
    ```
    curl --location 'http://localhost:8080/run' \
        --header 'Content-Type: application/json' \
        --data '{
            "prompt" : {
                    "messages": [
                        {
                            "role": "user",
                            "content": "What is the difference between the STIS and the COS?"
                        }
                    ]
                }
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
            "prompt" : {
                    "messages": [
                        {
                            "role": "user",
                            "content": "What is the difference between the STIS and the COS?"
                        }
                    ]
                }
        }'
    ```

## Notes
- The retriever uses a local PDF folder by default. If you need a persistent vector store or large-scale index, replace the in-memory retriever in `tools/doc_retriever.py` with a supported vector DB.
- Make sure you set BOTH `OPENAI_API_KEY` and `DIGITALOCEAN_INFERENCE_KEY` environment variables.
- If you need to upload a very large number of documents, consider using a dedicated vector DB that is separately deployed. You may run into memory constraints otherwise.
