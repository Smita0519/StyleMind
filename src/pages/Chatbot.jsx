// pages/Chatbot.jsx
// The full dedicated /chat page — sidebar + full-height conversation view.
import { useState } from "react"; // NEW — tracks whether the mobile chat-history drawer is open
import Navbar from "../components/Navbar";
import ChatSidebar from "../components/ChatSidebar";
import ChatBubble from "../components/ChatBubble";
import { useChat } from "../hooks/useChat";
import { Send, MapPin, Menu } from "lucide-react"; // NEW — Menu icon for the hamburger button

export default function Chatbot({ user, onLogout }) {
  const {
    messages, input, setInput, isThinking, scrollRef, handleSend, handleKeyDown,
    toggleLocation, locationStatus,
    sessions, activeSessionId, loadSession, startNewChat,
    renameSession, deleteSession, // NEW
  } = useChat("Hi! Tell me what you're dressing for and I'll pull looks from your wardrobe.");

  // NEW — the chat-history sidebar used to be `hidden` completely below the
  // lg breakpoint with no way to open it. Now it's a slide-in drawer,
  // toggled by this state and a hamburger button below.
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-[#FAF8F5]">
      <Navbar user={user} onLogout={onLogout} />
      <div className="flex flex-1 min-h-0">
        <ChatSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={loadSession}
          onNewChat={startNewChat}
          onRename={renameSession}
          onDelete={deleteSession}
          mobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />

        <div className="flex-1 flex flex-col min-w-0 bg-[#FBF8F5]">
          {/* NEW — mobile-only bar with a hamburger button to open the chat
              history drawer. Hidden on lg+, since the sidebar is already
              visible there. */}
          <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-[#F1E8E4] bg-white flex-shrink-0">
            <button onClick={() => setMobileSidebarOpen(true)} className="text-ink">
              <Menu size={20} />
            </button>
            <span className="text-sm font-medium text-ink truncate">
              {sessions.find((s) => s.id === activeSessionId)?.title || "AI Stylist"}
            </span>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 sm:px-8 py-4">
            {messages.map((m) => (
              <ChatBubble key={m.id} role={m.role} text={m.text} segments={m.segments} timestamp={m.timestamp} />
            ))}
            {isThinking && <div className="text-sm text-graytext px-1">Thinking…</div>}
          </div>

          {/* Location button sits left of the input; green when toggled on */}
          <div className="px-4 sm:px-9 py-4 flex-shrink-0 border-t border-[#CAB6AB] bg-white">
            {locationStatus === "requesting" && (
              <p className="text-[11px] text-amber-600 mb-1.5">Turning on location…</p>
            )}
            {locationStatus === "denied" && (
              <p className="text-[11px] text-red-500 mb-1.5">Location permission denied.</p>
            )}
            <div className="flex items-center gap-2">
              <button
                onClick={toggleLocation}
                disabled={locationStatus === "requesting"}
                title={
                  locationStatus === "on"
                    ? "Location on — tap to turn off"
                    : locationStatus === "requesting"
                    ? "Turning on location…"
                    : "Turn on location for weather"
                }
                className={`flex-shrink-0 w-11 h-11 rounded-full border flex items-center justify-center transition-colors ${
                  locationStatus === "on"
                    ? "border-green-300 bg-green-50 text-green-700"
                    : locationStatus === "requesting"
                    ? "border-amber-300 bg-amber-50 text-amber-700 animate-pulse"
                    : "border-[#CAB6AB] bg-white text-graytext hover:border-tan"
                }`}
              >
                <MapPin size={16} />
              </button>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything about fashion..."
                className="flex-1 rounded-full text-sm whitespace-pre-wrap outline-none min-w-0 bg-white border border-[#CAB6AB] px-5 py-4 shadow-sm"
              />
              <button
                onClick={handleSend}
                className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A855F7] text-white flex items-center justify-center hover:scale-110 hover:shadow-lg transition-all duration-200"
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}