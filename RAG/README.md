# RAG - Document Question Answering

A multi-agent Retrieval-Augmented Generation (RAG) system for question answering over PDF documents. Built with LangGraph and LangChain, deployable on the DigitalOcean Gradient AI Platform.

## Use Case

Build an AI assistant that answers questions using your own documents as the knowledge source. This template demonstrates document retrieval, query optimization, and answer generation with citations.

**When to use this template:**
- You need to answer questions from a document collection
- You want to build a knowledge base chatbot
- You need query rewriting for better retrieval

## Key Concepts

**Retrieval-Augmented Generation (RAG)** enhances LLM responses by fetching relevant documents before answering. Instead of relying solely on training data, the agent searches a vector index of your documents, retrieves the most relevant passages, and uses them as context for generating accurate, grounded responses with citations.

**Query rewriting** improves retrieval quality when initial results are poor. If the retrieved documents don't answer the question well, the agent reformulates the query with different terms or more specific phrasing, then retries the search. This multi-step approach handles ambiguous or complex questions more effectively than single-pass retrieval.

## Architecture

```
                              ┌───────────┐
                              │   Start   │
                              └─────┬─────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │  generate_query_or_respond   │
                     │                              │
                     │  LLM decides: retrieve docs  │
                     │  or answer directly?         │
                     └──────────────┬───────────────┘
                            ┌───────┴───────┐
                            │               │
                    (needs docs)      (can answer)
                            │               │
                            ▼               │
                     ┌──────────────┐       │
                     │   retrieve   │       │
                     │              │       │
                     │ Vector search│◄──────────────────────┐
                     │ for relevant │       │               │
                     │ documents    │       │               │
                     └──────┬───────┘       │               │
                            │               │               │
                            ▼               │               │
                     ┌──────────────┐       │               │
                     │    grade     │       │               │
                     │              │       │               │
                     │ LLM evaluates│       │               │
                     │ if docs are  │       │               │
                     │ relevant to  │       │               │
                     │ the question │       │               │
                     └──────┬───────┘       │               │
                            │               │               │
              ┌─────────────┴─────────┐     │               │
              │                       │     │               │
        (relevant)              (not relevant)              │
              │                       │                     │
              │                       ▼                     │
              │          ┌─────────────────┐                │
              │          │ rewrite_question│                │
              │          │                 │                │
              │          │ LLM reformulates│                │
              │          │ query for better│────────────────┘
              │          │ retrieval       │  (retry with
              │          └─────────────────┘   new query)
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
                ┌─────────────────┐
                │ generate_answer │
                │                 │
                │ LLM writes      │
                │ response with   │
                │ citations       │
                └────────┬────────┘
                         │
                         ▼
                  ┌───────────┐
                  │    End    │
                  └───────────┘
```

The workflow uses **LLMs at each decision point**:
1. **generate_query_or_respond**: LLM decides if retrieval is needed or if it can answer directly
2. **retrieve**: Vector search fetches potentially relevant documents
3. **grade**: LLM evaluates whether retrieved documents actually answer the question
4. **rewrite_question**: If documents aren't relevant, LLM reformulates the query and loops back to retrieve
5. **generate_answer**: LLM synthesizes the final response with citations from relevant documents

## Prerequisites

- Python 3.10+
- DigitalOcean account
- OpenAI API key (for embeddings)
- PDF documents to index

### Getting API Keys

