# EduSmartLearn - Safe Multi-Agent Teaching System

## MTech Project: Safe Multi-Agent Teaching System using Agent-to-Agent Protocol and Model Context Protocol Tools

**Author:** Soumyadeep Saha (M25AI1015)

---

## Overview

EduSmartLearn is a protocol-first, tool-using, multi-agent teaching system designed for safe and effective educational assistance. The system implements:

- **Agent-to-Agent (A2A) Protocol** for structured inter-agent communication
- **Model Context Protocol (MCP)** for standardized tool access
- **Defense-in-depth safety** with consent workflows and guardrails
- **Personalized learning** through learner modeling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Interaction & State Layer                     │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────────┐ │
│  │ Student/Instructor│  │   Tutor Agent   │  │ Session Store +│ │
│  │    UI (Web/App)   │─▶│(Session manager │◀▶│ Long-Term      │ │
│  │                   │  │    + Dialog)    │  │ Memory         │ │
│  └──────────────────┘  └─────────────────┘  └────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│              Multi-Agent Orchestration Layer (A2A)               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │     Knowledge Retrieval Agent (Orchestrator / A2A Router) │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │ A2A                               │
│       ┌──────────────────────┼──────────────────────┐           │
│       │                      │                      │           │
│  ┌────▼─────────┐    ┌──────▼──────┐    ┌─────────▼────────┐   │
│  │ Teacher Agent│    │  Evaluator  │    │ Code Execution   │   │
│  │  (Content    │    │   Agent     │    │     Agent        │   │
│  │  Generation) │    │(Assessment +│    │  (Run / Debug)   │   │
│  └──────────────┘    │  Feedback)  │    └──────────────────┘   │
│         │            └─────────────┘                            │
│  ┌──────┴──────────────────────────────────────┐               │
│  │  AI Content │ ML Content │ DL Content │ Programming Lang   │ │
│  │    Agent    │   Agent    │   Agent    │      Agent         │ │
│  └─────────────────────────────────────────────┘               │
│                              │                                  │
│                    ┌─────────▼─────────┐                       │
│                    │   Student Agent   │                       │
│                    │ (Learner Model +  │                       │
│                    │  Personalization) │                       │
│                    └───────────────────┘                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │ tools and action request
┌─────────────────────────────▼───────────────────────────────────┐
│                        Safety Layer                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │     Safety / Guardrail Agent + Policy Engine              │   │
│  │  (Consent · Schema Validation · Prompt-Injection Defense  │   │
│  │                    · Least-Privilege)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              │ LLM inference by all agents
┌─────────────────────────────▼───────────────────────────────────┐
│                  Execution & Integration Layer                   │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  MCP Server &  │  │  LLM Backends  │  │External Resources│  │
│  │     Tools      │  │ (Model APIs /  │  │ (APIs · Docs ·   │  │
│  │(Learner Model +│  │  Local Models) │  │    Sandbox)      │  │
│  │Personalization)│  │                │  │                  │  │
│  └────────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│         Observability & Audit Logs                               │
│    (A2A Traces · Tool Logs · Metrics · Evaluation Results)       │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
edusmartlearn/
├── config/
│   ├── __init__.py
│   └── settings.py                    # Global configuration
├── protocols/
│   ├── __init__.py
│   └── a2a_protocol.py                # A2A message schema and routing
├── mcp_server/
│   ├── __init__.py
│   └── tools/
│       ├── __init__.py
│       ├── doc_search.py              # RAG document retrieval
│       ├── code_run.py                # Sandboxed code execution
│       ├── quiz_bank.py               # Quiz storage/retrieval
│       └── logging_tool.py            # Structured logging
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                  # Base agent with Gemini integration
│   ├── tutor_agent.py                 # Session manager + Dialog
│   ├── knowledge_retrieval_agent.py   # Orchestrator / A2A Router
│   ├── teacher_agent.py               # Content Generation
│   ├── evaluator_agent.py             # Assessment + Feedback
│   ├── code_execution_agent.py        # Run / Debug
│   ├── safety_agent.py                # Guardrails + Policy Engine
│   └── student_agent.py               # Learner Model + Personalization
├── memory/
│   ├── __init__.py
│   ├── session_store.py               # Session state management
│   └── long_term_memory.py            # Persistent learner data
├── observability/
│   ├── __init__.py
│   ├── audit_logger.py                # Structured audit logging
│   └── metrics.py                     # Evaluation metrics
├── data/
│   ├── course_materials/              # RAG document store
│   ├── learner_profiles/              # Student model data
│   └── quiz_bank.json                 # Quiz questions
├── logs/                              # Audit logs
├── main.py                            # Application entry point
├── requirements.txt                   # Dependencies
├── .env.example                       # Environment template
└── README.md                          # This file
```

## Installation

### 1. Clone and Setup

```bash
cd edusmartlearn

# Delete old Chroma data to reindex
rm -rf data/chroma_db/
# Delete all generated data
rm -rf data/conversations/
rm -rf data/learner_profiles/
rm -rf data/metrics/
rm -rf logs/

