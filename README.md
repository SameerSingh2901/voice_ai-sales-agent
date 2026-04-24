# Voice AI Agent Framework

> A provider-agnostic, real-time voice AI agent framework built for adaptability. Swap a prompt file, a tool, and a settings file — and the same pipeline becomes a property consultant, a book sales agent, a customer support bot, or anything else.

**Currently demoed as:** Priya, an AI property consultant for Indian real estate.

---

## Demo

> 🎥 *Demo video coming soon*

> 💼 Running locally because cloud costs money and I'm actively looking for a job. **Hire me and we'll deploy this together.**

---

## The Core Idea

Most voice AI projects are built for one specific use case — tightly coupled to their domain, their data, and their persona. This project is built differently.

The framework separates **infrastructure** from **behaviour**:

- The **pipeline** (`agent.py`, `pipeline.py`) handles all the real-time audio, STT, LLM, TTS, and VAD wiring. It never changes between use cases.
- The **behaviour** is fully defined by three files you swap out per deployment:

| File | What it controls |
|---|---|
| `app/config/settings.py` | Which STT, LLM, TTS, VAD providers to use and which models |
| `app/config/system_prompt.yaml` | Agent persona, conversation rules, tool-calling discipline |
| `app/tools/your_tool.py` | The domain-specific action the agent can take |

