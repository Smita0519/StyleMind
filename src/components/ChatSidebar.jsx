// Sidebar shown on the full /chat page. Shows real saved conversations,
// with a three-dot menu per item for rename/delete.
import { useState, useRef, useEffect } from "react";
import { Sparkles, Plus, MessageSquare, MoreVertical, Pencil, Trash2, Check, X } from "lucide-react";
import ConfirmDialog from "./ConfirmDialog";
import ScrollingTitle from "./ScrollingTitle";

// CHANGED — added mobileOpen/onCloseMobile so this can also work as a
// slide-in drawer on small screens (it used to just be `hidden` below the
// lg breakpoint with no way to open it at all).
export default function ChatSidebar({ sessions, activeSessionId, onSelectSession, onNewChat, onRename, onDelete, mobileOpen, onCloseMobile }) {
  const [openMenuId, setOpenMenuId] = useState(null);   // which session's three-dot menu is open
  const [renamingId, setRenamingId] = useState(null);   // which session is currently being renamed (inline input)
  const [renameValue, setRenameValue] = useState("");
  const [confirmDeleteId, setConfirmDeleteId] = useState(null); // NEW — id pending delete confirmation
  const menuRef = useRef(null);

  // Closes the three-dot menu if the user clicks anywhere outside it
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpenMenuId(null);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function startRename(session) {
    setRenamingId(session.id);
    setRenameValue(session.title || "");
    setOpenMenuId(null);
  }

  function confirmRename(sessionId) {
    const trimmed = renameValue.trim();
    if (trimmed) onRename(sessionId, trimmed);
    setRenamingId(null);
  }

  // Opens the styled ConfirmDialog instead of deleting right away
  function handleDelete(sessionId) {
    setConfirmDeleteId(sessionId);
    setOpenMenuId(null);
  }

  function confirmDelete() {
    const id = confirmDeleteId;
    setConfirmDeleteId(null);
    onDelete(id);
  }

  return (
    <>
      {/* NEW — mobile-only backdrop, dims the page behind the drawer and
          closes it on click. Never rendered on lg+ since the sidebar is
          always visible there and mobileOpen is irrelevant. */}
      {mobileOpen && (
        <div className="fixed inset-0 bg-black/40 z-40 lg:hidden" onClick={onCloseMobile} />
      )}

      <div
        // CHANGED — used to be permanently `hidden lg:flex` (fully
        // inaccessible below the lg breakpoint). Now: on lg+ it's always a
        // normal static column exactly as before; below lg it becomes a
        // fixed slide-in drawer, shown/hidden and animated based on
        // `mobileOpen`.
        className={`${mobileOpen ? "flex" : "hidden"} lg:flex
          fixed lg:static inset-y-0 left-0 z-50 lg:z-auto
          w-[280px] flex-shrink-0 flex-col border-r border-[#F1E8E4]
          transition-transform duration-300 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} lg:translate-x-0`}
        style={{ background: "linear-gradient(180deg, #f6d4cb 0%, #FDF3F1 50%, #FBEDEA 100%)" }}
      >
      <div className="px-6 pt-8 pb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl text-[#222]" style={{ fontFamily: "'Playfair Display', serif" }}>AI Stylist</h2>
            <p className="text-sm text-gray-500 mt-1">Your personal<br />fashion assistant</p>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center shadow-sm flex-shrink-0">
              <Sparkles className="text-[#C46A8A]" size={18} />
            </div>
            {/* NEW — close button, only shown on the mobile drawer (hidden on lg+, where the sidebar can't be "closed") */}
            <button onClick={onCloseMobile} className="lg:hidden w-8 h-8 rounded-full bg-white/70 flex items-center justify-center text-gray-500 hover:bg-white flex-shrink-0">
              <X size={15} />
            </button>
          </div>
        </div>

        <button
          onClick={() => { onNewChat(); onCloseMobile?.(); }} // closes the mobile drawer after starting a new chat
          className="w-full flex items-center justify-center gap-2 rounded-xl py-2.5 text-sm font-medium text-white bg-gradient-to-r from-[#7C3AED] to-[#F97373] hover:opacity-90 transition"
        >
          <Plus size={15} /> New Chat
        </button>
      </div>

      <div className="px-4 flex-1 overflow-y-auto">
  {sessions.length === 0 && (
    <p className="text-xs text-gray-400 px-2">
      No conversations yet.
    </p>
  )}

  {sessions.map((s) => (
    <div key={s.id} className="relative group mb-1">
      {renamingId === s.id ? (
        <div className="flex items-center gap-1 px-2 py-1.5">
          <input
            autoFocus
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") confirmRename(s.id);
              if (e.key === "Escape") setRenamingId(null);
            }}
            className="flex-1 text-sm rounded-lg border border-[#CAB6AB] px-2 py-1.5 outline-none bg-white"
          />

          <button
            onClick={() => confirmRename(s.id)}
            className="w-7 h-7 rounded-full bg-white flex items-center justify-center hover:bg-green-50"
          >
            <Check size={14} className="text-green-600" />
          </button>

          <button
            onClick={() => setRenamingId(null)}
            className="w-7 h-7 rounded-full bg-white flex items-center justify-center hover:bg-red-50"
          >
            <X size={14} className="text-red-500" />
          </button>
        </div>
      ) : (
        <div className="relative">
          {/* Conversation Row */}
          <button
            onClick={() => { onSelectSession(s.id); onCloseMobile?.(); }} // closes the mobile drawer after picking a conversation
            className={`w-full flex items-center gap-2 text-left px-3 py-2.5 pr-11 rounded-xl text-sm transition-colors ${
              s.id === activeSessionId
                ? "bg-white shadow-sm text-ink font-medium"
                : "text-gray-600 hover:bg-white/60"
            }`}
          >
            <MessageSquare
              size={14}
              className="flex-shrink-0 text-gray-400"
            />

            <ScrollingTitle>
              {s.title || "New conversation"}
            </ScrollingTitle>
          </button>

          {/* Three Dots */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              setOpenMenuId(
                openMenuId === s.id ? null : s.id
              );
            }}
            className={`absolute right-2 top-1/2 -translate-y-1/2
              w-7 h-7 rounded-full flex items-center justify-center
              transition-all duration-150
              ${
                openMenuId === s.id
                  ? "opacity-100 bg-white"
                  : "opacity-0 group-hover:opacity-100 hover:bg-[#F3F3F3]"
              }`}
          >
            <MoreVertical
              size={14}
              className="text-gray-500"
            />
          </button>
        </div>
      )}

      {/* Dropdown */}
      {openMenuId === s.id && (
        <div
          ref={menuRef}
          className="absolute right-2 top-full mt-1 w-36 bg-white rounded-xl shadow-lg border border-[#EAEAEA] py-1 z-20"
        >
          <button
            onClick={() => startRename(s)}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ink hover:bg-[#FAF8F5] text-left"
          >
            <Pencil size={13} />
            Rename
          </button>

          <button
            onClick={() => handleDelete(s.id)}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-50 text-left"
          >
            <Trash2 size={13} />
            Delete
          </button>
        </div>
      )}
    </div>
  ))}
</div>

<ConfirmDialog
  open={!!confirmDeleteId}
  title="Delete this conversation?"
  message="This can't be undone — all messages in it will be permanently removed."
  onConfirm={confirmDelete}
  onCancel={() => setConfirmDeleteId(null)}
/>
      </div>
    </>
  );
}