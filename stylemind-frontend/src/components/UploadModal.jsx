import { useState } from "react";
import { X, Upload } from "lucide-react";
import Button from "./Button";

export default function UploadModal({ onClose, onAdd }) {
  const [files, setFiles] = useState([]);       // now an array instead of a single file
  const [previews, setPreviews] = useState([]); // matching array of object URLs
  const [uploading, setUploading] = useState(false);

  function handleFileChange(e) {
    const selected = Array.from(e.target.files); // FileList -> real array
    if (!selected.length) return;
    setFiles(selected);
    setPreviews(selected.map((f) => URL.createObjectURL(f)));
  }

  function removeFile(index) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleConfirm() {
    if (!files.length) return;
    setUploading(true);
    try {
      await onAdd(files); // Wardrobe.jsx now handles an array, uploads each
      onClose();
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl p-6 relative max-h-[85vh] flex flex-col">
        <button onClick={onClose} className="absolute top-4 right-4 text-graytext"><X size={18} /></button>
        <h3 className="text-lg font-semibold text-ink mb-4">Add New Items</h3>

        {previews.length > 0 ? (
          <div className="grid grid-cols-4 sm:grid-cols-5 gap-2 mb-4 overflow-y-auto max-h-[50vh] pr-1">
            {previews.map((src, i) => (
              <div key={i} className="relative w-full aspect-square rounded-lg overflow-hidden border border-[#EAEAEA]">
                <img src={src} alt={`preview ${i}`} className="w-full h-full object-cover" />
                <button
                  onClick={() => removeFile(i)}
                  className="absolute top-1 right-1 w-5 h-5 rounded-full bg-black/60 text-white flex items-center justify-center text-xs"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
            <label className="w-full aspect-square rounded-lg border-2 border-dashed border-[#EAEAEA] flex items-center justify-center cursor-pointer text-graytext">
              <Upload size={18} />
              <input type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
            </label>
          </div>
        ) : (
          <label className="block border-2 border-dashed border-[#EAEAEA] rounded-xl h-48 flex flex-col items-center justify-center cursor-pointer mb-4">
            <Upload size={24} className="text-graytext mb-2" />
            <span className="text-sm text-graytext">Click to upload photos</span>
            <input type="file" accept="image/*" multiple onChange={handleFileChange} className="hidden" />
          </label>
        )}

        <p className="text-xs text-graytext mb-4">
          {files.length > 1 ? `${files.length} Photos selected:` : ""}
          Category, texture, season, and dominant colors will be detected automatically once uploaded.
        </p>

        <Button onClick={handleConfirm} disabled={!files.length || uploading}>
          {uploading
            ? `Uploading ${files.length > 1 ? `${files.length} items` : "item"}...`
            : `Add ${files.length > 1 ? `${files.length} Items` : "to Wardrobe"}`}
        </Button>
      </div>
    </div>
  );
}