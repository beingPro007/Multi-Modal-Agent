import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="w-full bg-transparent py-4">
      <div className="max-w-6xl mx-auto flex justify-between items-center px-6">
        <h1 className="text-4xl md:text-6xl font-black -skew-x-12">
          AIVENGERS
        </h1>
        <Button className="bg-[#f4ce14] text-black font-bold px-6 py-2 -skew-x-12 text-lg">
          GET STARTED
        </Button>
      </div>
    </header>
  );
}
