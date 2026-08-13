// import { useState } from "react";
// import { FaGithub, FaInstagram } from "react-icons/fa";

// // Team GitHub profiles
// const teamGithub = [
//   { name: "Anshriti Sharma", url: "https://github.com/anshriti" },
//   { name: "Grishma Dahal", url: "https://github.com/GrishmaDahal" },
//   { name: "Shreeti Shrestha", url: "https://github.com/ShreetiShrestha1" },
//   { name: "Smita Maharjan", url: "https://github.com/Smita0519" },
// ];

// function GithubHoverReveal() {
//   const [hovered, setHovered] = useState(false);

//   return (
//     <div
//       className="relative"
//       onMouseEnter={() => setHovered(true)}
//       onMouseLeave={() => setHovered(false)}
//     >
//       {/* GitHub Icon */}
//       <button
//         className="text-white/70 hover:text-white transition-colors duration-300"
//         aria-label="GitHub"
//       >
//         <FaGithub size={22} />
//       </button>

//       {/* Vertical Dropdown */}
//       <div
//         className={`absolute left-10 top-1/2 -translate-y-1/2 w-56 rounded-xl border border-white/10 bg-[#1A1A1A] shadow-2xl overflow-hidden transition-all duration-300 origin-left z-50 ${
//             hovered
//             ? "opacity-100 scale-100 visible"
//             : "opacity-0 scale-95 invisible"
//         }`}
//         >
//         <div className="px-4 py-3 border-b border-white/10 text-sm font-medium text-white">
//           Team GitHub
//         </div>

//         {teamGithub.map((member) => (
//           <a
//             key={member.name}
//             href={member.url}
//             target="_blank"
//             rel="noopener noreferrer"
//             className="block px-4 py-3 text-sm text-white/70 hover:bg-white/10 hover:text-white transition-colors duration-200"
//           >
//             {member.name}
//           </a>
//         ))}
//       </div>
//     </div>
//   );
// }

// export default function Footer() {
//   return (
//     <footer className="mt-20 bg-[#111111] border-t border-white/10">
//       <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-8">
//         {/* Left Section */}
//         <div className="text-center md:text-left">
//           <h2
//             className="text-2xl md:text-3xl text-white font-semibold tracking-wide mb-3"
//             style={{ fontFamily: "'Playfair Display', serif" }}
//           >
//             StyleMind
//           </h2>

//           <p className="text-sm text-white/55 leading-7 max-w-md">
//             Your AI-powered wardrobe companion that helps you organize your
//             closet, receive personalized outfit recommendations, and discover
//             styles that match your personality and the occasion.
//           </p>
//         </div>

//         {/* Right Section */}
//         <div className="flex items-center gap-7">
//           <GithubHoverReveal />

//           <a
//             href="https://www.instagram.com/grishmaa_daahaall/"
//             target="_blank"
//             rel="noopener noreferrer"
//             aria-label="Instagram"
//             className="text-white/70 hover:text-pink-400 transition-colors duration-300"
//           >
//             <FaInstagram size={22} />
//           </a>
//         </div>
//       </div>

//       {/* Bottom Footer */}
//       <div className="border-t border-white/10">
//         <div className="max-w-6xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-white/40">
//           <p>
//             © {new Date().getFullYear()} <span className="text-white/60">StyleMind</span>. All
//             rights reserved.
//           </p>

//           <p>Designed & Developed as a College Minor Project.</p>
//         </div>
//       </div>
//     </footer>
//   );
// }










// import { useState } from "react";
// import { FaGithub, FaInstagram } from "react-icons/fa";

// const teamGithub = [
//   { name: "Anshriti Sharma", url: "https://github.com/anshriti" },
//   { name: "Grishma Dahal", url: "https://github.com/GrishmaDahal" },
//   { name: "Shreeti Shrestha", url: "https://github.com/ShreetiShrestha1" },
//   { name: "Smita Maharjan", url: "https://github.com/Smita0519" },
// ];

// function GithubHoverReveal() {
//   const [hovered, setHovered] = useState(false);

//   return (
//     <div
//       className="relative flex items-center gap-3"
//       onMouseEnter={() => setHovered(true)}
//       onMouseLeave={() => setHovered(false)}
//     >
//       <button className="text-white/70 hover:text-white transition-colors">
//         <FaGithub size={20} />
//       </button>

