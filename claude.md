# Claude Code Context: WeChat Group Automation with LangGraph

## Project Overview

This is a **multi-modal AI agent automation system** built with LangGraph that monitors WeChat work group messages, understands text and image content, tracks task states, and automatically generates reports and updates spreadsheets.

**Key Technologies:**
- **LangGraph 0.0.50+**: Workflow orchestration with stateful agents
- **LangChain**: AI tool integration
- **Ollama**: Local AI models (Qwen3-VL for vision, Qwen3-Embedding for embeddings)
- **FastAPI**: REST API orchestration layer
- **ChromaDB**: Vector database for knowledge base
- **Redis**: State storage and caching
- **Docker**: Containerized WeChat sandbox environment

## Architecture Pattern

The system uses a **hybrid architecture** combining centralized workflow with peripheral services:

```
WeChat Sandbox (Docker) → MonitorAgent → Orchestrator (FastAPI) → LangGraph Workflow
                                                      ↓
                                              [Multimodal → StateTracker → Document]
                                                      ↓
                                              AI Services (Ollama + ChromaDB)
```

### Core Components

1. **MonitorAgent** (`agents/monitor_agent.py`)
   - Manages WeChat Docker container lifecycle
   - Consumes message stream via Server-Sent Events
   - Triggers workflow execution

2. **Orchestrator** (`services/orchestrator/main.py`)
   - FastAPI service on port 8000
   - Manages LangGraph workflow execution
   - Handles state and results

3. **LangGraph Workflow** (`core/workflows/`)
   - **Monitor Node**: Message validation and routing
   - **Multimodal Node**: Text/image understanding with RAG
   - **StateTracker Node**: Task state management
   - **Document Node**: Excel/Word generation

## Important File Locations

### Configuration
- `config/settings.yaml` - Main configuration
- `.env` - Environment variables (not in git)
- `docker-compose.yml` - Service orchestration

### Core Framework
- `core/schemas.py` - Data models (RawMessage, MessageType, etc.)
- `core/state.py` - LangGraph state definition (AgentState)
- `core/workflows/main_workflow.py` - Main workflow graph
- `core/workflows/nodes/` - Individual node implementations

### Tools
- `tools/excel_tool.py` - Excel update operations
- `tools/word_tool.py` - Word report generation

### Knowledge Base
- `knowledge_base/vector_store.py` - ChromaDB wrapper
- `knowledge_base/embeddings.py` - Ollama embedding integration

## Development Guidelines

### Working with LangGraph Workflows

**Adding a new node:**

1. Create node in `core/workflows/nodes/new_node.py`:
```python
from typing import TypedDict
from ..state import AgentState

def process(state: AgentState) -> AgentState:
    """Node processing logic"""
    state["context"]["result"] = "processed"
    return state
```

2. Register in `core/workflows/main_workflow.py`:
```python
from .nodes.new_node import process

workflow.add_node("new_node", process)
workflow.add_edge("multimodal", "new_node")
```

### State Management

The `AgentState` is a `TypedDict` that flows through all nodes:
```python
class AgentState(TypedDict):
    raw_message: RawMessage          # Input message
    multimodal_analysis: Optional[dict]  # Analysis results
    task_status: Optional[str]       # Task state
    document_updates: list            # Update history
    messages: list                    # Message log
    context: dict                     # Additional context
```

**Important:** Nodes must return the updated state, even if unchanged.

### Configuration Access

Use the Pydantic Settings pattern:
```python
from config.settings import settings

# Access nested config
ollama_url = settings.ai.ollama.base_url
vision_model = settings.ai.ollama.vision_model
```

Environment variables override YAML settings:
- Use double underscores for nesting: `AI__OLLAMA__BASE_URL`

### Working with Ollama Models

**Vision model (Qwen3-VL):**
```python
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage

vision_model = ChatOllama(
    base_url=settings.ai.ollama.base_url,
    model="qwen3-vl-8b:latest"
)

# For images
message = HumanMessage(content=[
    {"type": "text", "text": "Describe this image"},
    {"type": "image_url", "url": "file://path/to/image.jpg"}
])
response = vision_model.invoke([message])
```

**Embeddings:**
```python
from langchain_community.embeddings import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    base_url=settings.ai.ollama.base_url,
    model="qwen3-embedding-4b"
)
vector = embeddings.embed_query("text to embed")
```

### Document Generation

**Excel updates:**
```python
from tools.excel_tool import ExcelTool

tool = ExcelTool(config=settings.ai.excel)
tool.update_row(
    sheet_name="Sheet1",
    row_index=5,
    data={"status": "完成", "date": "2026-01-09"}
)
```

**Word reports:**
```python
from tools.word_tool import WordTool

tool = WordTool(config=settings.ai.word)
tool.generate_from_template(
    template_path="templates/daily_report.j2",
    output_path="output/report.docx",
    context={"title": "日报", "items": [...]}
)
```

## Common Development Tasks

### Adding a New Message Type

1. Update enum in `core/schemas.py`:
```python
class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"  # New type
```

2. Add handling logic in `multimodal_node.py`

3. Update validation in `monitor_node.py`

### Testing Workflow Execution

```bash
# Start services
docker-compose up -d redis ollama

# Pull models
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b

# Start orchestrator
uvicorn services.orchestrator.main:app --reload

# Trigger workflow
curl -X POST http://localhost:8000/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "张三",
    "content": "请生成本周工作周报",
    "message_type": "text",
    "group_id": "group_123"
  }'
```

