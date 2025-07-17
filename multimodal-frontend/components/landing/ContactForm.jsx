"use client";

import { useState } from "react";

export default function ContactForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatus(null);

    try {
      const res = await fetch("/api/send-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, email, message }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus("success");
        setName("");
        setEmail("");
        setMessage("");
      } else {
        setStatus("error");
      }
    } catch (err) {
      console.error("Email send error:", err);
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-[#f8f3e9] text-black px-6 pt-12 pb-16">
      <div className="max-w-4xl mx-auto text-center mb-10">
        <h2
          className="text-4xl md:text-5xl font-black -skew-x-6"
          style={{ fontFamily: "'Bangers', sans-serif" }}
        >
          WANT TO WORK WITH OUR AI AGENTS?
        </h2>
        <p className="text-lg md:text-xl mt-2 -skew-x-3 text-[#444]">
          Reach out and we’ll get back to you faster than a bot.
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="max-w-3xl mx-auto grid md:grid-cols-2 gap-6 text-left"
      >
        <div>
          <label className="block font-bold mb-1">Your Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Enter your name"
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
            required
          />
        </div>

        <div>
          <label className="block font-bold mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
            required
          />
        </div>

        <div className="md:col-span-2">
          <label className="block font-bold mb-1">Message</label>
          <textarea
            rows="4"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message here..."
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
            required
          ></textarea>
        </div>

        <div className="md:col-span-2 text-center">
          <button
            type="submit"
            className="px-8 py-3 bg-[#e63946] text-white text-lg font-black rounded -skew-x-6 hover:bg-[#c5303c] transition disabled:opacity-60"
            disabled={loading}
          >
            {loading ? "SENDING..." : "SEND MESSAGE"}
          </button>

          {status === "success" && (
            <p className="text-green-600 mt-4 font-semibold">
              ✅ Message sent successfully!
            </p>
          )}
          {status === "error" && (
            <p className="text-red-600 mt-4 font-semibold">
              ❌ Failed to send message. Try again.
            </p>
          )}
        </div>
      </form>
    </section>
  );
}
