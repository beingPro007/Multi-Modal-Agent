// components/ContactForm.jsx

"use client";

export default function ContactForm() {
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

      <form className="max-w-3xl mx-auto grid md:grid-cols-2 gap-6 text-left">
        <div>
          <label className="block font-bold mb-1">Your Name</label>
          <input
            type="text"
            placeholder="Enter your name"
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
          />
        </div>

        <div>
          <label className="block font-bold mb-1">Email</label>
          <input
            type="email"
            placeholder="you@example.com"
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
          />
        </div>

        <div className="md:col-span-2">
          <label className="block font-bold mb-1">Message</label>
          <textarea
            rows="4"
            placeholder="Type your message here..."
            className="w-full p-3 rounded bg-white border border-gray-300 text-black"
          ></textarea>
        </div>

        <div className="md:col-span-2 text-center">
          <button
            type="submit"
            className="px-8 py-3 bg-[#e63946] text-white text-lg font-black rounded -skew-x-6 hover:bg-[#c5303c] transition"
          >
            SEND MESSAGE
          </button>
        </div>
      </form>
    </section>
  );
}
