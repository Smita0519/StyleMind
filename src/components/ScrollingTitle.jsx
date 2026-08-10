import { useEffect, useRef, useState } from "react";

export default function ScrollingTitle({ children }) {
  const containerRef = useRef(null);
  const scrollRef = useRef(null);

  const [overflow, setOverflow] = useState(false);
  const [hovered, setHovered] = useState(false);

  const timeoutRef = useRef(null);

  useEffect(() => {
    const checkOverflow = () => {
      if (!containerRef.current || !scrollRef.current) return;

      setOverflow(
        scrollRef.current.scrollWidth >
          containerRef.current.clientWidth
      );

      scrollRef.current.style.transform = "translateX(0)";
      scrollRef.current.style.transition = "none";
    };

    checkOverflow();

    const observer = new ResizeObserver(checkOverflow);

    observer.observe(containerRef.current);
    observer.observe(scrollRef.current);

    window.addEventListener("resize", checkOverflow);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", checkOverflow);
      clearTimeout(timeoutRef.current);
    };
  }, [children]);

  const handleEnter = () => {
    setHovered(true);

    if (!overflow) return;

    timeoutRef.current = setTimeout(() => {
      if (!containerRef.current || !scrollRef.current) return;

      const distance =
        scrollRef.current.scrollWidth -
        containerRef.current.clientWidth;

      const duration = Math.max(3, distance / 35);

      scrollRef.current.style.transition = `transform ${duration}s linear`;
      scrollRef.current.style.transform = `translateX(-${distance}px)`;
    }, 700);
  };

  const handleLeave = () => {
    setHovered(false);

    clearTimeout(timeoutRef.current);

    if (!scrollRef.current) return;

    scrollRef.current.style.transition = "transform .3s ease";
    scrollRef.current.style.transform = "translateX(0)";
  };

  return (
    <div
      ref={containerRef}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      className="relative flex-1 min-w-0 overflow-hidden h-5"
    >
      {/* Normal state with ... */}
      <span
        className={`absolute inset-0 block truncate ${
          hovered && overflow ? "opacity-0" : "opacity-100"
        }`}
      >
        {children}
      </span>

      {/* Hover scrolling */}
      <span
        ref={scrollRef}
        className={`absolute inset-0 whitespace-nowrap ${
          hovered && overflow ? "opacity-100" : "opacity-0"
        }`}
      >
        {children}
      </span>
    </div>
  );
}