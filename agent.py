import asyncio
import os
import json
from dotenv import load_dotenv
import time

from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, RoomInputOptions, cli, JobProcess, AutoSubscribe, RoomOutputOptions
from livekit.plugins import deepgram, silero, aws, openai, deepgram
from livekit.rtc import DataPacket
# from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit import api

load_dotenv()

outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
print(outbound_trunk_id)
if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
    raise ValueError("SIP_OUTBOUND_TRUNK_ID is not set or invalid")



class MultiModalAgent(Agent):
    def __init__(self) -> None:
        SYSTEM_PROMPT = """
        You are Alexis, a helpful and knowledgeable assistant from Gods of Growth.
        The user may speak or type at any time. Maintain shared context across both,
        and respond naturally and helpfully.
        """
        
        instructions = SYSTEM_PROMPT
        super().__init__(instructions=instructions)
        
    async def on_enter(self):
        await self.session.generate_reply(
            instructions=(
                f"Hello My name is Preety which is created by Gautam, How can i Assist You Today"
            )
        )
    
async def outbound_entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.SUBSCRIBE_ALL)
    print("Connected to room:", ctx.room.name)
    
    raw_metadata = ctx.job.metadata or ""
    metadata = {}
    
    if isinstance(raw_metadata, str) and raw_metadata.strip():
        try:
            metadata = json.loads(raw_metadata)
            print(f"Parsed metadata: {metadata}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            raise ValueError(f"Could not parse metadata JSON: {raw_metadata!r}")

    phone_number = metadata.get("phone_number")
    if not phone_number:
        print("Missing phone_number in job metadata")
        raise ValueError("Missing phone_number in job metadata")

    user_identity = "outbound_calle"
    print(f"Dialing {phone_number} into room {ctx.room.name}")
    
    try:
        await ctx.api.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=ctx.room.name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity=user_identity,
            )
        )
        print(f"SIP call initiated to {phone_number}")
    except Exception as e:
        print(f"Failed to create SIP participant: {e}")
        raise

    try:
        participant = await ctx.wait_for_participant(identity=user_identity)
        print(f"SIP participant joined: {participant.identity}")
    except Exception as e:
        print(f"Error waiting for SIP participant: {e}")
        raise
    
    start_time = time.time()
    timeout = 10
    
    session_should_start = False
    
    while True:
        status = participant.attributes.get("sip.callStatus")
        
        if status == "active":
            session_should_start = True
            break

        if status in ["terminated", "rejected"]:
            print(f"[SIP STATUS] {status} - exiting")
            break

        if status == "ringing" and (time.time() - start_time) > timeout:
            print("Call ringing too long, deleting room...")

            try:
                await ctx.api.room.delete_room(
                    api.DeleteRoomRequest(room=ctx.room.name)
                )
                print("Room deleted successfully")
            except Exception as e:
                print(f"Failed to delete room: {e}")

            return

        await asyncio.sleep(0.4)
        
    if not session_should_start:
        print("User did not pick up, skipping AgentSession")
        return
    
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM.with_cerebras(
            model="llama3.1-8b",
            temperature=0.1
        ),
        tts=aws.TTS(
            voice="Ruth",
            speech_engine="neural",
            language="en-US",
        ),
        vad=ctx.proc.userdata["vad"],
    )
    
    await session.start(
        room=ctx.room,
        agent=MultiModalAgent(),
        room_input_options=RoomInputOptions(
            # noise_cancellation=noise_cancellation.BVC(),
            text_enabled=True,
        ),        
        room_output_options=RoomOutputOptions(transcription_enabled=True)

    )
    @session.on("user_input_transcribed")
    def on_transcribed(evt):
        print("RECOGNIZED:", evt.transcript, "final?", evt.is_final)
    
    ctx.room.on("track_published", print("Track publshed"))


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        prewarm_fnc=prewarm,
        entrypoint_fnc=outbound_entrypoint,
        agent_name="adaptive-multimodal-agent"
    ))