# config/settings.py

# ─────────────────────────────────────────────
#  STT  (Speech-to-Text)
# ─────────────────────────────────────────────
# Options: "deepgram" | "openai"
STT_PROVIDER = "deepgram"

# Deepgram models: "nova-2" | "nova" | "base" | "enhanced"
# OpenAI models:   "whisper-1"
STT_MODEL = "nova-2"


# ─────────────────────────────────────────────
#  LLM
# ─────────────────────────────────────────────
# Options: "ollama" | "openai"
# LLM_PROVIDER = "ollama"
LLM_PROVIDER = "ollama"

# Ollama models:  "llama3.1" | "llama3.2" | "mistral" | "gemma2" | "phi3"
# OpenAI models:  "gpt-4o"   | "gpt-4o-mini"
LLM_MODEL = "qwen2.5:7b"

# Only used when LLM_PROVIDER = "ollama"
OLLAMA_BASE_URL = "http://localhost:11434/v1"


# ─────────────────────────────────────────────
#  TTS  (Text-to-Speech)
# ─────────────────────────────────────────────
# Options: "deepgram" | "openai" | "elevenlabs" | "cartesia"
TTS_PROVIDER = "deepgram"

# Deepgram voices:   "aura-asteria-en" | "aura-luna-en" | "aura-orion-en"
#                    "aura-zeus-en"    | "aura-athena-en"
# OpenAI voices:     "alloy" | "echo" | "fable" | "onyx" | "nova" | "shimmer"
# ElevenLabs voices: use the voice name from your ElevenLabs dashboard
# Cartesia voices:   "sonic-english" | "sonic-multilingual"
TTS_VOICE = "aura-asteria-en"


# ─────────────────────────────────────────────
#  VAD  (Voice Activity Detection)
# ─────────────────────────────────────────────
# Currently only "silero" is supported — leave this alone
VAD_PROVIDER = "silero"


# ─────────────────────────────────────────────
#  Prompt
# ─────────────────────────────────────────────
# Path to the YAML file containing the system prompt
PROMPT_FILE = "app/config/system_prompt.yaml"

# ─────────────────────────────────────────────
#  Pinecone / RAG
# ─────────────────────────────────────────────
# Pinecone index name (for RAG retrieval)
PINECONE_INDEX_NAME = "ai-sales-properties"

# ─────────────────────────────────────────────
#  Embeddings / RAG
# ─────────────────────────────────────────────
# Embedding model served via Ollama
# Pull it first: ollama pull nomic-embed-text
EMBEDDING_MODEL     = "nomic-embed-text"
EMBEDDING_DIM       = 768          # nomic-embed-text output dimension
OLLAMA_EMBED_URL    = "http://localhost:11434/api/embeddings"