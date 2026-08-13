import { useState } from "react";
import { RotateCw, ZoomIn, Maximize2 } from "lucide-react";
import Navbar from "../components/Navbar";
import FooterMini from "../components/FooterMini";
import { bodyTypes, skinTones, hairStyles, hairColors } from "../mock/outfits";
import { useLocation } from "react-router-dom";

const outfitTabs = ["Tops", "Bottoms", "Dresses", "Shoes", "Acc."];

export default function Avatar({ user, onLogout }) {
  // NEW — reads the outfit passed from the chatbot's "Try this on Avatar"
  // button, if the user arrived here that way
  const location = useLocation();
  const outfitFromChat = location.state?.outfitItems || null;

  const [bodyType, setBodyType] = useState(bodyTypes[0]);
  const [skinTone, setSkinTone] = useState(skinTones[0]);
  const [height, setHeight] = useState(166);
  const [hairStyle, setHairStyle] = useState(hairStyles[0]);
  const [hairColor, setHairColor] = useState(hairColors[0]);
  const [activeTab, setActiveTab] = useState(outfitTabs[0]);

  return (
    <div className="min-h-screen bg-[#FBF8F5]">
      <Navbar user={user} onLogout={onLogout} />

      <div className="px-4 sm:px-8 py-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Avatar Settings — left */}
           <aside className="w-full lg:w-64 flex-shrink-0 rounded-2xl border border-[#EAEAEA] bg-white p-6 h-fit">
            <h3 className="text-sm font-semibold text-ink mb-5">Avatar Settings</h3>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Body Type</label>
              <div className="grid grid-cols-4 gap-2">
                {bodyTypes.map((b) => (
                  <button
                    key={b}
                    onClick={() => setBodyType(b)}
                    title={b}
                    className={`aspect-square rounded-lg border text-xs flex items-center justify-center ${
                      bodyType === b ? "border-ink bg-[#F3E4E8]" : "border-[#EAEAEA] text-graytext"
                    }`}
                  >
                    {b[0]}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Skin Tone</label>
              <div className="flex gap-2">
                {skinTones.map((t) => (
                  <button
                    key={t}
                    onClick={() => setSkinTone(t)}
                    className={`w-7 h-7 rounded-full border transition-all ${
                      skinTone === t ? "ring-2 ring-offset-2 ring-ink border-transparent" : "border-[#EAEAEA]"
                    }`}
                    style={{ backgroundColor: t }}
                  />
                ))}
              </div>
            </div>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">
                Height <span className="text-ink font-semibold normal-case">{height} cm</span>
              </label>
              <input
                type="range"
                min="150"
                max="185"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                className="w-full accent-ink"
              />
            </div>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Hair Style</label>
              <div className="flex flex-wrap gap-2">
                {hairStyles.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHairStyle(h)}
                    className={`px-3 py-1.5 rounded-full text-xs border ${
                      hairStyle === h ? "border-ink bg-[#F3E4E8] text-ink" : "border-[#EAEAEA] text-graytext"
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Hair Color</label>
              <div className="flex gap-2">
                {hairColors.map((c) => (
                  <button
                    key={c}
                    onClick={() => setHairColor(c)}
                    className={`w-7 h-7 rounded-full border transition-all ${
                      hairColor === c ? "ring-2 ring-offset-2 ring-ink border-transparent" : "border-[#EAEAEA]"
                    }`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </div>
          </aside> 

          {/* Avatar preview — center. Placeholder only: the actual 3D
              rendering is Member B's Three.js work, not built here. */}
          <div className="flex-1 rounded-2xl border border-[#EAEAEA] bg-gradient-to-b from-[#F7E6D9] to-[#F3E4E8] flex flex-col items-center justify-center min-h-[500px] relative">
            <div className="text-center text-graytext">
              <div className="w-40 h-64 mx-auto rounded-xl border-2 border-dashed border-[#D9C4A3] flex items-center justify-center mb-4">
                <span className="text-xs px-4 text-center">3D Avatar Preview<br /><span className="opacity-60">(Member B's Three.js scene renders here)</span></span>
              </div>
              <p className="text-xs">Body: {bodyType} · Height: {height}cm · Hair: {hairStyle}</p>

              {/* NEW — shows the outfit that was passed in from the
                  chatbot, since the 3D scene itself isn't built yet */}
              {outfitFromChat && (
                <div className="mt-4 bg-white/70 rounded-xl p-3 max-w-xs mx-auto">
                  <p className="text-[11px] font-semibold text-ink uppercase mb-2">Trying on from chat:</p>
                  <div className="flex justify-center gap-2">
                    {outfitFromChat.map((item) => (
                      <img
                        key={item.id}
                        src={item.processed_image || item.image}
                        alt={item.category}
                        className="w-14 h-14 object-contain bg-[#FAF8F5] rounded-lg border border-[#EAEAEA]"
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="absolute bottom-4 flex items-center gap-4 bg-white/80 rounded-full px-4 py-2 text-xs text-graytext">
              <button className="flex items-center gap-1"><RotateCw size={14} /> Rotate</button>
              <button className="flex items-center gap-1"><ZoomIn size={14} /> Zoom</button>
              <button className="flex items-center gap-1"><Maximize2 size={14} /> Full Screen</button>
            </div>
          </div>

          {/* Outfit Options — right */}
          <aside className="w-full lg:w-72 flex-shrink-0 rounded-2xl border border-[#EAEAEA] bg-white p-6 h-fit">
            <h3 className="text-sm font-semibold text-ink mb-4">Outfit Options</h3>
            <div className="flex gap-1 mb-4 border-b border-[#EAEAEA] overflow-x-auto">
              {outfitTabs.map((t) => (
                <button
                  key={t}
                  onClick={() => setActiveTab(t)}
                  className={`px-3 py-2 text-xs whitespace-nowrap border-b-2 ${
                    activeTab === t ? "border-ink text-ink font-medium" : "border-transparent text-graytext"
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-3 gap-2">
              {Array.from({ length: 6 }, (_, i) => (
                <button
                  key={i}
                  className="aspect-square rounded-lg border border-[#EAEAEA] bg-[#F3E4E8] hover:border-ink transition-colors"
                  onClick={() => alert(`Selecting ${activeTab} item ${i + 1} — connects to real wardrobe once ready`)}
                />
              ))}
            </div>
          </aside>
        </div>
      </div>
      <FooterMini />
    </div>
  );
}