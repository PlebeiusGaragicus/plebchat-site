# Setup

1. Install dependencies:

```bash
cd agent
pip install -e . "langgraph-cli[inmem]"
```

2. Configure environment:

```bash
cp .env.example .env
# Edit .env with your LLM endpoint configuration
```

3. Run the LangGraph server:

```bash
langgraph dev --no-browser
```

The server will be available at `http://localhost:2024`