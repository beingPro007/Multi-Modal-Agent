import { Card } from "@/components/ui/card";
import Image from "next/image";

export default function AgentShowcase() {
  return (
    <section className="relative max-w-4xl mx-auto h-[420px]">
      <Card className="w-64 h-80 absolute left-0 top-0 overflow-hidden shadow-xl">
        <Image src="/Lead.webp" alt="Lead" fill className="object-cover" priority/>
      </Card>

      <Card className="w-64 h-80 absolute left-1/2 transform -translate-x-1/2 top-16 overflow-hidden shadow-xl">
        <Image src="/Joana.webp" alt="JOANA" fill className="object-cover" priority/>
      </Card>

      <Card className="w-64 h-80 absolute right-0 top-4 overflow-hidden shadow-xl">
        <Image src="/Anne.webp" alt="ANNE" fill className="object-cover" priority/>
      </Card>
    </section>
  );
}
