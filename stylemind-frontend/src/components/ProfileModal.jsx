// components/ProfileModal.jsx
// Opens when "View Profile" is clicked in the Navbar. Shows the user's
// name, email, and profile picture, and lets them edit the name, upload
// a new picture, remove the current one, or click it to view full size.
import { useState, useRef } from "react";
import { X, Camera, Loader2, Trash2, ZoomIn } from "lucide-react";
import { updateProfile } from "../lib/api";
import ImageLightbox from "./ImageLightbox";

export default function ProfileModal({ user, onClose, onSave }) {
  const [displayName, setDisplayName] = useState(user?.name || "");
  const [picturePreview, setPicturePreview] = useState(user?.pictureUrl || null);
  const [pictureFile, setPictureFile] = useState(null);
  // ===================== CHANGE START =====================
  // NEW — tracks whether the user explicitly asked to remove the current
  // photo. Separate from picturePreview being null, since that also
  // happens before any photo ever existed — this flag is only true when
  // they actively clicked "Remove".
  const [pictureRemoved, setPictureRemoved] = useState(false);
  const [showLightbox, setShowLightbox] = useState(false);
  // ===================== CHANGE END =====================
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const initial = displayName?.[0]?.toUpperCase() || "?";

  function handlePictureChange(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPictureFile(file);
    setPicturePreview(URL.createObjectURL(file));
    setPictureRemoved(false); // picking a new photo cancels any pending removal
  }

  // ===================== CHANGE START =====================
  // NEW — clears the local preview immediately and marks it for removal
  // on save
  function handleRemovePicture() {
    setPicturePreview(null);
    setPictureFile(null);
    setPictureRemoved(true);
  }
  // ===================== CHANGE END =====================

  async function handleSave() {
    setError("");
    setSaving(true);
    try {
      // CHANGED — pass removePicture through
      const updated = await updateProfile({ displayName, pictureFile, removePicture: pictureRemoved });
      onSave({ email: user.email, name: updated.display_name, pictureUrl: updated.pictureUrl });
      onClose();
    } catch (err) {
      setError(err.message || "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      {/* ===================== CHANGE START ===================== */}
      {/* REDESIGNED — warm gradient header band behind the avatar (same
          palette as ChatSidebar/Login), softer card background, tan
          accents throughout, instead of the previous plain white card */}
      <div
        className="rounded-2xl w-full max-w-sm overflow-hidden relative"
        style={{ background: "#FEFBF8" }}
        onClick={(e) => e.stopPropagation()}
      >
        <button onClick={onClose} className="absolute top-4 right-4 text-white/90 hover:text-white z-10">
          <X size={18} />
        </button>

        {/* Gradient header band */}
        <div
          className="pt-8 pb-14 px-6 text-center"
          style={{ background: "linear-gradient(160deg, #6b5c47 0%, #D4B996 100%)" }}
        >
          <h2 className="text-lg font-semibold text-white" style={{ fontFamily: "'Playfair Display', serif" }}>
            Your Profile
          </h2>
        </div>

        {/* Avatar overlaps the gradient band and the card body below it */}
        <div className="flex flex-col items-center -mt-12 mb-6 px-6">
          <div className="relative">
            <div
              className="w-24 h-24 rounded-full bg-tan flex items-center justify-center text-white text-3xl font-semibold overflow-hidden border-4 border-white shadow-md cursor-pointer"
              onClick={() => picturePreview && setShowLightbox(true)} // NEW — click the photo to view it full size
            >
              {picturePreview ? (
                <img src={picturePreview} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                initial
              )}
            </div>
            
            <button
              onClick={() => fileInputRef.current?.click()}
              className="absolute bottom-0 right-0 w-8 h-8 rounded-full bg-ink text-white flex items-center justify-center border-2 border-white hover:opacity-90"
              title="Change photo"
            >
              <Camera size={14} />
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" onChange={handlePictureChange} className="hidden" />
          </div>

          {/* NEW — Remove Photo, only shown when there's actually a photo to remove */}
          {picturePreview && (
            <button
              onClick={handleRemovePicture}
              className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-600 mt-3"
            >
              <Trash2 size={12} /> Remove photo
            </button>
          )}
        </div>
        {/* ===================== CHANGE END ===================== */}

        <div className="px-6 pb-6">
          <div className="mb-4">
            <label className="text-xs font-bold text-gray-500 uppercase block mb-1.5">Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full border border-[#E7D8CD] bg-white rounded-lg px-3 py-2 text-sm text-ink focus:outline-none focus:border-tan transition-colors"
            />
          </div>

          <div className="mb-6">
            <label className="text-xs font-bold text-gray-500 uppercase block mb-1.5">Email</label>
            <div className="w-full border border-[#E7D8CD] rounded-lg px-3 py-2 text-sm text-graytext bg-[#FAF3EC]">
              {user?.email}
            </div>
          </div>

          {error && <p className="text-xs text-red-600 mb-4">{error}</p>}

          <div className="flex gap-3">
            <button
              onClick={onClose}
              disabled={saving}
              className="flex-1 border border-[#E7D8CD] text-ink rounded-lg py-2.5 text-sm hover:bg-[#FAF3EC] transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !displayName.trim()}
              className="flex-1 bg-ink text-white rounded-lg py-2.5 text-sm hover:opacity-90 transition-opacity flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {saving && <Loader2 size={14} className="animate-spin" />}
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>

      {/* NEW — full-size photo viewer, opened by clicking the avatar */}
      {showLightbox && <ImageLightbox src={picturePreview} onClose={() => setShowLightbox(false)} />}
    </div>
  );
}