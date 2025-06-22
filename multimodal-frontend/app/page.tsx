"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [room, setRoom] = useState("");
  const router = useRouter();

  const handleJoin = async () => {
    if (!room) return;
    router.push(`/room/${room}`);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleJoin();
    }
  };

  return (
    <main className="flex flex-col items-center justify-center h-screen p-4">
      <h1 className="text-2xl font-semibold mb-4">Join a LiveKit Room</h1>
      <input
        type="text"
        value={room}
        onChange={(e) => setRoom(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Enter room name"
        className="border p-2 rounded w-full max-w-md mb-4"
      />
      <button
        onClick={handleJoin}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Join Room
      </button>
    </main>
  );
}
