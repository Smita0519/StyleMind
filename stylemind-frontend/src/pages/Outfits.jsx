// pages/Outfits.jsx
// Shows every outfit the user has saved from the Recommendations page,
// with occasion filtering, click-to-preview, and delete.
import { useState, useMemo, useEffect } from "react";
import { Trash2 } from "lucide-react";
import Navbar from "../components/Navbar";
import FooterMini from "../components/FooterMini";
import OutfitPreviewModal from "../components/OutfitPreviewModal";
import OutfitPieceSlider from "../components/OutfitPieceSlider";
import { occasionOptions } from "../mock/outfits";
import { getOutfits, deleteOutfit } from "../lib/api";
import ConfirmDialog from "../components/ConfirmDialog";

export default function Outfits({ user, onLogout }) {
  const [outfits, setOutfits] = useState([]);
  const [filter, setFilter] = useState("All");
  const [previewOutfit, setPreviewOutfit] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  useEffect(() => {
    getOutfits().then(setOutfits).catch((err) => console.error("Failed to load outfits:", err));
  }, []);

  const filtered = useMemo(() => {
    if (filter === "All") return outfits;
    return outfits.filter((o) => o.occasion === filter);
  }, [outfits, filter]);

  function handleDeleteOutfit(id) {
    setConfirmDeleteId(id);
  }

  async function confirmDeleteOutfit() {
    const id = confirmDeleteId;
    setConfirmDeleteId(null);
    try {
      await deleteOutfit(id);
      setOutfits((prev) => prev.filter((o) => o.id !== id));
      setPreviewOutfit((prev) => (prev?.id === id ? null : prev));
    } catch (err) {
      alert("Failed to delete outfit: " + err.message);
    }
  }

  return (
    <div className="min-h-screen bg-[#FBF8F5] flex flex-col">
      <Navbar user={user} onLogout={onLogout} />

      <div className="px-4 sm:px-8 py-8 flex-1">
        <h1 className="text-3xl text-ink mb-1" style={{ fontFamily: "'Playfair Display', serif" }}>Outfits</h1>
        <p className="text-sm text-graytext mb-6">Outfits you've saved from Recommendations</p>

        <div className="flex gap-2 overflow-x-auto mb-8">
          {["All", ...occasionOptions].map((o) => (
            <button
              key={o}
              onClick={() => setFilter(o)}
              className={`px-4 py-2 rounded-full text-sm whitespace-nowrap border ${filter === o ? "bg-ink text-white border-ink" : "border-[#EAEAEA] text-graytext"}`}
            >
              {o}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-[#EAEAEA] bg-white p-10 text-center text-graytext text-sm">
            No saved outfits yet. Generate one on the Recommendations page and click “Save Outfit”.
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-6">
            {filtered.map((o) => {
              const pieces = [o.top_detail, o.bottom_detail, o.jacket_detail].filter(Boolean);
              return (
                <div
                  key={o.id}
                  onClick={() => setPreviewOutfit(o)}
                  // CHANGED — border was #EAEAEA (gray), now matches WardrobeCard's tan #CFA187 so both card types look consistent
                  className="group relative rounded-xl border border-[#CFA187] bg-white overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="aspect-square">
                    <OutfitPieceSlider pieces={pieces} imgClassName="w-full h-full p-2" />
                  </div>

                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteOutfit(o.id); }}
                    className="absolute top-2.5 left-2.5 w-7 h-7 rounded-full bg-white/90 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 z-10"
                  >
                    <Trash2 size={13} className="text-red-500" />
                  </button>

                  {/* CHANGED — added the same tan top divider (border-t-[#CFA187]) that WardrobeCard uses between the image and the info section */}
                  <div className="p-3 border-t border-t-[#CFA187] bg-[#F7E6D9]">
                    <div className="text-sm font-medium text-ink">{pieces.map((p) => p.category).join(" + ")}</div>
                    <div className="text-xs text-graytext">{o.occasion} • {pieces.length} pieces</div>
                    <div className="text-[11px] text-graytext/80 mt-1 flex flex-wrap gap-x-2">
                      {o.temp_c != null && <span>🌡️ {Math.round(o.temp_c)}°C</span>}
                      {o.style_preference && <span className="capitalize">✨ {o.style_preference}</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {previewOutfit && (
        <OutfitPreviewModal outfit={previewOutfit} onClose={() => setPreviewOutfit(null)} onDelete={handleDeleteOutfit} />
      )}

      <ConfirmDialog
        open={!!confirmDeleteId}
        title="Remove this outfit?"
        message="Only this saved outfit will be removed. Your individual wardrobe items will remain unchanged."
        onConfirm={confirmDeleteOutfit}
        onCancel={() => setConfirmDeleteId(null)}
      />

      <FooterMini />
    </div>
  );
}