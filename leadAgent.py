from livekit.agents import cli, WorkerOptions, JobContext, AgentSession, JobProcess, RoomInputOptions
from livekit.plugins import deepgram, silero, openai, noise_cancellation, aws
from livekit.plugins.turn_detector.english import EnglishModel
from Agent.Leadagent import LeadAgent
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()
        
async def entrypoint(ctx: JobContext):
    session = AgentSession(
            vad=ctx.proc.userdata["vad"],
            turn_detection=EnglishModel()
    )
    
    try:
        await session.start(
                room=ctx.room,
                agent=LeadAgent(),
                room_input_options=RoomInputOptions(
                    audio_enabled=True,
                    text_enabled=True,
                    noise_cancellation=noise_cancellation.BVC()
                ),
        )
    except Exception as e:
        print(f"Session failed to start: {e}")

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        prewarm_fnc=prewarm,
        entrypoint_fnc=entrypoint
    ))