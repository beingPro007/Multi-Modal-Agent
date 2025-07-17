"use client"

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function JoinRoomFAB() {
  const [room, setRoom] = useState("");
  const [open, setOpen] = useState(false);
  const router = useRouter();

  const join = () => {
    if (room.trim()) router.push(`/room/${room}`);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2">
      {open && (
        <div className="bg-white p-4 rounded-lg shadow-lg w-80">
          <h4 className="text-lg font-semibold mb-2">🎙️ Join LiveKit Room</h4>
          <input
            type="text"
            value={room}
            onChange={(e) => setRoom(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && join()}
            placeholder="Enter room name"
            className="border border-gray-300 p-2 rounded w-full mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={join}
            className="bg-blue-600 text-white px-4 py-2 rounded w-full hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Join Room
          </button>
        </div>
      )}

      <button
        onClick={() => setOpen((o) => !o)}
        className="bg-blue-600 hover:bg-blue-700 text-white rounded-full p-4 shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label="Open join room panel"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </div>
  );
}
