import { useState, useRef, useEffect } from "react";
import { FaGithub, FaLinkedin } from "react-icons/fa";

// Update with your team's real profile URLs
const team = [
  {
    name: "Anshriti Sharma",
    github: "https://github.com/anshriti",
    linkedin: "https://www.linkedin.com/in/anshriti-sharma/",
  },
  {
    name: "Grishma Dahal",
    github: "https://github.com/GrishmaDahal",
    linkedin: "https://www.linkedin.com/in/grishma-dahal/",
  },
  {
    name: "Shreeti Shrestha",
    github: "https://github.com/ShreetiShrestha1",
    linkedin: "https://www.linkedin.com/in/shreeti-shrestha-246201316/",
  },
  {
    name: "Smita Maharjan",
    github: "https://github.com/Smita0519",
    linkedin: "https://www.linkedin.com/in/smita-maharjan/",
  },
];

function TeamDropdown({
  icon,
  label,
  hrefKey,
  hoverColorClass,
  verticalOffsetClass = "top-1/2 -translate-y-1/2",
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef(null);

  // Close the dropdown when tapping/clicking anywhere outside it
  useEffect(() => {
    function handleClickOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, []);

  return (
    <div ref={containerRef} className="relative group w-full sm:w-auto">
      <div
        className="flex items-center gap-2 cursor-pointer sm:cursor-default"
        onClick={() => setOpen((prev) => !prev)}
      >
        {icon}
        <h4 className="text-white font-medium text-sm whitespace-nowrap">
          {label}
        </h4>
      </div>

      {/*
        Visibility strategy:
        - Below sm (mobile): visibility is driven ONLY by the `open` state,
          toggled by tapping the trigger (see onClick above).
        - sm and up (desktop): the mobile `open` classes are explicitly
          overridden back to hidden (sm:opacity-0 sm:invisible ...), and
          visibility is driven ONLY by group-hover (sm:group-hover:*).
          So clicking does nothing on desktop, only hovering opens it.
      */}
      <div
        className={`
          absolute z-50
          left-full
          ${verticalOffsetClass}
          ml-3
          w-max
          max-w-[52vw] sm:max-w-none sm:w-56 lg:w-60
          rounded-xl
          border border-white/10
          bg-[#1b1b1b]
          shadow-2xl
          overflow-hidden
          transition-all duration-300
          ${
            open
              ? "opacity-100 visible translate-x-0"
              : "opacity-0 invisible translate-x-1"
          }
          sm:opacity-0 sm:invisible sm:translate-x-1
          sm:group-hover:opacity-100
          sm:group-hover:visible
          sm:group-hover:translate-x-0
        `}
      >
        {team.map((member) => (
          <a
            key={member.name}
            href={member[hrefKey]}
            target="_blank"
            rel="noopener noreferrer"
            className={`block px-4 py-3 text-sm text-white/70 hover:bg-white/10 ${hoverColorClass} transition-colors whitespace-nowrap`}
          >
            {member.name}
          </a>
        ))}
      </div>
    </div>
  );
}

export default function Footer() {
  return (
    <footer className="mt-20 bg-[#111111] border-t border-white/10">
      <div
        className="
          max-w-6xl mx-auto px-6 py-20
          flex flex-col lg:flex-row
          justify-between
          gap-10
        "
      >
        {/* Brand */}
        <div className="max-w-md">
          <h2
            className="text-2xl sm:text-3xl text-white font-semibold tracking-wide mb-3"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            StyleMind
          </h2>

          <p className="text-sm text-white/55 leading-7">
            Confidence begins with what you wear. Every outfit tells a story,
            and StyleMind helps you discover the one that's uniquely yours.
          </p>
        </div>

        {/* Team Links */}
        <div
          className="
            flex flex-col sm:flex-row lg:flex-col
            gap-6 sm:gap-10 lg:gap-8 pt-8
            w-full sm:w-auto
            pr-[52vw] sm:pr-24 lg:pr-28
          "
        >
          <TeamDropdown
            icon={<FaGithub size={18} className="text-white/70 shrink-0" />}
            label="Team GitHub"
            hrefKey="github"
            hoverColorClass="hover:text-white"
          />

          <TeamDropdown
            icon={<FaLinkedin size={18} className="text-white/70 shrink-0" />}
            label="Team LinkedIn"
            hrefKey="linkedin"
            hoverColorClass="hover:text-[#5c9dd5]"
          />
        </div>
      </div>

      {/* Bottom */}
      <div className="border-t border-white/10">
        <div
          className="
            max-w-6xl mx-auto px-6 py-5
            flex flex-col sm:flex-row
            justify-between items-center
            gap-2
            text-xs text-white/40
            text-center sm:text-left
          "
        >
          <p>© {new Date().getFullYear()} StyleMind. All rights reserved.</p>
          <p>Designed & Developed as a College Minor Project.</p>
        </div>
      </div>
    </footer>
  );
}
