// components/landing/JoinRoomFAB.jsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function JoinRoomFAB() {
  const [room, setRoom] = useState("");
  const [showJoinBox, setShowJoinBox] = useState(false);
  const router = useRouter();

  const handleJoin = () => {
    if (!room.trim()) return;
    router.push(`/room/${room}`);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleJoin();
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2">
      {showJoinBox && (
        <div className="bg-white p-4 rounded-lg shadow-lg w-72">
          <h4 className="text-lg font-semibold mb-2">Join LiveKit Room</h4>
          <input
            type="text"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter room name"
            className="border p-2 rounded w-full mb-2"
          />
          <button
            onClick={handleJoin}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 w-full"
          >
            Join Room
          </button>
        </div>
      )}
      <button
        onClick={() => setShowJoinBox((prev) => !prev)}
        className="bg-blue-600 text-white rounded-full p-4 shadow-lg hover:bg-blue-700"
      >
        🤖
      </button>
    </div>
  );
}