1. **DigitalOcean API Token**:
   - Go to [API Settings](https://cloud.digitalocean.com/account/api/tokens)
   - Generate a new token with read/write access

2. **DigitalOcean Inference Key**:
   - Go to [GenAI Settings](https://cloud.digitalocean.com/gen-ai)
   - Create or copy your inference key

3. **OpenAI API Key** (for embeddings):
   - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new API key

> Note: OpenAI is required because DigitalOcean GenAI Serverless Inference does not yet support embedding models. The LLM inference still uses DigitalOcean.

## Setup

### 1. Create Virtual Environment

```bash
cd RAG
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
DIGITALOCEAN_INFERENCE_KEY=your_inference_key
OPENAI_API_KEY=your_openai_key
```

### 4. Add Your Documents

Copy PDF files to the `pdfs/` folder:

```bash
cp /path/to/your/documents/*.pdf ./pdfs/
```

The template includes sample Hubble Space Telescope fact sheets by default.

## Running Locally

### Start the Agent

```bash
export DIGITALOCEAN_API_TOKEN=your_token
gradient agent run
```

### Test with curl

```bash
curl --location 'http://localhost:8080/run' \
    --header 'Content-Type: application/json' \
    --data '{
        "prompt": {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the difference between the STIS and the COS?"
                }
            ]
        }
    }'
```

## Deployment

### 1. Configure Agent Name

Edit `.gradient/agent.yml`:

```yaml
agent_name: my-rag-agent
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
        "prompt": {
            "messages": [
                {
                    "role": "user",
                    "content": "What is the difference between the STIS and the COS?"
                }
            ]
        }
    }'
```

## Sample Input/Output

### Input

```json
{
    "prompt": {
        "messages": [
            {
                "role": "user",
                "content": "What instruments does Hubble use to observe ultraviolet light?"
            }
        ]
    }
}
```

### Output

```json
{
    "response": "Hubble uses two primary instruments for ultraviolet observations:\n\n1. **Cosmic Origins Spectrograph (COS)**: Installed in 2009, COS is optimized for observing faint ultraviolet emissions from distant sources like quasars and intergalactic gas.\n\n2. **Space Telescope Imaging Spectrograph (STIS)**: A versatile instrument that can observe in ultraviolet, visible, and near-infrared wavelengths, often used for studying planetary atmospheres and stellar winds.\n\nBoth instruments take advantage of Hubble's position above Earth's atmosphere, which blocks most ultraviolet light from reaching ground-based telescopes.",
    "sources": [
        "hubble_cos_factsheet.pdf",
        "hubble_stis_factsheet.pdf"
    ]
}
```

## Project Structure

```
RAG/
├── .gradient/
│   └── agent.yml          # Deployment configuration
├── agents/
│   ├── __init__.py
│   ├── grader.py          # Document relevance evaluation
│   ├── rewriter.py        # Query reformulation
│   └── answer_writer.py   # Response generation
├── tools/
│   ├── __init__.py
│   └── doc_retriever.py   # PDF loading and vector search
├── pdfs/                   # Your PDF documents
│   └── *.pdf
├── main.py                 # LangGraph workflow
├── prompts.py              # All agent prompts (edit this to customize!)
├── requirements.txt
├── .env.example
└── README.md
```

## Customization

### Customizing the Prompts

The easiest way to adapt this template is by editing **`prompts.py`**. This file contains all the prompts used by the RAG pipeline agents.

**Key prompts you can customize:**

| Variable | Purpose | Example Change |
|----------|---------|----------------|
| `GRADE_PROMPT` | Evaluates document relevance | Make stricter for high-precision retrieval |
| `REWRITE_PROMPT` | Reformulates failed queries | Add domain-specific synonyms |
| `GENERATE_PROMPT` | Creates the final answer | Change style (concise vs detailed) |

**Example: Detailed Technical Answers**

```python
# In prompts.py, change GENERATE_PROMPT to:
GENERATE_PROMPT = (
    "You are a technical documentation assistant. "
    "Use the following retrieved context to answer the question thoroughly. "
    "Provide step-by-step explanations when applicable. "
    "If the context doesn't contain enough information, say so and explain what's missing.\n"
    "Question: {question} \n"
    "Context: {context}"
)
```

**Example: Strict Document Grading**

```python
# For higher precision retrieval:
GRADE_PROMPT = (
    "You are a strict grader assessing relevance of a retrieved document to a user question. \n "
    "Here is the retrieved document: \n\n {context} \n\n"
    "Here is the user question: {question} \n"
    "The document must directly answer the question or contain key information needed. "
    "Tangentially related content should be graded as 'no'. \n"
    "Give a binary score 'yes' or 'no' score to indicate whether the document is relevant."
)
```

**Example: Citation-focused Answers**

```python
GENERATE_PROMPT = (
    "You are a research assistant that provides well-cited answers. "
    "Use the retrieved context to answer the question. "
    "Reference specific parts of the documents in your answer. "
    "If you don't have enough information, acknowledge the limitations.\n"
    "Question: {question} \n"
    "Context: {context}"
)
```

### Change the Documents

Sample documents are included in `/pdfs`. You can swap these documents out for your documents and have the agent answer questions on your data.


### Using a Different Vector Store

Replace the in-memory retriever in `tools/doc_retriever.py`:

```python
from langchain_community.vectorstores import Pinecone

def create_retriever():
    # Use Pinecone for persistent storage
    vectorstore = Pinecone.from_existing_index(
        index_name="my-index",
        embedding=OpenAIEmbeddings()
    )
    return vectorstore.as_retriever(search_kwargs={"k": 5})
```

### Changing the Embedding Model

Modify `tools/doc_retriever.py` to use a different embedding:

```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```

### Adjusting Retrieval Parameters

Change the number of documents retrieved:

```python
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 10}  # Retrieve 10 documents instead of default
)
```

### Adding Document Sources

Support additional file types by modifying the loader:

```python
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# Load both PDFs and text files
loader = DirectoryLoader(
    "./documents",
    glob="**/*.*",
    loader_cls=TextLoader
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No documents found" | Check that PDFs exist in the `pdfs/` folder |
| Embedding errors | Verify your `OPENAI_API_KEY` is set correctly |
| Poor retrieval results | Try adding more context to your question |
| Memory issues | Reduce the number/size of PDFs or use an external vector DB |

## Limitations

- **In-memory storage**: Document index is rebuilt on each restart. For production, use a persistent vector store.
- **PDF only**: The default loader only supports PDF files.
- **Embedding costs**: Each document is embedded using OpenAI, which incurs API costs.

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain RAG Guide](https://python.langchain.com/docs/tutorials/rag/)
- [Gradient ADK Documentation](https://docs.digitalocean.com/products/gradient/adk/)
