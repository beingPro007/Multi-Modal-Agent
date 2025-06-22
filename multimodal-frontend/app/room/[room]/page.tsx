"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import {
  Room,
  RemoteParticipant,
  RoomEvent,
  DataPacket_Kind,
  Participant,
} from "livekit-client";

export default function RoomPage() {
  const { room: roomName } = useParams();
  const [room, setRoom] = useState<Room | null>(null);
  const [connected, setConnected] = useState(false);
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState<{
    sender: string;
    text: string;
    avatar?: string | null;
    identity: string;
  }[]>([]);
  const [participantInfo, setParticipantInfo] = useState<Record<string, { avatar?: string; displayName?: string }>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!roomName) return;

    const connectToRoom = async () => {
      const res = await fetch(`/api/token?room=${roomName}`);
      const { token } = await res.json();

      const newRoom = new Room();
      await newRoom.connect(process.env.NEXT_PUBLIC_LIVEKIT_URL!, token);

      newRoom.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
        console.log("participant connected:", participant.identity);

        const metadata = participant.metadata ? JSON.parse(participant.metadata) : {};
        setParticipantInfo((prev) => ({
          ...prev,
          [participant.identity]: {
            displayName: metadata.displayName || participant.identity,
            avatar: metadata.avatar || null,
          },
        }));
      });

      newRoom.on(RoomEvent.ParticipantMetadataChanged, (metadata: string | undefined, participant: Participant) => {
        const updatedMetadata = metadata ? JSON.parse(metadata) : {};
        setParticipantInfo((prev) => ({
          ...prev,
          [participant.identity]: {
            displayName: updatedMetadata.displayName || participant.identity,
            avatar: updatedMetadata.avatar || null,
          },
        }));
      });

      newRoom.localParticipant.on("dataReceived", (payload: Uint8Array, kind: DataPacket_Kind, topic?: string) => {
        if (topic !== "lk.chat") return;
        const text = new TextDecoder().decode(payload);
        setChatLog((prev) => [
          ...prev,
          {
            sender: "You",
            text,
            identity: newRoom.localParticipant.identity,
            avatar: participantInfo[newRoom.localParticipant.identity]?.avatar || null,
          },
        ]);
      });

      const messageBuffer = new Map();

      newRoom.on(RoomEvent.DataReceived, (payload, participant) => {
        const text = new TextDecoder().decode(payload);
        const identity = participant?.identity || "unknown";
        const meta = participant?.metadata ? JSON.parse(participant.metadata) : {};

        if (!messageBuffer.has(identity)) {
          messageBuffer.set(identity, { text: "", timestamp: Date.now() });
        }

        const buffer = messageBuffer.get(identity);
        buffer.text += text;

        setChatLog((prev) => {
          const updatedLog = [...prev.filter((msg) => msg.identity !== identity)];
          return [
            ...updatedLog,
            {
              sender: meta.displayName || identity,
              text: buffer.text,
              identity,
              avatar: meta.avatar || null,
            },
          ];
        });

        setTimeout(() => {
          if (messageBuffer.has(identity)) {
            messageBuffer.delete(identity);
          }
        }, 1000);
      });

      setRoom(newRoom);
      setConnected(true);
    };

    connectToRoom();

    return () => {
      room?.disconnect();
    };
  }, [roomName]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const sendMessage = async () => {
    if (!room || !message.trim()) return;
    const encoded = new TextEncoder().encode(message);
    await room.localParticipant.publishData(encoded, { reliable: true, topic: "lk.chat" });
    setMessage("");
  };

  return (
    <div className="p-4 max-w-4xl mx-auto h-screen flex flex-col">
      <h1 className="text-xl sm:text-2xl font-bold mb-4">Room: {roomName}</h1>

      {connected ? (
        <div className="flex-1 flex flex-col space-y-4 overflow-hidden">
          <div className="flex-1 overflow-y-auto border p-2 rounded bg-blue-400 flex flex-col space-y-2">
            {chatLog.map((msg, i) => {
              const isSelf = msg.sender === "You";
              const initials = msg.sender.charAt(0).toUpperCase();
              return (
                <div
                  key={i}
                  className={`flex items-start ${isSelf ? "justify-end" : "justify-start"}`}
                >
                  {!isSelf && (
                    <>{
                      msg.avatar ? (
                        <img
                          src={msg.avatar}
                          alt={msg.sender}
                          className="w-8 h-8 rounded-full object-cover mr-2"
                        />
                      ) : (
                        <div className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-400 text-white font-bold mr-2">
                          {initials}
                        </div>
                      )
                    }</>
                  )}
                  <div className={`p-3 rounded-lg max-w-xs text-sm leading-tight ${isSelf ? "bg-blue-500 text-white" : "bg-white text-gray-900 border border-gray-200"}`}>
                    {!isSelf && (
                      <p className="text-xs text-gray-500 mb-1">{msg.sender}</p>
                    )}
                    <p>{msg.text}</p>
                  </div>
                  {isSelf && (
                    <>{
                      msg.avatar ? (
                        <img
                          src={msg.avatar}
                          alt={msg.sender}
                          className="w-8 h-8 rounded-full object-cover ml-2"
                        />
                      ) : (
                        <div className="w-8 h-8 flex items-center justify-center rounded-full bg-blue-600 text-white font-bold ml-2">
                          {initials}
                        </div>
                      )
                    }</>
                  )}
                </div>
              );
            })}
            <div ref={bottomRef} />
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              placeholder="Type a message..."
              className="border p-2 flex-1 rounded shadow-sm"
            />
            <button
              onClick={sendMessage}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Send
            </button>
          </div>
        </div>
      ) : (
        <p className="text-gray-500">Connecting...</p>
      )}
    </div>
  );
}