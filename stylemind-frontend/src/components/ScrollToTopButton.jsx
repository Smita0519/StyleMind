// components/ScrollToTopButton.jsx
// A small floating button that appears once the user has scrolled down a
// bit, and smooth-scrolls the page back to the top when clicked.
import { useState, useEffect } from "react";
import { ArrowUp } from "lucide-react";

export default function ScrollToTopButton() {
  const [visible, setVisible] = useState(false); // only show once scrolled down

  useEffect(() => {
    function handleScroll() {
      setVisible(window.scrollY > 300); // appears after scrolling ~300px down
    }
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll); // cleanup on unmount
  }, []);

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (!visible) return null; // render nothing while near the top of the page

  return (
    <button
      onClick={scrollToTop}
      aria-label="Scroll to top"
      // bottom-24 (not bottom-6) so it sits stacked above the FloatingChatbot
      // bubble (which is at bottom-6 right-6, 56px tall) instead of overlapping it
      className="fixed bottom-24 right-6 w-11 h-11 rounded-full bg-white border border-[#EAD9CF] shadow-lg flex items-center justify-center text-[#A66F79] hover:bg-[#FBF1EC] hover:scale-105 transition-all z-40"
    >
      <ArrowUp size={18} />
    </button>
  );
}