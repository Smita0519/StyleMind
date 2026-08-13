import { X } from "lucide-react";

export default function ItemPreviewModal({ item, onClose }) {
  if (!item) return null;
  // CHANGED — now a real backend-computed value (from getWardrobe()'s
  // response), not a disconnected localStorage counter
  const count = item.selection_count ?? 0;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-md w-full overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="relative">
          <button onClick={onClose} className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 flex items-center justify-center z-10">
            <X size={16} />
          </button>
          {(item.processedImageUrl || item.imageUrl) && (
            <img src={item.processedImageUrl || item.imageUrl} alt={item.category} className="w-full max-h-[70vh] object-contain bg-[#F3E4E8]" />
          )}
        </div>

        <div className="p-5 bg-[#F7E6D9]">
          <h3 className="text-lg font-semibold text-ink">{item.category}</h3>
          <p className="text-sm text-graytext mb-3">{item.texture} • {item.season}</p>

          {item.dominant_colors?.length > 0 && (
            <div className="flex gap-1 mb-4">
              {item.dominant_colors.map((c, i) => (
                <div key={i} className="w-5 h-5 rounded-full border border-[#EAEAEA]" style={{ backgroundColor: c }} />
              ))}
            </div>
          )}

          <div className="rounded-xl bg-[#FAF8F5] p-3 text-sm text-ink">
            Selected as final outfit <span className="font-semibold">{count}</span> time{count === 1 ? "" : "s"}
          </div>
        </div>
      </div>
    </div>
  );
}