# Remove old virtual environmen (venv)
rm -rf venv/

# /opt/homebrew/bin/python3 --version
# /usr/local/bin/python3 --version
/usr/local/bin/python3 -m venv venv # please use a different pathin your own machine, I have used my own python path
source venv/bin/activate  # On Windows: venv\Scripts\activate
python --version
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
#cp .env.example .env
# Edit .env and add your Gemini API key
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

### 3. Run the System

## Usage

### Interactive CLI

```bash
# Step 1: Run your test session
python main.py
# Run all 20 test queries from the queries.md file
# Type /quit when done

# Step 2: Extract metrics
You: /metrics
or
cat data/metrics/metrics_*.json
or
python extract_metrics.py
```

Commands:
- Type questions naturally to learn
- `/quiz <topic>` - Generate a quiz
- `/code` - Enter code execution mode
- `/profile` - View learner profile
- `/metrics` - View system metrics
- `/quit` - Exit


### just in case you want to see the embeddings
chroma run --path ./data/chroma_db --port 8001
**For Mac terminal like my machnine**  --> Ctrl + Z
**For Windows terminal**  --> Ctrl + X

### Programmatic Usage (to be used as a library)

```python
import asyncio
from main import EduSmartLearn

async def main():
    # Initialize system
    system = EduSmartLearn()
    await system.initialize()
    
    # Start a session
    session = system.start_session("user123")
    
    # Chat with the system
    response = await system.chat(
        "Explain backpropagation in neural networks",
        session.session_id
    )
    print(response)
    
    # Generate a quiz
    quiz = await system.generate_quiz("neural networks", num_questions=5)
    print(quiz)
    
    # Execute code (with consent)
    result = await system.execute_code(
        "print('Hello, World!')",
        consent_granted=True
    )
    print(result)
    
    # Shutdown
    await system.shutdown()

asyncio.run(main())
```

## Agent Descriptions (per Architecture Diagram)

| Agent | Role | Tool Access |
|-------|------|-------------|
| **Tutor Agent** | Session manager + Dialog | logging |
| **Knowledge Retrieval Agent** | Orchestrator / A2A Router | doc_search, logging |
| **Teacher Agent** | Content Generation | doc_search, logging |
| **Evaluator Agent** | Assessment + Feedback | quiz_bank, doc_search, logging |
| **Code Execution Agent** | Run / Debug | code_run (consent required) |
| **Safety Agent** | Guardrails + Policy Engine | logging |
| **Student Agent** | Learner Model + Personalization | logging |

## A2A Protocol

The Agent-to-Agent protocol provides structured communication:

```python
from protocols.a2a_protocol import A2AMessage, MessageType, AgentCapability

# Create a task request
message = A2AMessage(
    message_type=MessageType.TASK_REQUEST,
    sender="orchestrator",
    receiver="teacher_agent",
    capabilities_requested=[AgentCapability.EXPLAIN_CONCEPT],
    payload={"topic": "neural networks", "level": "beginner"}
)

# Create a response
response = message.create_response(
    message_type=MessageType.TASK_RESPONSE,
    sender="teacher_agent",
    payload={"explanation": "Neural networks are..."}
)
```

## Safety Features

1. **Consent Workflows**: Code execution requires explicit user consent
2. **Input Sanitization**: Prevents prompt injection attacks
3. **Rate Limiting**: Prevents abuse
4. **Least Privilege**: Agents only access necessary tools
5. **Audit Logging**: All actions are logged for compliance

## Configuration

Key settings in `config/settings.py`:

```python
# Gemini LLM settings
gemini.model_name = "gemini-1.5-flash"
gemini.temperature = 0.7

# Safety settings
safety.require_consent_for_code_execution = True
safety.code_execution_timeout = 10  # seconds
safety.max_requests_per_minute = 60

# Session settings
session.session_timeout_minutes = 60
session.max_history_turns = 20
```

## Adding Course Materials

Place `.txt` or `.md` files in `data/course_materials/` for RAG:

```bash
data/course_materials/
├── neural_networks.md
├── machine_learning_basics.txt
└── python_programming.md
```

## Evaluation Metrics

The system tracks metrics aligned with agent-quality pillars:

- **Effectiveness**: Task completion rate, quiz scores
- **Efficiency**: Response times, token usage
- **Robustness**: Error rates, recovery rates
- **Safety**: Policy compliance, consent rates

Access via:
```python
metrics = system.get_metrics_summary()
```

## Technology Stack

- **LLM**: Google Gemini (gemini-1.5-flash)
- **Vector DB**: ChromaDB (for RAG)
- **Sandbox**: RestrictedPython (code execution)
- **Validation**: Pydantic
- **Logging**: structlog

## License

This project is part of an MTech academic project.

## References

- Google Gemini API: https://ai.google.dev/
- Model Context Protocol: https://modelcontextprotocol.io/
- Agent-to-Agent Protocol concepts from Google ADK patterns
