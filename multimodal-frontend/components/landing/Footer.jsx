export default function Footer() {
  return (
    <footer className="bg-[#2a2a2a] text-white text-center py-6">
      <p className="text-sm font-semibold">
        &copy; {new Date().getFullYear()} MultAgent.Ai — All rights reserved.
      </p>
    </footer>
  );
}