//       <div
//         className={`flex items-center gap-2 overflow-hidden transition-all duration-300 ${
//           hovered ? "max-w-[300px] opacity-100" : "max-w-0 opacity-0"
//         }`}
//       >
//         {teamGithub.map((member, i) => (
//           <a
//             key={member.name}
//             href={member.url}
//             target="_blank"
//             rel="noopener noreferrer"
//             title={member.name}
//             className="whitespace-nowrap text-xs px-2.5 py-1 rounded-full bg-white/10 text-white/80 hover:bg-white/20 hover:text-white transition-colors"
//             style={{ transitionDelay: `${i * 40}ms` }}
//           >
//             {member.name.replace(" (You)", "")}
//           </a>
//         ))}
//       </div>
//     </div>
//   );
// }

// export default function Footer() {
//   return (
//     <footer className="bg-[#111111] text-white/70 mt-16">
//       <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
//         <div className="text-center sm:text-left">
//           <h3
//             className="text-white font-semibold text-lg mb-1"
//             style={{ fontFamily: "'Playfair Display', serif" }}
//           >
//             StyleMind
//           </h3>
//           <p className="text-sm max-w-sm">
//             Style isn't found, it's styled — one outfit, one algorithm, one perfect match at a time.
//           </p>
//         </div>

//         <div className="flex items-center gap-6">
//           <GithubHoverReveal />
//           <a
//             href="https://www.instagram.com/grishmaa_daahaall/"
//             target="_blank"
//             rel="noopener noreferrer"
//             className="text-white/70 hover:text-white transition-colors"
//           >
//             <FaInstagram size={20} />
//           </a>
//         </div>
//       </div>

//       <div className="border-t border-white/10 py-4 text-center text-xs text-white/40">
//         © {new Date().getFullYear()} StyleMind. Built as a college minor project.
//       </div>
//     </footer>
//   );
// }





// import { FaGithub, FaLinkedin } from "react-icons/fa";

// // Update with your team's real profile URLs
// const team = [
//   { name: "Anshriti Sharma", github: "https://github.com/anshriti", linkedin: "https://www.linkedin.com/in/anshriti-sharma/" },
//   { name: "Grishma Dahal", github: "https://github.com/GrishmaDahal", linkedin: "https://www.linkedin.com/in/grishma-dahal/" },
//   { name: "Shreeti Shrestha", github: "https://github.com/ShreetiShrestha1", linkedin: "https://www.linkedin.com/in/shreeti-shrestha-246201316/" },
//   { name: "Smita Maharjan", github: "https://github.com/Smita0519", linkedin: "https://www.linkedin.com/in/smita-maharjan/" },
// ];

// export default function Footer() {
//   return (
//     <footer className="mt-20 bg-[#111111] border-t border-white/10">
//       <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col lg:flex-row justify-between gap-10">
//         {/* Brand */}
//         <div className="max-w-md">
//           <h2
//             className="text-3xl text-white font-semibold tracking-wide mb-3"
//             style={{ fontFamily: "'Playfair Display', serif" }}
//           >
//             StyleMind
//           </h2>
//           <p className="text-sm text-white/55 leading-7">
//             Confidence begins with what you wear. Every outfit tells a story, and StyleMind helps you discover the one that's uniquely yours.
//           </p>
//         </div>

//         {/* Team links */}
//         <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 sm:gap-14">
//           <div>
//             <div className="flex items-center gap-2 mb-3">
//               <FaGithub size={18} className="text-white/70" />
//               <h4 className="text-white font-medium text-sm">Team GitHub</h4>
//             </div>
//             <div className="flex flex-col gap-2">
//               {team.map((m) => (
//                 <a
//                   key={m.name}
//                   href={m.github}
//                   target="_blank"
//                   rel="noopener noreferrer"
//                   className="text-sm text-white/60 hover:text-white transition-colors w-fit"
//                 >
//                   {m.name}
//                 </a>
                
//               ))}
//             </div>
//           </div>

//           <div>
//             <div className="flex items-center gap-2 mb-3">
//               <FaLinkedin size={18} className="text-white/70" />
//               <h4 className="text-white font-medium text-sm">Team LinkedIn</h4>
//             </div>
//             <div className="flex flex-col gap-2">
//               {team.map((m) => (
//                 <a
//                   key={m.name}
//                   href={m.linkedin}
//                   target="_blank"
//                   rel="noopener noreferrer"
//                   className="text-sm text-white/60 hover:text-[#5c9dd5] transition-colors w-fit"
//                 >
//                   {m.name}
//                 </a>
//               ))}
//             </div>
//           </div>
//         </div>
//       </div>

//       <div className="border-t border-white/10">
//         <div className="max-w-6xl mx-auto px-6 py-5 flex flex-col sm:flex-row justify-between items-center gap-2 text-xs text-white/40 text-center sm:text-left">
//           <p>© {new Date().getFullYear()} StyleMind. All rights reserved.</p>
//           <p>Designed & Developed as a College Minor Project.</p>
//         </div>
//       </div>
//     </footer>
//   );
// }








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
