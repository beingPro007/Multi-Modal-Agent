import { Card } from "@/components/ui/card";
import Image from "next/image";

export default function AgentShowcase() {
  return (
    <section className="relative max-w-4xl mx-auto md:h-[420px] h-[340px] flex flex-col items-center justify-center mt-0">
      <div className="w-full flex flex-col items-center mb-0">
        <h2 className="text-xl md:text-2xl font-bold text-[#7b4019] tracking-wide mb-0 text-center -skew-x-6 leading-tight">Your Business</h2>
        <span className="text-2xl md:text-3xl font-black text-[#2a9d8f] text-center -skew-x-6 leading-tight">Our Agents</span>
      </div>
      {/* Desktop layout */}
      <div className="hidden md:block w-full h-full relative">
        <Card className="w-64 h-80 absolute left-0 top-0 overflow-hidden shadow-xl p-0">
          <div className="relative w-full h-full">
            <Image
              src="/Lead.webp"
              alt="Lead"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 256px"
              quality={70}
            />
          </div>
        </Card>
        <Card className="w-64 h-80 absolute left-1/2 transform -translate-x-1/2 top-16 overflow-hidden shadow-xl p-0">
          <div className="relative w-full h-full">
            <Image
              src="/Joana.webp"
              alt="JOANA"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 256px"
              priority
              quality={75}
            />
          </div>
        </Card>
        <Card className="w-64 h-80 absolute right-0 top-4 overflow-hidden shadow-xl p-0">
          <div className="relative w-full h-full">
            <Image
              src="/Anne.webp"
              alt="ANNE"
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, 256px"
              quality={70}
            />
          </div>
        </Card>
      </div>
      {/* Mobile layout */}
      <div className="md:hidden flex w-full h-full gap-3 justify-center items-end">
        <Card className="w-20 h-28 overflow-hidden shadow-xl p-0 flex-shrink-0">
          <div className="relative w-full h-full">
            <Image
              src="/Lead.webp"
              alt="Lead"
              fill
              className="object-cover"
              sizes="100vw"
              quality={70}
            />
          </div>
        </Card>
        <Card className="flex-1 h-36 overflow-hidden shadow-xl p-0">
          <div className="relative w-full h-full">
            <Image
              src="/Joana.webp"
              alt="JOANA"
              fill
              className="object-cover"
              sizes="100vw"
              priority
              quality={75}
            />
          </div>
        </Card>
        <Card className="w-20 h-28 overflow-hidden shadow-xl p-0 flex-shrink-0">
          <div className="relative w-full h-full">
            <Image
              src="/Anne.webp"
              alt="ANNE"
              fill
              className="object-cover"
              sizes="100vw"
              quality={70}
            />
          </div>
        </Card>
      </div>
    </section>
  );
}
