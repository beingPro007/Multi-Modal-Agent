import Header from "@/components/landing/Header";
import AgentShowcase from "@/components/landing/AgentShowcase";
import DemoForm from "@/components/landing/DemoForm";
import JoinRoomFAB from "@/components/landing/JoinRoomFAB";
import FinalCTA from "@/components/landing/FinalCTA";
import ContactForm from "@/components/landing/ContactForm";
import Footer from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div
      className="min-h-screen flex flex-col bg-[#f8f3e9] text-black"
      style={{ fontFamily: "'Bangers', sans-serif" }}
    >
      <Header />
      <main className="flex-grow">
        <AgentShowcase />
        <section className="text-center py-10 max-w-4xl mx-auto">
          <h2 className="text-3xl md:text-5xl font-black -skew-x-6">
            SKY ROCKETS YOUR BUSINESS WITH AI AGENTS
          </h2>
          <h3 className="text-xl md:text-3xl font-bold text-[#2a9d8f] -skew-x-6">
            AGENTS WHO LOVE OVERTIME
          </h3>
        </section>
        <DemoForm />
        <FinalCTA />
        <ContactForm />
      </main>
      <Footer />
    </div>
  );
}
