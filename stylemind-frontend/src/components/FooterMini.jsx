import { FaGithub, FaLinkedin } from "react-icons/fa";

// Points to the project's main repo / team lead's profile — condensed
// version doesn't list all 4 members individually, unlike the full Footer.
const projectGithub = "https://github.com/Smita0519/StyleMind";
const projectLinkedin = "https://linkedin.com/";

export default function FooterMini() {
  return (
    <footer className="mt-12 bg-[#111111] border-t border-white/10">
      <div className="max-w-6xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-white/50">
        <p className="text-center sm:text-left">
          © {new Date().getFullYear()} <span className="text-white/70 font-medium">StyleMind</span> College Minor Project
        </p>
        <div className="flex items-center gap-4">
          <a href={projectGithub} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">
            <FaGithub size={16} />
          </a>
          <a href={projectLinkedin} target="_blank" rel="noopener noreferrer" className="hover:text-[#5c9dd5] transition-colors">
            <FaLinkedin size={16} />
          </a>
        </div>
      </div>
    </footer>
  );
}