**To go from a property consultant to a book sales agent:** change the prompt, replace `property_tool.py` with `book_tool.py`, update the data in Pinecone, and you're done. The entire audio pipeline, provider switching, and RAG infrastructure stays identical.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       User Browser                           │
│            (LiveKit Playground via livekit-cli)              │
└────────────────────────┬─────────────────────────────────────┘
                         │  WebRTC audio
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    LiveKit Server                            │
│           (room management, signalling, relay)               │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              Voice AI Agent Framework  (Python)              │
│                                                              │
│  ── INFRASTRUCTURE (never changes) ──────────────────────── │
│  ┌───────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │  STT Plugin   │─▶│  Silero  │─▶│    LLM Plugin      │   │
│  │  (pluggable)  │  │   VAD    │  │    (pluggable)      │   │
│  └───────────────┘  └──────────┘  └────────┬───────────┘   │
│                                             │ tool call      │
│  ── BEHAVIOUR (swap per deployment) ──────  │               │
│                                             ▼               │
│  ┌───────────────┐              ┌──────────────────┐        │
│  │  TTS Plugin   │◀─ response ──│   Your Tool      │        │
│  │  (pluggable)  │              │ (property/book/  │        │
│  └───────────────┘              │  support/etc.)   │        │
│                                 └────────┬─────────┘        │
│  ┌─────────────────────────────┐         │                  │
│  │  system_prompt.yaml         │         ▼                  │
│  │  (persona + rules)          │  ┌──────────────────┐      │
│  └─────────────────────────────┘  │  Pinecone / Any  │      │
│  ┌─────────────────────────────┐  │  Data Source     │      │
│  │  settings.py                │  └──────────────────┘      │
│  │  (provider config)          │                            │
│  └─────────────────────────────┘                            │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Details |
|---|---|---|
| Real-time transport | [LiveKit](https://livekit.io) | WebRTC room, audio streaming, agent worker |
| Speech-to-text | [Deepgram](https://deepgram.com) | `nova-2` model — swappable with OpenAI Whisper |
| Voice activity detection | [Silero VAD](https://github.com/snakers4/silero-vad) | Detects end-of-speech |
| LLM | Ollama / OpenAI | Fully swappable via `settings.py` — no code changes |
| Embeddings | Ollama (`nomic-embed-text`) | 768-dim, runs fully locally |
| Text-to-speech | [Deepgram](https://deepgram.com) | `aura-asteria-en` — swappable with ElevenLabs, OpenAI, Cartesia |
| Vector database | [Pinecone](https://pinecone.io) | Semantic search + metadata filtering for any dataset |
| Agent framework | [LiveKit Agents](https://docs.livekit.io/agents/) | Pipeline orchestration, tool use, session management |

---

## Project Structure

```
.
├── agent.py                        # Entry point — defines the Assistant and starts the LiveKit worker
├── pipeline.py                     # Core infrastructure — builds STT, LLM, TTS, VAD from config
│
├── app/
│   ├── config/
│   │   ├── settings.py             # ← SWAP THIS: all provider and model choices per deployment
│   │   └── system_prompt.yaml      # ← SWAP THIS: agent persona, rules, and tool-calling behaviour
│   │
│   ├── tools/
│   │   └── property_tool.py        # ← SWAP THIS: the domain-specific tool (current demo: property search)
│   │
│   └── rag/
│       ├── ingest.py               # One-time script — embeds your dataset and uploads to Pinecone
│       └── pinecone_client.py      # Semantic search with metadata filters — works with any structured data
│
└── requirements.txt
```

The three files marked `← SWAP THIS` are the only files you change between deployments.

---

## How to Adapt This to a New Use Case

Here's what changing the domain actually looks like in practice.

**Example: property consultant → book sales agent**

**1. Replace the tool** (`app/tools/book_tool.py`):
```python
@function_tool
async def book_search(
    genre: str,
    max_price: float | None = None,
    author: str | None = None,
) -> list[dict]:
    return search_books(genre=genre, max_price=max_price, author=author)
```

**2. Update the prompt** (`system_prompt.yaml`):
```yaml
instructions: |
  You are Nova, a friendly book sales assistant.
  Collect genre and budget before searching.
  Only call book_search when you have genre confirmed.
  ...
```

**3. Update settings** (`settings.py`) — only if you want different providers:
```python
LLM_PROVIDER = "openai"   # switch to cloud if needed
TTS_VOICE = "aura-luna-en"  # different voice for different persona
```

**4. Ingest your new dataset** into Pinecone:
```bash
python -m app.rag.ingest  # point it at your books dataset
```

The audio pipeline, LiveKit integration, provider switching, and RAG infrastructure — all unchanged.

---

## Configuration

All provider choices live in `app/config/settings.py`:

```python
# STT — Options: "deepgram" | "openai"
STT_PROVIDER = "deepgram"
STT_MODEL    = "nova-2"          # Deepgram: nova-2 | nova | base | enhanced
                                 # OpenAI:   whisper-1

# LLM — Options: "ollama" | "openai"
LLM_PROVIDER    = "ollama"
LLM_MODEL       = "qwen2.5:7b"  # Ollama: llama3.1 | llama3.2 | mistral | gemma2 | phi3 | qwen2.5:7b
                                 # OpenAI: gpt-4o | gpt-4o-mini
OLLAMA_BASE_URL = "http://localhost:11434/v1"

# TTS — Options: "deepgram" | "openai" | "elevenlabs" | "cartesia"
TTS_PROVIDER = "deepgram"
TTS_VOICE    = "aura-asteria-en" # Deepgram: aura-asteria-en | aura-luna-en | aura-orion-en
                                 # OpenAI:   alloy | echo | fable | nova | shimmer
                                 # Cartesia: sonic-english | sonic-multilingual

# VAD — only silero is supported
VAD_PROVIDER = "silero"

# Embeddings (used during ingest only)
EMBEDDING_MODEL  = "nomic-embed-text"  # pull first: ollama pull nomic-embed-text
EMBEDDING_DIM    = 768
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

# Pinecone
PINECONE_INDEX_NAME = "ai-sales-properties"

# Prompt
PROMPT_FILE = "app/config/system_prompt.yaml"
```

---

## Environment Variables

```env
DEEPGRAM_API_KEY=your_deepgram_key

LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

PINECONE_API_KEY=your_pinecone_key
```

> **Note:** No OpenAI key needed when running with Ollama. LLM and embeddings both run fully locally.

---

## Setup & Running Locally

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- [livekit-cli](https://docs.livekit.io/reference/cli/) installed
- A [LiveKit Cloud](https://cloud.livekit.io) account (free tier works)
- A [Deepgram](https://deepgram.com) account (free tier works)
- A [Pinecone](https://pinecone.io) account with an index created

### Step 1 — Pull Ollama models

```bash
ollama pull qwen2.5:7b        # LLM
ollama pull nomic-embed-text  # Embeddings (for ingest)
```

### Step 2 — Clone and install

```bash
git clone https://github.com/SameerSingh2901/voice_ai-sales-agent.git
cd voice_ai-sales-agent

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Step 3 — Configure

```bash
cp .env.example .env
# Fill in your keys
```

Edit `app/config/settings.py` to choose your providers and models.

### Step 4 — Ingest your dataset into Pinecone

```bash
python -m app.rag.ingest
```

### Step 5 — Authenticate with LiveKit CLI

```bash
lk cloud auth
```

### Step 6 — Start the agent

```bash
python -m agent start
```

### Step 7 — Test via LiveKit Playground

Go to [agents-playground.livekit.io](https://agents-playground.livekit.io), connect to your LiveKit project, enable your mic, and start talking. The agent introduces itself immediately.

---

## Demo Use Case — Priya, Property Consultant

The current deployment demonstrates the framework as **Priya**, an AI property consultant for Indian real estate.

**Dataset:** A curated set of Indian property listings with the following fields:

| Field | Type | Example |
|---|---|---|
| `id` | string | `prop_001` |
| `title` | string | `Sunny 2BHK in Bandra West` |
| `city` | string | `mumbai` |
| `price` | integer (INR) | `8500000` |
| `bedrooms` | integer | `2` |
| `property_type` | string | `apartment` |
| `description` | string | Free-text, used for semantic search |

**Search filters supported:** city, property type, bedrooms, min/max price — combined with semantic vector search so natural language queries like "affordable flat near the sea in Mumbai" return relevant results.

**Prompt design decisions:**
- Agent introduces itself immediately on session start — no user prompt needed
- LLM collects city + property type before calling the search tool, preventing bad queries
- Unit conversion rules (lakh/crore → INR integers) baked into the prompt
- Hard guardrails: no fabricating listings, no financial advice

---

## How the RAG Pipeline Works

**Ingestion** (`ingest.py`) — run once per dataset:
- Data is embedded using `nomic-embed-text` via Ollama (768 dimensions)
- Vectors uploaded to Pinecone with full metadata attached

**Retrieval** (`pinecone_client.py`) — runs on every tool call:
- Semantic vector search + metadata filters applied together
- Results ranked by similarity score and returned to the LLM

This works with any structured dataset — properties, books, products, FAQs, or anything else you ingest.

---

## What's Next

- [ ] Additional demo use cases to showcase the framework's adaptability
- [ ] React frontend using LiveKit Agents UI components
- [ ] Deployment on LiveKit Cloud with a token server
- [ ] Hindi and regional language support

---

## Built By

**Sameer Singh**

Built this to explore what a truly reusable voice AI agent architecture looks like — where the infrastructure is generic and the domain is just configuration. The goal was to build something a company could pick up, point at their data and prompt, and have a working voice agent without touching the pipeline.

If you're a recruiter or hiring manager: yes, this works, yes I built all of it, and yes I'm very much open to opportunities. It's local-only because cloud hosting costs money I don't currently have — but the architecture is production-ready and I'd love to show you what it can do.


[LinkedIn]((https://www.linkedin.com/in/sameersingh2901/)) · [GitHub](https://github.com/SameerSingh2901) · [Email - sameersinghwork@gmail.com](mailto:sameersinghwork@gmail.com)