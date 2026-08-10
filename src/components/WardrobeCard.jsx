import { Heart, Trash2 } from "lucide-react";

export default function WardrobeCard({ item, onDelete, isFavorite, onToggleFavorite, onOpen }) {
  return (
    <div className="bg-white border border-[#CFA187] rounded-xl overflow-hidden hover:shadow-md transition-shadow group">
      <div
        className="relative aspect-square bg-[#F3E4E8] flex items-center justify-center cursor-pointer"
        onClick={() => onOpen(item)}
      >
        {(item.processedImageUrl || item.imageUrl) && (
          // object-contain (not object-cover) so the whole garment is
          // visible instead of being cropped to fill the square thumbnail
          <img src={item.processedImageUrl || item.imageUrl} alt={item.category} className="w-full h-full object-contain p-2" />
        )}

        {/* ===================== CHANGE START ===================== */}
        {/* NEW — overlay shown while this item's ML classification is
            still running in the background (upload now returns
            immediately instead of waiting for the full pipeline). Sits
            inside the same `relative` container as the image, so it
            covers exactly the thumbnail area. z-10 keeps it above the
            image but the favorite/delete buttons (below) still render
            after this in the DOM, so they stay clickable on top of it. */}
        {item.status === "processing" && (
          <div className="absolute inset-0 bg-white/80 flex flex-col items-center justify-center gap-2 z-10">
            <div className="w-6 h-6 border-2 border-ink border-t-transparent rounded-full animate-spin" />
            <span className="text-xs text-graytext">Processing…</span>
          </div>
        )}
        {item.status === "failed" && (
          <div className="absolute inset-0 bg-white/90 flex flex-col items-center justify-center gap-1 z-10 px-3 text-center">
            <span className="text-xs text-red-500 font-medium">Processing failed</span>
            <span className="text-[10px] text-graytext">Try deleting and re-uploading</span>
          </div>
        )}
        {/* ===================== CHANGE END ===================== */}

        <button
          onClick={(e) => { e.stopPropagation(); onToggleFavorite(item.id); }}
          className="absolute top-2.5 right-2.5 w-7 h-7 rounded-full bg-white/90 flex items-center justify-center hover:bg-white transition-colors z-20"
        >
          <Heart size={14} className={isFavorite ? "fill-red-500 text-red-500" : "text-graytext"} />
        </button>

        <button
          onClick={(e) => { e.stopPropagation(); onDelete(item.id); }}
          className="absolute top-2.5 left-2.5 w-7 h-7 rounded-full bg-white/90 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 z-20"
        >
          <Trash2 size={13} className="text-red-500" />
        </button>
      </div>

      <div className="pt-3 pb-1 border-t border-t-[#CFA187] bg-[#F7E6D9]">
        <div className="text-xs sm:text-sm text-center lg:text-base text-ink font-medium">{item.category}</div>
        <div className="text-[10px] sm:text-xs text-center lg:text-sm text-graytext">{item.texture} • {item.season}</div>
      </div>
    </div>
  );
}