# Priya — AI Voice Property Consultant

> A real-time voice AI agent that helps users find properties across India through natural conversation. Speak naturally, Priya listens, searches semantically, and talks back — all in real time.

---

## Demo

> 🎥 *Demo video coming soon*

> 💼 Running locally because cloud costs money and I'm actively looking for a job. **Hire me and we'll put this in production together.**

---

## What Priya Does

Priya is a voice-first property consultant for Indian real estate. Here's the full loop of a single conversation turn:

1. User speaks into the browser mic
2. **Deepgram STT** (`nova-2`) transcribes the audio in real time
3. **Silero VAD** detects end-of-speech so Priya knows when to respond
4. The **LLM** (Ollama / OpenAI — swappable via config) reasons over the conversation
5. Once the user provides city + property type, the LLM calls `property_search`
6. `property_search` runs a **semantic vector search on Pinecone**, filtered by city, type, bedrooms, and price range
7. The LLM summarises the top matches naturally — names, prices in lakhs/crores, key features
8. **Deepgram TTS** (`aura-asteria-en`) speaks the response back to the user
9. Priya waits for the next turn

Priya introduces herself the moment the session starts — the user doesn't need to say anything first.

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
│                  Priya Agent  (Python)                       │
│                                                              │
│  ┌───────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │ Deepgram STT  │─▶│  Silero  │─▶│        LLM         │   │
│  │   nova-2      │  │   VAD    │  │  Ollama / OpenAI   │   │
│  └───────────────┘  └──────────┘  └────────┬───────────┘   │
│                                             │ tool call      │
│                                             ▼               │
│                                  ┌──────────────────┐       │
│                                  │ property_search   │       │
│                                  └────────┬─────────┘       │
│                                           │                 │
│  ┌───────────────┐                        ▼                 │
│  │ Deepgram TTS  │◀──────────── ┌──────────────────┐        │
│  │aura-asteria-en│   response   │    Pinecone       │        │
│  └───────────────┘              │ (semantic search  │        │
│                                 │  + meta filters)  │        │
│                                 └──────────────────┘        │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Details |
|---|---|---|
| Real-time transport | [LiveKit](https://livekit.io) | WebRTC room, audio streaming, agent worker |
| Speech-to-text | [Deepgram](https://deepgram.com) | `nova-2` model, real-time transcription |
| Voice activity detection | [Silero VAD](https://github.com/snakers4/silero-vad) | Detects end-of-speech |
| LLM | Ollama / OpenAI | Configurable — see `settings.py` |
| Embeddings | Ollama (`nomic-embed-text`) | 768-dim embeddings for property ingestion |
| Text-to-speech | [Deepgram](https://deepgram.com) | `aura-asteria-en` voice |
| Vector database | [Pinecone](https://pinecone.io) | Semantic search + metadata filtering |
| Agent framework | [LiveKit Agents](https://docs.livekit.io/agents/) | Pipeline orchestration, tool use, sessions |

---

## Project Structure

```
.
├── agent.py                        # Entry point — defines the Assistant and starts the LiveKit worker
├── pipeline.py                     # Builds STT, LLM, TTS, VAD instances from config
│
├── app/
│   ├── config/
│   │   ├── settings.py             # All provider choices live here — swap providers without touching agent code
│   │   └── system_prompt.yaml      # Priya's system prompt — personality, rules, tool instructions
│   │
│   ├── tools/
│   │   └── property_tool.py        # property_search tool — called by the LLM, queries Pinecone
│   │
│   └── rag/
│       ├── ingest.py               # One-time script — embeds property data and uploads to Pinecone
│       └── pinecone_client.py      # Pinecone client — semantic search with metadata filter logic
│
└── requirements.txt
```

---

## Configuration

All provider choices live in `app/config/settings.py`. No code changes needed to swap models — just edit this file.

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

Create a `.env` file in the project root:

```env
DEEPGRAM_API_KEY=your_deepgram_key

LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

PINECONE_API_KEY=your_pinecone_key
```

> **Note:** No OpenAI key needed when running with Ollama. The LLM and embeddings both run fully locally.

---

## Setup & Running Locally

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running locally
- [livekit-cli](https://docs.livekit.io/reference/cli/) installed
- A [LiveKit Cloud](https://cloud.livekit.io) account (free tier works)
- A [Deepgram](https://deepgram.com) account (free tier works)
- A [Pinecone](https://pinecone.io) account with an index created

---

### Step 1 — Pull Ollama models

```bash
ollama pull qwen2.5:7b        # LLM
ollama pull nomic-embed-text  # Embeddings (needed for ingest step)
```

---

### Step 2 — Clone and install

```bash
git clone https://github.com/SameerSingh2901/voice_ai-sales-agent.git   # replace with your repo URL
cd priya-agent

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

### Step 3 — Configure

```bash
cp .env.example .env
# Fill in your keys — see Environment Variables section above
```

Edit `app/config/settings.py` to set your preferred providers and models.

---

### Step 4 — Ingest property data into Pinecone

One-time setup. Embeds the property dataset and uploads it to Pinecone.

```bash
python -m app.rag.ingest
```

---

### Step 5 — Authenticate with LiveKit CLI

```bash
lk cloud auth
```

Opens your browser to authenticate with LiveKit Cloud. Only needed once.

---

### Step 6 — Start the agent

```bash
python -m agent start
```

---

### Step 7 — Test via LiveKit Playground

Go to [agents-playground.livekit.io](https://agents-playground.livekit.io), connect to your LiveKit project, enable your mic, and start talking. Priya will introduce herself immediately without any prompt from you.

---

## How the RAG Pipeline Works

### Ingestion (`ingest.py`) — run once

- Property listings are loaded from a local JSON dataset
- Each listing is converted to a descriptive text string
- The text is embedded using `nomic-embed-text` via Ollama (768 dimensions)
- Vectors are uploaded to Pinecone with full metadata attached

### Retrieval (`pinecone_client.py`) — runs on every search

When the LLM calls `property_search`, the tool queries Pinecone with both a semantic vector search and optional metadata filters:

| Filter | Match type | Example value |
|---|---|---|
| `city` | Exact | `"mumbai"` |
| `property_type` | Exact | `"apartment"` |
| `bedrooms` | Exact | `2` |
| `min_price` / `max_price` | Range | `5000000` – `15000000` |

Filters are combined — so "affordable 2BHK apartment in Pune" translates to a semantic query with city, type, bedroom, and price filters all applied together. Results are ranked by vector similarity score.

---

## The Property Dataset

Priya searches a demo dataset of Indian property listings. Each listing has the following fields:

| Field | Type | Example |
|---|---|---|
| `id` | string | `prop_001` |
| `title` | string | `Sunny 2BHK in Bandra West` |
| `city` | string | `mumbai` |
| `address` | string | `Linking Road, Bandra West, Mumbai` |
| `price` | integer (INR) | `8500000` |
| `bedrooms` | integer | `2` |
| `bathrooms` | integer | `2` |
| `area_sqft` | integer | `950` |
| `property_type` | string | `apartment` |
| `description` | string | Free-text, used for semantic search |

---

## Prompt Design

Priya's behaviour is fully defined in `app/config/system_prompt.yaml`. Key decisions:

- **Auto-introduction** — Priya speaks first using `on_enter`, no user prompt needed to start the conversation
- **Mandatory field collection** — the LLM is explicitly instructed not to call `property_search` until it has both city AND property type, preventing empty or low-quality searches
- **Unit conversion rules** — the prompt contains explicit conversion instructions so the LLM always passes plain INR integers to the tool (1 crore = 10,000,000 / 1 lakh = 100,000)
- **Voice-first constraints** — responses are kept concise, no raw data or JSON is ever read aloud, natural Indian English throughout
- **Hard guardrails** — no fabricating listings not returned by the tool, no financial advice, no going off-topic

---

## What's Next

- [ ] Real property listings via a live real estate API
- [ ] React frontend using LiveKit Agents UI components
- [ ] Deployment on LiveKit Cloud with a proper token server
- [ ] Hindi and regional language query support

---

## Built By

**Sameer Singh**

Built this end-to-end to understand what a production-grade voice AI agent actually looks like — raw audio in, semantic search, natural speech out, all in real time. Every layer from STT to vector search to TTS is wired together and working.

If you're a recruiter or hiring manager: yes, this works, yes I built all of it, and yes I'm very much open to opportunities. It's local-only because cloud hosting costs money I don't currently have — but the architecture is production-ready and I'd love to show you what it can do.

[LinkedIn]((https://www.linkedin.com/in/sameersingh2901/)) · [GitHub](https://github.com/SameerSingh2901) · [Email - sameersinghwork@gmail.com](#)