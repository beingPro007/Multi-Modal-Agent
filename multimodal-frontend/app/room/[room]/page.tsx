"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { LiveKitRoom, useDataChannel } from "@livekit/components-react";

function InnerChatUI() {
  const { message: incoming, send } = useDataChannel<string>(
    "lk.chat",
    (msg) => {} 
  );
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState<any[]>([]);
  const [participantInfo, setParticipantInfo] = useState<Record<string, any>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!incoming) return;
    const { from, payload } = incoming;
    if (!from) return;
    const text = new TextDecoder().decode(payload);
    const identity = from.identity;
    const meta = from.metadata ? JSON.parse(from.metadata) : {};

    setChatLog((prev) => [
      ...prev.filter((m) => m.identity !== identity),
      {
        sender: meta.displayName || identity,
        identity,
        avatar: meta.avatar || null,
        text,
      },
    ]);
    setParticipantInfo((prev) => ({
      ...prev,
      [identity]: {
        displayName: meta.displayName || identity,
        avatar: meta.avatar || null,
      },
    }));
  }, [incoming]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const sendMessage = () => {
    if (!message.trim()) return;
    send(new TextEncoder().encode(message), { reliable: true });
    setChatLog((prev) => [
      ...prev,
      {
        sender: "You",
        identity: "<local>",
        avatar: participantInfo["<local>"]?.avatar || null,
        text: message,
      },
    ]);
    setMessage("");
  };

  return (
    <div className="flex-1 flex flex-col space-y-4 overflow-hidden">
      <div className="flex-1 overflow-y-auto border p-2 rounded bg-blue-400 flex flex-col space-y-2">
        {chatLog.map((msg, i) => {
          const isSelf = msg.sender === "You";
          const initials = msg.sender.charAt(0).toUpperCase();
          return (
            <div key={i} className={`flex items-start ${isSelf ? "justify-end" : "justify-start"}`}>
              {!isSelf && (
                <>
                  {msg.avatar ? (
                    <img
                      src={msg.avatar}
                      alt={msg.sender}
                      className="w-8 h-8 rounded-full object-cover mr-2"
                    />
                  ) : (
                    <div className="w-8 h-8 flex items-center justify-center rounded-full bg-gray-400 text-white font-bold mr-2">
                      {initials}
                    </div>
                  )}
                </>
              )}
              <div className={`p-3 rounded-lg max-w-xs text-sm leading-tight ${
                  isSelf
                    ? "bg-blue-500 text-white"
                    : "bg-white text-gray-900 border border-gray-200"
                }`}>
                {!isSelf && (
                  <p className="text-xs text-gray-500 mb-1">{msg.sender}</p>
                )}
                <p>{msg.text}</p>
              </div>
              {isSelf && (
                <>
                  {msg.avatar ? (
                    <img
                      src={msg.avatar}
                      alt={msg.sender}
                      className="w-8 h-8 rounded-full object-cover ml-2"
                    />
                  ) : (
                    <div className="w-8 h-8 flex items-center justify-center rounded-full bg-blue-600 text-white font-bold ml-2">
                      {initials}
                    </div>
                  )}
                </>
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
  );
}

export default function RoomPage() {
  const { room: roomName } = useParams();
  const [token, setToken] = useState<string>();

  useEffect(() => {
    if (!roomName) return;
    fetch(`/api/token?room=${roomName}`)
      .then((res) => res.json())
      .then((data) => setToken(data.token));
  }, [roomName]);

  return (
    <LiveKitRoom
      serverUrl={process.env.NEXT_PUBLIC_LIVEKIT_URL}
      token={token}
      connect={!!token}
    >
      <div className="p-4 max-w-4xl mx-auto h-screen flex flex-col">
        <h1 className="text-xl sm:text-2xl font-bold mb-4">Room: {roomName}</h1>
        {token ? <InnerChatUI /> : <p className="text-gray-500">Connecting...</p>}
      </div>
    </LiveKitRoom>
  );
}
