// components/OutfitImageCard.jsx
// A small inline chip showing a real wardrobe item's photo, meant to sit
// mid-sentence inside a chat bubble. Hovering it pops up a larger,
// square product-style preview card.
import { useState, useRef } from "react";
import { createPortal } from "react-dom";

export default function OutfitImageCard({ item }) {
  const [popupPos, setPopupPos] = useState(null); // null = hidden; {top, left, placement} when shown
  const chipRef = useRef(null);
  const src = item.processedImageUrl || item.imageUrl;

  const POPUP_WIDTH = 192;  // matches w-48 below
  const POPUP_HEIGHT = 260; // rough card height, used for the "does it fit above?" check

  // ===================== CHANGE START =====================
  // NEW — computes the popup's position from the chip's actual on-screen
  // location (not from CSS positioning relative to an ancestor), so it
  // can be rendered via a portal straight into document.body. This is
  // what actually fixes the clipping: the popup no longer lives inside
  // the scrollable message list or under the fixed navbar's stacking
  // context, so neither can cut it off anymore.
  function handleMouseEnter() {
    const rect = chipRef.current.getBoundingClientRect();
    const fitsAbove = rect.top > POPUP_HEIGHT + 12;

    let left = rect.left + rect.width / 2 - POPUP_WIDTH / 2;
    // Clamp horizontally so it never runs off either edge of the screen
    left = Math.max(8, Math.min(left, window.innerWidth - POPUP_WIDTH - 8));

    setPopupPos({
      left,
      top: fitsAbove ? rect.top - 8 : rect.bottom + 8,
      placement: fitsAbove ? "above" : "below",
    });
  }
  // ===================== CHANGE END =====================

  return (
    <>
      <span
        ref={chipRef}
        className="relative inline-flex items-center gap-1.5 align-middle mx-1 bg-[#FBF1EC] border border-[#EAD9CF] rounded-full pl-1 pr-2.5 py-0.5 cursor-pointer"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setPopupPos(null)}
      >
        {src ? (
          <img src={src} alt={item.category} className="w-6 h-6 rounded-full object-cover" />
        ) : (
          <span className="w-6 h-6 rounded-full bg-[#D4B996]/40 flex-shrink-0" />
        )}
        <span className="text-sm font-medium text-ink">{item.category}</span>
      </span>

      {/* ===================== CHANGE START ===================== */}
      {/* CHANGED — rendered via a portal into document.body with
          position:fixed, using the coordinates computed above, instead
          of position:absolute nested inside the chip. z-[9999] keeps it
          above the fixed navbar too. */}
      {popupPos && src && createPortal(
        <div
          className="fixed z-[9999] pointer-events-none"
          style={{ top: popupPos.top, left: popupPos.left, transform: popupPos.placement === "above" ? "translateY(-100%)" : "none" }}
        >
          <div className="w-48 bg-white rounded-2xl shadow-xl border border-[#EAD9CF] overflow-hidden">
            <div className="w-full aspect-square bg-white flex items-center justify-center border-b border-[#F3E4E8]">
              <img src={src} alt={item.category} className="w-full h-full object-contain p-3" />
            </div>
            <div className="px-3 py-2.5 bg-[#F7E6D9] text-center">
              <div className="text-sm font-semibold text-ink">{item.category}</div>
              {(item.texture || item.season) && (
                <div className="text-xs text-graytext mt-0.5">
                  {[item.texture, item.season].filter(Boolean).join(" • ")}
                </div>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
      {/* ===================== CHANGE END ===================== */}
    </>
  );
}