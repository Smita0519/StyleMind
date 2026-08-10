// components/OutfitPieceSlider.jsx
// A small horizontal stepper embedded inside an outfit card/modal — shows
// ONE piece (top/bottom/jacket) at a time instead of squeezing all
// pieces side by side, with left/right arrows to step through them.
import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function OutfitPieceSlider({ pieces, imgClassName = "" }) {
  const [index, setIndex] = useState(0);
  if (pieces.length === 0) return null;
  const piece = pieces[index];

  // stopPropagation on both — without it, clicking an arrow inside a grid
  // card would also trigger the card's own onClick (opening the full preview)
  function goNext(e) {
    e.stopPropagation();
    setIndex((i) => (i + 1) % pieces.length);
  }
  function goPrev(e) {
    e.stopPropagation();
    setIndex((i) => (i - 1 + pieces.length) % pieces.length);
  }

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-white">
      <img
        src={piece.processedImageUrl || piece.imageUrl}
        alt={piece.category}
        className={`object-contain ${imgClassName}`}
      />

      {/* ===================== CHANGE START ===================== */}
      {/* CHANGED — category label moved to the top-RIGHT (was top-left),
          using the site's decorative serif font instead of the default
          sans-serif, to match headings elsewhere (e.g. "Recommended for
          you", "My Wardrobe"). */}
      <span
        className="absolute top-2 right-2 text-xs font-medium bg-[#F7E6D9] text-ink px-2.5 py-1 rounded-full shadow-sm"
        style={{ fontFamily: "'Playfair Display', serif" }}
      >
        {piece.category}
      </span>
      {/* ===================== CHANGE END ===================== */}

      {/* Only show navigation if there's more than one piece to step through */}
      {pieces.length > 1 && (
        <>
          {/* ===================== CHANGE START ===================== */}
          {/* CHANGED — was a vertical up/down stack on the right; now
              left/right arrows on opposite edges (horizontal slider) */}
          {/* <button
            onClick={goPrev}
            aria-label="Previous piece"
            className="absolute left-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/90 shadow-sm flex items-center justify-center hover:bg-white transition-colors"
          >
            <ChevronLeft size={15} className="text-ink" />
          </button> */}
          <button
            onClick={goNext}
            aria-label="Next piece"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 w-7 h-7 rounded-full bg-white/90 shadow-sm flex items-center justify-center hover:bg-white transition-colors"
          >
            <ChevronRight size={15} className="text-ink" />
          </button>
          {/* ===================== CHANGE END ===================== */}

          {/* Position dots at the bottom, one per piece */}
          <div className="absolute bottom-1.5 left-0 right-0 flex justify-center gap-1">
            {pieces.map((_, i) => (
              <span key={i} className={`w-1.5 h-1.5 rounded-full transition-colors ${i === index ? "bg-ink" : "bg-[#EAEAEA]"}`} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}