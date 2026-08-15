// A simple full-screen image viewer — click any photo thumbnail to see
// it enlarged. Reused by both the Navbar dropdown and ProfileModal so
// there's one consistent "view full size" experience across the app.
import { X } from "lucide-react";

export default function ImageLightbox({ src, onClose }) {
  if (!src) return null;
  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-[60] p-6"
      onClick={onClose}
    >
      <button onClick={onClose} className="absolute top-5 right-5 text-white/80 hover:text-white">
        <X size={26} />
      </button>
      <img
        src={src}
        alt="Full size"
        className="max-w-full max-h-full rounded-2xl object-contain"
        onClick={(e) => e.stopPropagation()} // clicking the image itself shouldn't close it
      />
    </div>
  );
}