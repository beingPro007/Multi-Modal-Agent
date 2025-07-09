"use client";

import { useState, useEffect } from "react";

const topPhrases = [
  "GENERATE LEADS",
  "CUSTOMER SUPPORT",
  "LEGAL HELP",
  "24x7 SERVICE",
];

const bottomPhrases = [
  "WHEN YOU ARE SLEEPING",
  "WITHOUT HIRING STAFF",
  "WHILE YOU RELAX",
  "ON AUTOPILOT",
];

export default function FinalCTA() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % topPhrases.length);
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="px-6 py-12 text-center max-w-4xl mx-auto">
      <h2 className="text-3xl md:text-5xl font-black -skew-x-6 flex flex-col items-center gap-1">
        {/* Single line */}
        <span className="text-black ">HAVE YOU EVER THINK HOW TO</span>

        {/* Animated top line */}
        <div
          className="h-[60px] overflow-hidden text-[#e63946] font-black text-3xl md:text-5xl flex items-center justify-center"
          style={{ minWidth: "280px" }}
        >
          <span
            key={index}
            className="block transition-transform duration-500 ease-in-out animate-slide-in"
          >
            {topPhrases[index]}
          </span>
        </div>

        <div
          className="h-[60px] overflow-hidden text-black font-black text-3xl md:text-5xl flex items-center justify-center"
          style={{ minWidth: "280px" }}
        >
          <span
            key={index + "_bottom"}
            className="block transition-transform duration-500 ease-in-out animate-slide-in"
          >
            {bottomPhrases[index]}
          </span>
        </div>
      </h2>
      <style jsx>{`
        @keyframes slide-in {
          0% {
            transform: translateY(100%);
            opacity: 0;
          }
          100% {
            transform: translateY(0);
            opacity: 1;
          }
        }
        .animate-slide-in {
          animation: slide-in 0.5s ease-out;
        }
      `}</style>
    </section>
  );
}
