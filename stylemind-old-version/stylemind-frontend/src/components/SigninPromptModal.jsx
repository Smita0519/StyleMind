// Small popup shown when "Try for Yourself" is clicked on the landing
// page — lets the visitor choose Sign In or Create Account rather than
// navigating away immediately, matching the sketch's "signin popup" note.
import { X } from "lucide-react";
import { Link } from "react-router-dom";

export default function SigninPromptModal({ onClose }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-2xl w-full max-w-sm p-8 text-center relative"
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute top-4 right-4 text-graytext hover:text-ink">
          <X size={18} />
        </button>
        <h3 className="text-xl font-semibold text-ink mb-2" style={{ fontFamily: "'Playfair Display', serif" }}>
          Ready to try StyleMind?
        </h3>
        <p className="text-sm text-graytext mb-6">Sign in to your account, or create one in seconds.</p>
        <div className="flex flex-col gap-3">
          <Link to="/login" className="bg-ink text-white rounded-lg py-2.5 text-sm font-medium hover:opacity-90 transition-opacity">
            Sign In
          </Link>
          <Link to="/signup" className="border border-[#EAEAEA] text-ink rounded-lg py-2.5 text-sm font-medium hover:bg-[#FAF8F5] transition-colors">
            Create Account
          </Link>
        </div>
      </div>
    </div>
  );
}