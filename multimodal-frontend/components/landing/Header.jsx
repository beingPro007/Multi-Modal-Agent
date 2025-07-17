import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="w-full bg-transparent py-4">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center px-4 md:px-6 gap-3 md:gap-0">
        <h1 className="text-3xl sm:text-4xl md:text-6xl font-black -skew-x-12 text-center md:text-left">
          AIVENGERS
        </h1>
        <Button className="bg-[#f4ce14] text-black font-bold px-4 py-2 md:px-6 md:py-2 -skew-x-12 text-base md:text-lg w-full md:w-auto">
          GET STARTED
        </Button>
      </div>
    </header>
  );
}
