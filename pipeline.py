from livekit.plugins import deepgram, silero
from livekit.plugins import openai as lk_openai
from livekit.plugins import google as lk_google
from app.config.settings import (
    STT_PROVIDER, STT_MODEL,
    LLM_PROVIDER, LLM_MODEL, OLLAMA_BASE_URL,
    TTS_PROVIDER, TTS_VOICE,
    VAD_PROVIDER, PROMPT_FILE
)
import yaml


def build_stt():
    if STT_PROVIDER == "deepgram":
        return deepgram.STT(model=STT_MODEL)
    elif STT_PROVIDER == "openai":
        return lk_openai.STT(model=STT_MODEL)
    else:
        raise ValueError(f"Unknown STT_PROVIDER: '{STT_PROVIDER}' — check config/settings.py")

def build_llm():
    if LLM_PROVIDER == "ollama":
        return lk_openai.LLM.with_ollama(
            model=LLM_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    elif LLM_PROVIDER == "openai":
        return lk_openai.LLM(model=LLM_MODEL)

    elif LLM_PROVIDER == "gemini":
        return lk_google.LLM(model=LLM_MODEL)

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}' — check config/settings.py")

def build_tts():
    if TTS_PROVIDER == "deepgram":
        return deepgram.TTS(model=TTS_VOICE)
    elif TTS_PROVIDER == "openai":
        return lk_openai.TTS(voice=TTS_VOICE)
    elif TTS_PROVIDER == "elevenlabs":
        from livekit.plugins import elevenlabs
        return elevenlabs.TTS(voice=TTS_VOICE)
    elif TTS_PROVIDER == "cartesia":
        from livekit.plugins import cartesia
        return cartesia.TTS(voice=TTS_VOICE)
    else:
        raise ValueError(f"Unknown TTS_PROVIDER: '{TTS_PROVIDER}' — check config/settings.py")


def build_vad():
    if VAD_PROVIDER == "silero":
        return silero.VAD.load()
    raise ValueError(f"Unknown VAD_PROVIDER: '{VAD_PROVIDER}' — check config/settings.py")


def load_instructions() -> str:
    with open(PROMPT_FILE, "r") as f:
        data = yaml.safe_load(f)
    return data["instructions"]

def build_chat_model():
    """Return a LangChain ChatModel for use with LangGraph.

    Uses the same LLM_PROVIDER / LLM_MODEL settings as the LiveKit pipeline,
    but returns a LangChain-compatible object instead of a LiveKit plugin.
    """
    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        # OLLAMA_BASE_URL is ".../v1" (OpenAI-compat); ChatOllama wants the root
        base = OLLAMA_BASE_URL.replace("/v1", "")
        return ChatOllama(model=LLM_MODEL, base_url=base)
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=LLM_MODEL)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: '{LLM_PROVIDER}'")
