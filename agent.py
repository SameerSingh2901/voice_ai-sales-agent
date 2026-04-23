from dotenv import load_dotenv
load_dotenv()

from livekit import agents
from livekit.agents import AgentSession, Agent, AgentServer
from pipeline import build_stt, build_llm, build_tts, build_vad, load_instructions
from app.tools.property_tool import property_search 

server = AgentServer()


class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions=load_instructions(),
            tools=[property_search],
        )


@server.rtc_session()
async def session(ctx):
    await AgentSession(
        stt=build_stt(),
        llm=build_llm(),
        tts=build_tts(),
        vad=build_vad(),
    ).start(room=ctx.room, agent=Assistant())


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=session))