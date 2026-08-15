// components/ConfirmDialog.jsx
// A reusable "are you sure?" modal, styled to match the app, used instead
// of the browser's native confirm() popup wherever a destructive action
// (delete) needs confirmation.
import { AlertTriangle } from "lucide-react";

export default function ConfirmDialog({
  open,
  title = "Are you sure?",
  message,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  onConfirm,
  onCancel,
}) {
  if (!open) return null;

  return (
    // z-[60] — higher than the preview modals (z-50), so this can stack
    // correctly on top when triggered from inside one of them
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60] p-4" onClick={onCancel}>
      <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-lg font-semibold text-ink mb-1">{title}</h3>
        {message && <p className="text-sm text-graytext mb-6">{message}</p>}
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 py-2.5 rounded-xl border border-[#EAEAEA] text-sm text-ink hover:bg-[#FAF8F5] transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 py-2.5 rounded-xl text-sm font-medium text-white bg-[#C96A5A] hover:bg-[#B85A4B] transition-colors"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}