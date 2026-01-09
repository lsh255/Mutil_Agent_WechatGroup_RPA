# Claude Code Context - WeChat Multi-Agent Workflow System

> This document provides essential context for Claude Code to understand the system architecture, component responsibilities, and development standards.

## Project Overview

**Project Name**: Multimodal WeChat Group Automation Agent System

**Purpose**: A stateful multimodal AI agent system based on LangGraph that monitors WeChat workgroup messages, understands text+image content, tracks task status, automatically updates ledgers, and generates work reports.

**Core Value**:
- Automate WeChat group message processing, reducing manual intervention
- Multimodal understanding (text + images)
- Intelligent task status tracking and management
- Automated document generation (Excel, Word)
- Production-ready multi-instance deployment support

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              WeChat Sandbox Container (Docker)               │
│  ├── Linux WeChat Client                                     │
│  ├── Producer Service (http://localhost:8000)                │
│  │   ├── FastAPI Server                                      │
│  │   ├── Producer1 (Observer - Screen Monitor)              │
│  │   ├── Producer2 (Content Fetcher - Message Extraction)   │
│  │   ├── ChangeDetector (Change Detection)                   │
│  │   ├── MessageTypeClassifier (Message Classifier)          │
│  │   └── Redis Queue Manager                                 │
│  ├── noVNC Remote Desktop (http://localhost:6080)            │
│  └── Web UI Management Interface (http://localhost:8000/api/ui)│
└──────────────────────┬──────────────────────────────────────┘
                       │ SSE Message Stream / HTTP API
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              MonitorAgent (Monitoring Agent)                │
│  ├── Docker container lifecycle management                    │
│  ├── Server-Sent Events message consumption                  │
│  ├── Message parsing and preprocessing                      │
│  └── Workflow triggering                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP POST /workflow/trigger
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            Orchestrator (Workflow Orchestration Center)      │
│  ├── FastAPI Web Service (http://localhost:8000)           │
│  ├── LangGraph Workflow Engine                               │
│  ├── API request handling and response                        │
│  └── Health check and monitoring                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 LangGraph Workflow Engine                     │
│  ┌─────────┐    ┌──────────────┐    ┌─────────────┐         │
│  │ Monitor │ →  │  Multimodal  │ →  │ StateTracker │         │
│  │  Node   │    │     Node     │    │    Node     │         │
│  └─────────┘    └──────────────┘    └──────┬──────┘         │
│                                             │                 │
│                                   ┌─────────┴─────────┐       │
│                                   │                   │       │
│                           Task Complete? No         │ Yes    │
│                                   ↓                   ↓       │
│                                 END              ┌─────────┐  │
│                                                  │Document │  │
│                                                  │  Node   │  │
│                                                  └─────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   External Services & Infrastructure          │
│  ├── Redis (state cache, distributed locks, message queue)   │
│  ├── Ollama (local AI model service)                         │
│  │   ├── Qwen3-VL (visual understanding)                     │
│  │   └── Qwen3-Chat (dialogue generation)                    │
│  ├── SiliconFlow (cloud AI model service)                    │
│  │   └── Qwen3-Embedding (text embedding)                    │
│  ├── ChromaDB (vector database)                              │
│  └── Document Tools (Word/Excel generation)                  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Technology/Framework | Version | Purpose |
|---------------------|---------|---------|
| Python | 3.12+ | Main development language |
| LangGraph | 0.0.50+ | Workflow orchestration framework |
| LangChain | 0.1.0+ | AI tool integration framework |
| FastAPI | 0.104+ | Web API framework |
| OpenCV | 4.8+ | Image processing and computer vision |
| Ollama | latest | Local AI model service |
| SiliconFlow | - | Cloud AI model service (Embedding) |
| ChromaDB | latest | Vector database |
| Redis | 7.0+ | Cache, state storage, message queue |
| Docker | 20.0+ | Containerized deployment |
| noVNC | latest | Web remote desktop |
| Xvfb & Fluxbox | - | Virtual display and window manager |

## Core Components

### 1. WeChat Sandbox Container

**Path**: `services/wechat_sandbox/`

**Core Responsibilities**:
- Provide isolated Linux WeChat runtime environment
- Browser access via noVNC
- Screen monitoring and message capture
- Producer service API endpoints
- Web UI management interface
- Multi-instance deployment support

**Technical Architecture**:

```
┌─────────────────────────────────────────┐
│         Docker Container                │
│  ┌──────────────────────────────────┐  │
│  │   Linux WeChat Client           │  │
│  │   (Headless, running in Xvfb)   │  │
│  └────────────┬─────────────────────┘  │
│               │ Screen Capture          │
│  ┌────────────▼─────────────────────┐  │
│  │   Producer1 (Observer)          │  │
│  │   - ChangeDetector               │  │
│  │   - MessageTypeClassifier       │  │
│  │   - ROI Management               │  │
│  └────────────┬─────────────────────┘  │
│               │ New Message Detected   │
│  ┌────────────▼─────────────────────┐  │
│  │   Producer2 (Content Fetcher)    │  │
│  │   - Bubble Extraction            │  │
│  │   - Text/Image Parsing           │  │
│  │   - OCR Text Recognition         │  │
│  └────────────┬─────────────────────┘  │
│               │ Structured Message     │
│  ┌────────────▼─────────────────────┐  │
│  │   Redis Queue Manager            │  │
│  │   - Redis Streams                │  │
│  │   - Message Persistence          │  │
│  │   - Multi-consumer Support       │  │
│  └────────────┬─────────────────────┘  │
│               │ SSE / HTTP             │
│  ┌────────────▼─────────────────────┐  │
│  │   FastAPI Server                 │  │
│  │   - REST API Endpoints           │  │
│  │   - SSE Message Stream           │  │
│  │   - Web UI Service               │  │
│  └────────────┬─────────────────────┘  │
└───────────────┼────────────────────────┘
                │
        ┌───────▼───────┐
        │  noVNC UI     │
        │  (Port 6080)  │
        └───────────────┘
```

#### 1.1 Producer Service

**File**: `producer_service/api_server.py`

**Core Features**:
- FastAPI server providing REST API and SSE endpoints
- Manage producer service lifecycle
- Health check and status query
- Integrate Web UI management interface

**API Endpoints**:

| Endpoint | Method | Function | Description |
|----------|--------|----------|-------------|
| `/` | GET | Service Info | Returns version and status |
| `/health` | GET | Health Check | Checks service health |
| `/status` | GET | Get Status | Returns detailed service status |
| `/api/screenshot` | GET | Screenshot | Gets current screen capture |
| `/api/roi` | POST | Update ROI | Updates monitoring region config |
| `/stream` | GET | Message Stream | SSE real-time message stream |
| `/api/ui` | GET | Web UI | Management interface |

#### 1.2 Producer1 Observer

**File**: `producer_service/producer1_observer.py`

**Core Features**:
- Continuously monitor screen changes
- Use ROI (Region of Interest) for efficiency
- Detect new message bubbles
- Call content fetcher to process

**Workflow**:
```
1. Initialize Xvfb virtual display
2. Configure ROI monitoring region
3. Loop execution:
   - Capture screen screenshot
   - Use ChangeDetector to detect changes
   - Change detected → Call Producer2
   - Use MessageTypeClassifier to classify
   - Push message to Redis
```

#### 1.3 Producer2 Content Fetcher

**File**: `producer_service/producer2_content_fetcher.py`

**Core Features**:
- Extract message bubble boundaries
- Parse message content (text, image)
- OCR text recognition (if needed)
- Generate structured message

**Message Structure**:
```python
{
    "sender": "sender_name",
    "content": "message_content",
    "message_type": "text",  # text/image/video/link
    "timestamp": "2026-01-09T10:30:00",
    "metadata": {
        "bubble_bbox": [x, y, w, h],
        "has_avatar": True,
        "group_id": "group_123"
    }
}
```

#### 1.4 ChangeDetector

**File**: `producer_service/detector.py`

**Core Features**:
- Use dHash algorithm to detect frame differences
- HSV color space to identify message bubbles
- Contour detection and validation
- Threshold and morphological operations

**Key Methods**:
```python
class ChangeDetector:
    def compute_dhash(image):        # Compute image hash
    def hash_distance(hash1, hash2): # Compute Hamming distance
    def detect_changes(current, prev): # Detect significant changes
    def detect_bubbles(image):      # Identify message bubbles
```

**Configuration Parameters**:
- `threshold`: 0.05 (change threshold)
- `hash_diff_threshold`: 2 (hash distance threshold)
- `hsv_lower/upper`: HSV color range (green bubbles)
- `min_area`: 500 (minimum bubble area)

#### 1.5 MessageTypeClassifier

**File**: `producer_service/classifier.py`

**Core Features**:
- Classify message types based on image features
- HSV color space to detect icons
- Supported types: text, image, video, link, unknown

**Classification Logic**:
```
1. Detect yellow/blue icons → Media message
2. Further distinguish image vs video
3. Detect blue link icon → Link message
4. Check aspect ratio → Auxiliary judgment
5. Default → Text message
```

#### 1.6 Redis Queue Manager

**File**: `producer_service/queue_manager.py`

**Core Features**:
- Use Redis Streams for message queue
- Support multi-consumer concurrent reading
- Message persistence and fault tolerance
- Provide queue status query

**Data Structure**:
```
Stream: wechat_messages
Fields: sender, content, message_type, timestamp, metadata
```

#### 1.7 Web UI Management Interface

**File**: `static/index.html`

**Core Features**:
- Real-time screen capture viewing
- Visual ROI region configuration
- Service status monitoring
- Real-time message stream display
- Responsive design, mobile support

**Interface Layout**:
```
┌─────────────────────────────────┐
│         Header Bar               │
├──────────────┬──────────────────┤
│              │   Status Cards    │
│              │   - Service State │
│   Screen      │   - Message Count │
│   (noVNC)     │   - Detector State│
│              │                   │
│              │   ROI Config      │
│              │   - Coordinate In │
│              │   - Update Button │
│              │                   │
│              │   Message Stream  │
│              │   - Real-time Dis │
└──────────────┴──────────────────┘
```

### 2. Multi-Instance Deployment Support

**File**: `docker-compose.multi.yml`

**Core Features**:
- Support running multiple WeChat instances simultaneously
- Each instance has independent port mapping
- Shared Redis queue
- Independent data volume isolation

**Port Mapping**:

| Instance | FastAPI | noVNC | VNC |
|----------|---------|-------|-----|
| 1 | 8001 | 6081 | 5901 |
| 2 | 8002 | 6082 | 5902 |
| 3 | 8003 | 6083 | 5903 |

**Startup Command**:
```bash
docker-compose -f docker-compose.multi.yml up -d
```

### 3. Testing Framework

**Path**: `tests/`

**Test Types**:
1. **Unit Tests**: Test individual components
   - `test_queue_manager.py` - Redis queue manager
   - `test_producer_service.py` - Producer service components

2. **API Tests**: Test FastAPI endpoints
   - `test_api_server.py` - All REST API endpoints

3. **Integration Tests**: Test complete workflows
   - `test_integration.py` - End-to-end workflow
   - Docker service tests
   - Multi-instance tests

**Testing Tools**:
- pytest + pytest-asyncio
- pytest-html (HTML reports)
- pytest-cov (coverage)
- Mock/patch (external dependency isolation)

**Running Tests**:
```bash
# Run all tests
python run_tests.py all

# Run specific type
python run_tests.py unit
python run_tests.py api
python run_tests.py integration

# Generate coverage report
pytest tests/ --cov=. --cov-report=html
```

### 4. MonitorAgent

**Path**: `agents/monitor_agent.py`

**Core Responsibilities**:
- Manage WeChat sandbox Docker container start/stop
- Subscribe to WeChat message stream (Server-Sent Events)
- Parse and validate message format
- Trigger workflow execution

**Key Methods**:
```python
class MonitorAgent:
    async def start_container()    # Start WeChat sandbox container
    async def stop_container()     # Stop container
    async def start()              # Start monitoring messages
    def stop()                     # Stop monitoring
    def set_message_callback()     # Set message callback function
```

**Port Mapping**:
- `5800` → noVNC Web interface
- `5900` → VNC protocol
- `6789` → Producer service API

### 5. Orchestrator

**Path**: `services/orchestrator/main.py`

**Core Responsibilities**:
- Provide RESTful API endpoints
- Manage workflow instances and execution
- Handle concurrent requests and state management
- Return execution results and error handling

**API Endpoints**:

| Endpoint | Method | Function | Example |
|----------|--------|----------|---------|
| `/` | GET | Service Info | - |
| `/health` | GET | Health Check | - |
| `/workflow/trigger` | POST | Trigger Workflow | See below |
| `/workflow/status` | GET | Query Status | - |

**Trigger Workflow Request Format**:
```json
POST /workflow/trigger
{
  "sender": "Zhang San",
  "content": "Please generate this week's work report",
  "message_type": "text",
  "group_id": "group_123",
  "timestamp": "2026-01-09T10:30:00",
  "metadata": {
    "priority": "high",
    "mentions": ["@all"]
  }
}
```

**Response Format**:
```json
{
  "success": true,
  "workflow_id": "wf_20260109_103000_abc123",
  "status": "completed",
  "result": {
    "task_status": "completed",
    "document_path": "/output/report_20260109.docx"
  }
}
```

### 6. LangGraph Workflow Nodes

**Path**: `core/workflows/`

#### 6.1 Monitor Node

**File**: `nodes/monitor_node.py`

**Function**:
- Receive raw messages
- Validate message format and type
- Message preprocessing (cleanup, standardization)
- Route to next node

**Input**: `raw_message: RawMessage`
**Output**: Updated `AgentState`

#### 6.2 Multimodal Node

**File**: `nodes/multimodal_node.py`

**Function**:
- **Text messages**: Use LLM for intent recognition and task extraction
- **Image messages**: Use vision model (Qwen3-VL) for image content understanding
- **Mixed messages**: Fuse text and image information for comprehensive analysis
- **RAG enhancement**: Retrieve relevant context from vector database

**Processing Flow**:
```
Message Input → Determine Type → Select Model → Generate Analysis → RAG Retrieval → Fuse Results → Output
```

**AI Capabilities**:
- Text intent recognition (task type, urgency, executor)
- Image content recognition (screenshot, document, photo, QR code)
- Entity extraction (names, time, location, task content)
- Context understanding (combining historical dialogue and knowledge base)

#### 6.3 StateTracker Node

**File**: `nodes/state_tracker_node.py`

**Function**:
- Maintain task state machine (pending → in_progress → completed)
- Record task context and history
- Determine if task is completed
- Update Redis cache

**State Transition**:
```
┌──────────┐    Task Start    ┌──────────┐
│  Pending  │ ────────────→  │ In_Progress│
└──────────┘                └──────────┘
     ↑                          │
     │                     Task Complete
     │                          ↓
└──────────┐                ┌──────────┐
│ Completed│ ←────────────  │ Completed│
└──────────┘                └──────────┘
```

**Decision Logic**:
```python
def should_generate_document(state: AgentState) -> str:
    """Determine if document should be generated"""
    analysis = state.get("multimodal_analysis", {})

    # Judgment criteria:
    # 1. Clear completion signals ("completed", "done")
    # 2. Task status marked as completed
    # 3. Contains report generation instruction

    if any(signal in analysis.get("text", "") for signal in ["complete", "end", "report"]):
        return "yes"
    return "no"
```

#### 6.4 Document Node

**File**: `nodes/document_node.py`

**Function**:
- Select document template based on task type
- Generate Word report documents
- Update Excel ledgers
- Save documents to specified path
- Record document update history

**Template System**:
```
templates/
├── daily_report.j2         # Daily report template
├── weekly_report.j2        # Weekly report template
├── monthly_report.j2       # Monthly report template
├── task_summary.j2         # Task summary template
└── meeting_minutes.j2      # Meeting minutes template
```

**Output Paths**:
```
output/
├── reports/                # Report documents
│   ├── daily_20260109.docx
│   └── weekly_20260109.docx
└── ledgers/                # Ledger files
    └── task_tracker.xlsx
```

## Data Models

### Core Data Structures

**RawMessage**:
```python
class RawMessage(BaseModel):
    sender: str              # Sender
    content: str             # Message content
    message_type: MessageType # Message type
    group_id: str            # Group ID
    timestamp: datetime      # Timestamp
    metadata: dict = {}      # Metadata
    image_url: Optional[str] = None  # Image URL (if any)
```

**MessageType**:
```python
class MessageType(str, Enum):
    TEXT = "text"            # Plain text
    IMAGE = "image"          # Plain image
    TEXT_IMAGE = "text_image" # Text+Image mixed
    VOICE = "voice"          # Voice (future support)
    VIDEO = "video"          # Video (future support)
    FILE = "file"            # File (future support)
```

**AgentState**:
```python
class AgentState(TypedDict):
    # Input
    raw_message: RawMessage                  # Raw message

    # Processing results
    multimodal_analysis: Optional[dict]      # Multimodal analysis results
    task_status: Optional[str]               # Task status
    document_updates: List[dict]             # Document update history

    # Context
    messages: List[BaseMessage]              # Message records
    context: dict                            # Additional context
    next_action: Optional[str]               # Next action
```

**MultimodalAnalysis**:
```python
class MultimodalAnalysis(BaseModel):
    text_summary: str                        # Text summary
    image_description: Optional[str]         # Image description
    intent: str                              # Intent recognition
    entities: Dict[str, Any]                 # Extracted entities
    task_type: Optional[str]                 # Task type
    confidence: float                        # Confidence
    rag_context: Optional[List[str]]         # RAG retrieval context
```

## Data Flow

### Message Processing Flow

```
1. WeChat message
   ↓
2. Captured by WeChat sandbox container
   ↓
3. Producer1 observer detects screen changes
   ↓
4. ChangeDetector detects new bubble
   ↓
5. Producer2 extracts message content
   ↓
6. MessageTypeClassifier classifies message type
   ↓
7. Redis queue stores structured message
   ↓
8. FastAPI SSE endpoint pushes message stream
   ↓
9. MonitorAgent receives message
   ↓
10. HTTP POST to Orchestrator
   ↓
11. LangGraph workflow execution
   │
   ├─→ Monitor Node: Message validation
   ├─→ Multimodal Node: AI analysis
   │   ├─ Text understanding (LLM)
   │   ├─ Image understanding (Vision Model)
   │   └─ RAG retrieval (Vector DB)
   ├─→ StateTracker Node: State update
   │   ├─ Determine task status
   │   ├─ Update Redis
   │   └─ Decide next step
   └─→ Document Node: Document generation
       ├─ Select template
       ├─ Fill data
       ├─ Generate Word/Excel
       └─ Save files
   ↓
12. Return result
```

### State Flow

```
Initial State
  ↓
raw_message (receive message)
  ↓
multimodal_analysis (AI analysis)
  ↓
task_status (state update)
  ↓
Judge: Task Complete?
  ├─ No → END (wait for next message)
  └─ Yes → document_updates (generate document)
          ↓
        END
```

## Project Directory Structure

```
Mutil_Agent_WechatGroup_RPA/
├── agents/                              # Agent modules
│   └── monitor_agent.py                 # Monitoring agent
│
├── config/                              # Configuration management
│   ├── settings.yaml                    # Main configuration file
│   └── settings.py                      # Pydantic configuration class
│
├── core/                                # Core framework
│   ├── schemas.py                       # Data model definitions
│   ├── state.py                         # LangGraph state definitions
│   ├── workflows/                       # Workflow definitions
│   │   ├── main_workflow.py             # Main workflow
│   │   └── nodes/                       # Workflow nodes
│   │       ├── monitor_node.py          # Monitor node
│   │       ├── multimodal_node.py       # Multimodal analysis node
│   │       ├── state_tracker_node.py    # State tracking node
│   │       └── document_node.py         # Document generation node
│   └── exceptions.py                    # Custom exceptions
│
├── tools/                               # Tools layer
│   ├── excel_tool.py                    # Excel update tool
│   ├── word_tool.py                     # Word report generation tool
│   └── __init__.py
│
├── knowledge_base/                      # Knowledge base management
│   ├── vector_store.py                  # Vector storage management
│   └── embeddings.py                    # Embedding model management
│
├── services/                            # Services layer
│   ├── orchestrator/                    # Orchestration center
│   │   └── main.py                      # FastAPI application
│   │
│   └── wechat_sandbox/                  # WeChat sandbox
│       ├── Dockerfile                   # Docker image definition
│       ├── start.sh                     # Container startup script
│       ├── docker-compose.yml           # Single instance orchestration
│       ├── docker-compose.multi.yml    # Multi-instance orchestration
│       ├── QUICKSTART.md                # Quick start guide
│       │
│       ├── producer_service/            # Message producer service
│       │   ├── __init__.py
│       │   ├── api_server.py            # FastAPI server
│       │   ├── monitor.py               # Monitor
│       │   ├── producer1_observer.py    # Observer (screen monitoring)
│       │   ├── producer2_content_fetcher.py # Content fetcher
│       │   ├── queue_manager.py         # Redis queue manager
│       │   ├── classifier.py            # Message type classifier
│       │   ├── detector.py              # Change detector
│       │   ├── extractor.py             # Content extractor
│       │   └── main.py                  # Main entry point
│       │
│       ├── static/                      # Web UI static resources
│       │   └── index.html                # Management interface
│       │
│       ├── tests/                       # Test suite
│       │   ├── conftest.py              # pytest configuration
│       │   ├── pytest.ini               # pytest configuration file
│       │   ├── test_queue_manager.py    # Queue manager tests
│       │   ├── test_producer_service.py # Producer service tests
│       │   ├── test_api_server.py       # API tests
│       │   ├── test_integration.py      # Integration tests
│       │   └── README.md                # Test documentation
│       │
│       └── utils/                       # Utility modules
│           ├── config.py                # Configuration loader
│           └── logger.py                # Logging configuration
│
├── scripts/                             # Utility scripts
│   ├── init_knowledge_base.py           # Initialize knowledge base
│   ├── start_all.py                     # Start all services
│   └── run_monitor_agent.py             # Run monitoring agent
│
├── templates/                           # Jinja2 templates
│   ├── daily_report.j2                  # Daily report template
│   ├── weekly_report.j2                 # Weekly report template
│   └── task_summary.j2                  # Task summary template
│
├── data/                                # Data directory
│   ├── chroma_db/                       # Vector database
│   └── wechat_profile/                  # WeChat user data
│
├── output/                              # Output directory
│   ├── reports/                         # Generated reports
│   └── ledgers/                         # Ledger files
│
├── logs/                                # Logs directory
│
├── docs/                                # Documentation directory
│   ├── ENVIRONMENT_SETUP.md             # Environment setup guide
│   └── ENVIRONMENT_INIT.md              # Environment initialization guide
│
├── docker-compose.yml                   # Docker orchestration configuration
├── requirements.txt                     # Python dependencies
├── environment.yml                      # Conda environment configuration
├── .env.example                         # Environment variable example
├── .gitignore                           # Git ignore file
├── README.md                            # Project description
├── agent.md                             # AI agent context (Chinese)
├── claude.md                            # This file: Claude Code context (English)
└── claude-cn.md                         # Claude Code context (Chinese)
```

## Configuration Management

### Configuration File Priority

```
System Environment Variables > .env file > settings.yaml > Code defaults
```

### Environment Variable Naming Convention

Use double underscores for nested configuration:

```bash
# In settings.yaml:
# ai:
#   ollama:
#     base_url: "http://localhost:11434"

# Corresponding environment variable:
export AI__OLLAMA__BASE_URL="http://localhost:11434"
```

### Main Configuration Items

```yaml
# Project configuration
project:
  name: "wechat-workflow-agent"
  env: "development"  # development | production

# AI model services
ai:
  ollama:
    base_url: "http://localhost:11434"
    vision_model: "qwen3-vl-8b:latest"
    chat_model: "qwen3-72b:latest"
  siliconflow:
    api_key: "your-api-key"
    base_url: "https://api.siliconflow.cn/v1"
    embedding_model: "Qwen/Qwen3-Embedding-8B"

# Redis configuration
redis:
  host: "localhost"
  port: 6379
  lock_db: 1          # Distributed lock database
  cache_db: 0         # Cache database

# Vector database
chroma:
  persist_directory: "data/chroma_db"
  collection_name: "wechat_messages"

# WeChat sandbox
wechat_sandbox:
  docker_image: "wechat-sandbox:latest"
  data_volume: "wechat-data"
  producer_service_url: "http://localhost:6789"

# Document tools
ai:
  excel:
    template_path: "templates/task_tracker.xlsx"
    output_path: "output/ledgers/"
  word:
    template_dir: "templates/"
    output_path: "output/reports/"
```

## Deployment Guide

### Single Instance Deployment

```bash
# 1. Start service
cd services/wechat_sandbox
docker-compose up -d

# 2. Login to WeChat
# Access: http://localhost:6080
# Password: vnc123

# 3. Configure monitoring region
# Access: http://localhost:8000/api/ui
# Configure ROI coordinates in Web UI
```

### Multi-Instance Deployment

```bash
# 1. Start multi-instance
cd services/wechat_sandbox
docker-compose -f docker-compose.multi.yml up -d

# 2. Login to WeChat for each instance
# Instance1: http://localhost:6081
# Instance2: http://localhost:6082
# Instance3: http://localhost:6083

# 3. Configure ROI for each instance
# Instance1: http://localhost:8001/api/ui
# Instance2: http://localhost:8002/api/ui
# Instance3: http://localhost:8003/api/ui
```

## Testing Guide

### Running Tests

```bash
# Run all tests
python run_tests.py all

# Run specific type
python run_tests.py unit
python run_tests.py api
python run_tests.py integration

# Generate coverage report
pytest tests/ --cov=. --cov-report=html
```

### Test Types

1. **Unit Tests**: Test individual components (queue manager, detector, classifier)
2. **API Tests**: Test FastAPI endpoints
3. **Integration Tests**: Test end-to-end workflows
4. **Docker Tests**: Test containerized deployment

## Performance Optimization

### WeChat Sandbox Optimization

- **Adjust sampling frequency**: `capture_interval_ms` parameter controls CPU usage
- **Precise ROI configuration**: Reduce unnecessary screen region scanning
- **Redis persistence**: Use AOF mode for data safety
- **Instance scaling**: Horizontal scaling by adding Docker instances

### LangGraph Workflow Optimization

- **Connection pool reuse**: Reuse HTTP clients for Ollama and API calls
- **Async operations**: Use `asyncio` to improve concurrent message processing
- **Redis caching**: Cache common queries (embedding vectors, RAG results)
- **Batch processing**: Group multiple messages for batch analysis

## Security Notes

1. **Sensitive Information Protection**
   - Never commit `.env` file (already in `.gitignore`)
   - Use environment variables for all secrets
   - Store API keys in secure key management systems

2. **Container Security**
   - Use Docker network to isolate services
   - Limit container permissions (principle of least privilege)
   - Regularly update base images

3. **Input Validation**
   - Validate user input at all API endpoints
   - Sanitize and escape user-generated content
   - Use Pydantic for data validation

## Troubleshooting

### WeChat Sandbox Issues

**Container cannot start:**
```bash
docker ps -a                    # Check container status
docker logs wechat_producer_service  # View logs
docker inspect wechat_producer_service  # Check configuration
```

**VNC cannot connect:**
```bash
# Check port mapping
docker port wechat_producer_service 6080

# View container logs
docker logs -f wechat_producer_service

# Restart container
docker-compose restart producer_service
```

**Messages cannot be retrieved:**
```bash
# Check ROI configuration
curl http://localhost:8000/api/screenshot

# View Producer1 logs
docker logs -f wechat_producer_service | grep Producer1

# Check Redis connection
docker exec -it wechat_redis redis-cli ping
```

### LangGraph Workflow Issues

**Workflow execution failed:**
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check Redis
redis-cli ping

# Check orchestrator logs
# (View terminal output running uvicorn)
```

**Model loading error:**
```bash
# Verify model is pulled
docker exec -it ollama ollama list

# Re-pull
docker exec -it ollama ollama pull qwen3-vl-8b
```

## Reference Resources

- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Ollama Docs**: https://ollama.ai/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **OpenCV Docs**: https://docs.opencv.org
- **Project README**: See README.md for installation instructions
- **Quick Start Guide**: See `services/wechat_sandbox/QUICKSTART.md`
- **Test Documentation**: See `services/wechat_sandbox/tests/README.md`

## Development Standards

### Code Style

1. **Type hints**: All functions must have type hints
2. **Docstrings**: Use Google-style docstrings
3. **Logging**: Use `structlog` for structured logging
4. **Error handling**: Use custom exceptions from `core/exceptions.py`
5. **Async programming**: Use `async/await` for I/O operations

### Git Commit Convention

```
<type>: <brief description>

Type: Add | Fix | Refactor | Optimize | Docs | Config
```

### Testing Requirements

- All new features must include unit tests
- Core features must include integration tests
- Test coverage maintained above 80%
- Run full test suite before commit

## Project Roadmap

### Completed ✅

- [x] WeChat sandbox containerization
- [x] Screen monitoring and message capture
- [x] Message type classification
- [x] Redis queue management
- [x] FastAPI service
- [x] Web UI management interface
- [x] Multi-instance deployment support
- [x] Complete test suite

### In Progress 🚧

- [ ] LangGraph workflow integration
- [ ] Multimodal AI analysis
- [ ] Automated document generation
- [ ] Task status tracking

### Planned 📋

- [ ] Voice message support
- [ ] Video message processing
- [ ] User authentication and authorization
- [ ] Data analysis and visualization
- [ ] Performance monitoring and alerting
- [ ] Enterprise WeChat API integration
