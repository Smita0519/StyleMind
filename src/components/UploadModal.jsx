import { useState } from "react";
import { X, Upload } from "lucide-react";
import Button from "./Button";

export default function UploadModal({ onClose, onAdd }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);

  function handleFileChange(e) {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  }

  async function handleConfirm() {
    if (!file) return;
    setUploading(true);
    try {
      await onAdd(file); // Wardrobe.jsx handles the real backend upload + classification
      onClose();
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-graytext"><X size={18} /></button>
        <h3 className="text-lg font-semibold text-ink mb-4">Add New Item</h3>

        <label className="block border-2 border-dashed border-[#EAEAEA] rounded-xl h-48 flex flex-col items-center justify-center cursor-pointer mb-4 overflow-hidden">
          {preview ? <img src={preview} alt="preview" className="w-full h-full object-cover" /> : (
            <>
              <Upload size={24} className="text-graytext mb-2" />
              <span className="text-sm text-graytext">Click to upload a photo</span>
            </>
          )}
          <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
        </label>

        <p className="text-xs text-graytext mb-4">
          Category, texture, season, and dominant colors will be detected automatically once uploaded.
        </p>

        <Button onClick={handleConfirm} disabled={!file || uploading}>
          {uploading ? "Uploading & classifying..." : "Add to Wardrobe"}
        </Button>
      </div>
    </div>
  );
}