### Debugging LangGraph Workflows

**Enable workflow visualization:**
```python
from core.workflows.main_workflow import create_workflow

workflow = create_workflow()
# Print the graph structure
print(workflow.get_graph().print_ascii())
```

**Inspect state at each node:**
```python
def debug_node(state: AgentState) -> AgentState:
    print(f"Current state: {state}")
    # Node logic
    return state
```

### Working with RAG (Knowledge Base)

```python
from knowledge_base.vector_store import VectorStoreManager

vector_store = VectorStoreManager(config=settings.vector_store)

# Add documents
vector_store.add_documents([
    {"text": "Knowledge content", "metadata": {"source": "doc1"}}
])

# Search
results = vector_store.similarity_search(
    query="用户的问题",
    k=3
)
```

## Code Style Guidelines

1. **Type Hints**: All functions must have type hints
2. **Docstrings**: Use Google-style docstrings
3. **Logging**: Use `structlog` for structured logging
4. **Error Handling**: Use custom exceptions in `core/exceptions.py`
5. **Async**: Use `async/await` for I/O operations

```python
import structlog

logger = structlog.get_logger()

async def process_message(message: RawMessage) -> dict:
    """Process a WeChat message.

    Args:
        message: The raw message from WeChat

    Returns:
        Processing results dictionary

    Raises:
        MessageValidationError: If message format is invalid
    """
    logger.info("Processing message", sender=message.sender)
    # Implementation
    return {"status": "success"}
```

## Testing Strategy

- **Unit tests**: `tests/unit/` - Test individual components
- **Integration tests**: `tests/integration/` - Test service interactions
- **Workflow tests**: `tests/workflows/` - Test LangGraph workflows

```bash
# Run tests
pytest

# With coverage
pytest --cov=core --cov-report=html
```

## Docker Services

### WeChat Sandbox
- **Ports**: 5800 (noVNC), 5900 (VNC), 6789 (producer service)
- **Usage**: Access WeChat via browser at http://localhost:5800
- **Management**: `docker start/stop wechat-sandbox`

### Ollama
- **Port**: 11434
- **API**: http://localhost:11434/api/tags
- **Models**: qwen3-vl-8b, qwen3-embedding-4b, qwen3-72b

### Redis
- **Port**: 6379
- **Usage**: Caching and distributed locks

## Performance Considerations

1. **Connection Pooling**: Reuse HTTP clients for Ollama and API calls
2. **Async Operations**: Use `asyncio` for concurrent message processing
3. **Redis Caching**: Cache frequent queries (embeddings, RAG results)
4. **Batch Processing**: Group multiple messages for batch analysis

## Security Notes

1. **Never commit** `.env` file (already in `.gitignore`)
2. **API Keys**: Use environment variables for all secrets
3. **Input Validation**: Validate all user inputs in nodes
4. **Docker Isolation**: Use Docker networks for service isolation

## Troubleshooting

**Container won't start:**
```bash
docker ps -a                    # Check container status
docker logs wechat-sandbox       # View logs
docker inspect wechat-sandbox   # Check configuration
```

**Workflow execution fails:**
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check Redis
redis-cli ping

# Check orchestrator logs
# (View terminal where uvicorn is running)
```

**Model loading errors:**
```bash
# Verify models are pulled
docker exec -it ollama ollama list

# Re-pull if needed
docker exec -it ollama ollama pull qwen3-vl-8b
```

## Key Dependencies

- `langgraph>=0.0.50` - Workflow orchestration
- `langchain>=0.1.0` - AI framework
- `fastapi>=0.104` - API framework
- `pydantic>=2.0` - Data validation
- `pydantic-settings` - Configuration management
- `structlog` - Structured logging
- `docker` - Container management
- `redis` - Caching
- `chromadb` - Vector database
- `openpyxl` - Excel operations
- `python-docx` - Word operations

## Resources

- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Ollama Docs**: https://ollama.ai/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Project README**: See README.md for setup instructions
- **Agent Architecture**: See agent.md for detailed architecture

## Quick Reference

### Start all services:
```bash
docker-compose up -d
docker exec -it ollama ollama pull qwen3-vl-8b
docker exec -it ollama ollama pull qwen3-embedding-4b
python scripts/init_knowledge_base.py
uvicorn services.orchestrator.main:app --reload
```

### MonitorAgent control:
```python
from agents.monitor_agent import MonitorAgent

agent = MonitorAgent()
await agent.start()  # Start monitoring
agent.stop()         # Stop monitoring
```

### Trigger workflow manually:
```bash
curl -X POST http://localhost:8000/workflow/trigger \
  -H "Content-Type: application/json" \
  -d '{"sender": "test", "content": "test message", "message_type": "text"}'
```

### Check workflow status:
```bash
curl http://localhost:8000/workflow/status
```

## Notes for Claude

When working with this codebase:

1. **Always read existing code before modifying** - This is a complex system with interdependent components
2. **Understand the data flow** - Messages flow through nodes, updating state at each step
3. **Test workflow changes** - Use the API endpoint to test before committing
4. **Check configuration** - Many behaviors are configured in `settings.yaml` or `.env`
5. **Monitor logs** - Use structlog output to debug issues
6. **Respect async patterns** - Most I/O operations are asynchronous

The project uses **Chinese comments** in some files and supports Chinese text processing (WeChat messages). The AI models (Qwen3) are Chinese-optimized models.
