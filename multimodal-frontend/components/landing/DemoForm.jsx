"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Image from "next/image";

const AGENTS = [
  { name: "Joana", color: "#e63946" },
  { name: "Anne", color: "#2a9d8f" },
  { name: "Lead", color: "#f4ce14" },
  { name: "Ronald", color: "#e63946" },
];

export default function DemoForm() {
  const [selectedAgent, setSelectedAgent] = useState("");
  const [name, setName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [loading, setLoading] = useState(false);
  const [responseMessage, setResponseMessage] = useState("");
  const [isError, setIsError] = useState(false);

  // Logic strictly matching the HTML
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !phoneNumber) return;

    setLoading(true);
    setResponseMessage("");

    const payload = {
      room: name,
      phone_number: phoneNumber,
    };

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_DISPATCH_URL}/start_call`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.error || res.statusText);
      }

      setIsError(false);
      setResponseMessage(
        "✅ Call started!"
      );
    } catch (err) {
      setIsError(true);
      setResponseMessage("❌ Failed to start call: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="px-4 md:px-8 py-12 bg-[#7b4019] text-white">
      <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-10 items-center bg-white rounded-2xl p-8 shadow-xl text-black">
        {/* Form Section */}
        <form className="space-y-5" onSubmit={handleSubmit}>
          <h3 className="text-3xl font-black text-[#7b4019] -skew-x-6">
            TRY DEMO
          </h3>

          <div>
            <label className="block font-bold mb-1 text-sm">Name</label>
            <Input
              className="w-full p-3 rounded-md bg-gray-100 text-black"
              placeholder="Your Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block font-bold mb-1 text-sm">Phone Number</label>
            <Input
              className="w-full p-3 rounded-md bg-gray-100 text-black"
              placeholder="+91..."
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              pattern="^\+\d{1,3}\s?\d{4,14}(?:x.+)?$"
              title="Include country code, e.g. +91 9876543210"
              required
            />
          </div>

          <Button
            type="submit"
            className="w-full py-3 bg-[#e63946] text-white font-black text-lg -skew-x-6 mt-4"
            disabled={loading}
          >
            {loading ? "Starting..." : "GET CALL"}
          </Button>

          {responseMessage && (
            <div
              className={`mt-4 p-3 rounded-md text-sm ${
                isError
                  ? "bg-red-100 text-red-800"
                  : "bg-green-100 text-green-800"
              }`}
            >
              {responseMessage}
            </div>
          )}
        </form>

        {/* Agent Selection (frontend only, no backend impact) */}
        <div>
          <h4 className="text-lg font-bold text-center mb-5 text-[#7b4019]">
            Choose Agent
          </h4>
          <div className="grid grid-cols-2 gap-x-0 gap-y-12 justify-items-center">
            {AGENTS.map((agent) => (
              <button
                key={agent.name}
                type="button"
                onClick={() => setSelectedAgent(agent.name)}
                className={`w-24 h-24 md:w-28 md:h-28 rounded-xl overflow-hidden relative shadow-md transition-all duration-200 outline-none ${
                  selectedAgent === agent.name
                    ? "ring-4 ring-[#7b4019] scale-105"
                    : "opacity-90 hover:opacity-100"
                }`}
                style={{ backgroundColor: agent.color }}
              >
                <Image
                  src={`/${agent.name}.webp`}
                  alt={agent.name}
                  fill
                  className="object-cover"
                />
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
