// components/OutfitPreviewModal.jsx
// Opens when an outfit card is clicked — shows all pieces larger, plus
// the exact preferences (occasion/temp/city/style) it was saved under,
// and lets the user delete it. Mirrors ItemPreviewModal's structure so
// the two feel consistent across the app.
import { X, Trash2, Calendar } from "lucide-react";

export default function OutfitPreviewModal({ outfit, onClose, onDelete }) {
  if (!outfit) return null;
  const pieces = [outfit.top_detail, outfit.bottom_detail, outfit.jacket_detail].filter(Boolean);
  const savedDate = outfit.saved_at ? new Date(outfit.saved_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-lg w-full overflow-hidden max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Header with close + delete buttons */}
        <div className="relative">
          <div className="grid" style={{ gridTemplateColumns: `repeat(${pieces.length}, 1fr)` }}>
            {pieces.map((p, i) => (
              <img
                key={i}
                src={p.processedImageUrl || p.imageUrl}
                alt={p.category}
                className="w-full h-56 object-contain bg-white"
              />
            ))}
          </div>
          <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 flex items-center justify-center shadow-sm">
            <X size={16} />
          </button>
          <button
            onClick={() => onDelete(outfit.id)}
            className="absolute top-3 left-3 w-8 h-8 rounded-full bg-white/90 flex items-center justify-center shadow-sm hover:bg-red-50"
          >
            <Trash2 size={14} className="text-red-500" />
          </button>
        </div>

        {/* Details */}
        <div className="p-5 overflow-y-auto bg-[#F7E6D9]">
          <h3 className="text-lg font-semibold text-ink">{pieces.map((p) => p.category).join(" + ")}</h3>
          {savedDate && (
            <p className="text-xs text-graytext flex items-center gap-1 mt-1 mb-3">
              <Calendar size={12} /> Saved {savedDate}
            </p>
          )}

          {/* Preferences this outfit was generated/saved with */}
          <div className="rounded-xl bg-[#FAF8F5] p-3 grid grid-cols-2 gap-y-2 text-sm">
            <div>
              <p className="text-[10px] text-graytext uppercase font-bold">Occasion</p>
              <p className="text-ink">{outfit.occasion || "—"}</p>
            </div>
            <div>
              <p className="text-[10px] text-graytext uppercase font-bold">Style</p>
              <p className="text-ink capitalize">{outfit.style_preference || "—"}</p>
            </div>
            {/* ===================== CHANGE START =====================
                CHANGED — this used to show EITHER location OR temperature
                (whichever existed), never both. Now it shows temperature
                AND location together, since the outfit card grid only has
                room for one badge but the full preview does. */}
            <div>
              <p className="text-[10px] text-graytext uppercase font-bold">Weather</p>
              <p className="text-ink">
                {outfit.temp_c != null ? `${Math.round(outfit.temp_c)}°C` : ""}
                {outfit.temp_c != null && outfit.location_name ? " · " : ""}
                {outfit.location_name ? [outfit.location_name, outfit.region, outfit.country].filter(Boolean).join(", ") : ""}
                {outfit.temp_c == null && !outfit.location_name ? "—" : ""}
              </p>
            </div>
            {/* ===================== CHANGE END ===================== */}
            <div>
              <p className="text-[10px] text-graytext uppercase font-bold">Pieces</p>
              <p className="text-ink">{pieces.length}</p>
            </div>
          </div>

          {/* Individual piece breakdown */}
          <div className="mt-4 space-y-2">
            {pieces.map((p, i) => (
              <div key={i} className="flex items-center gap-3 rounded-lg border border-[#EAEAEA] p-2">
                <img src={p.processedImageUrl || p.imageUrl} alt={p.category} className="w-10 h-10 object-contain bg-[#FAF8F5] rounded-md flex-shrink-0" />
                <div className="text-xs">
                  <p className="text-ink font-medium">{p.category}</p>
                  <p className="text-graytext">{p.texture} • {p.season}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}