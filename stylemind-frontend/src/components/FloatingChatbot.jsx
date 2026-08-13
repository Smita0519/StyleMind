// The bottom-right floating chat widget — available on Home/Wardrobe.
// Shares its actual chat logic with Chatbot.jsx via the useChat hook,
// so only the UI/layout differs between the two.
import { useState } from "react";
import { MessageCircle, X, Sparkles, Send, MapPin } from "lucide-react";
import ChatBubble from "./ChatBubble";
import { useChat } from "../hooks/useChat";

export default function FloatingChatbot() {
  const [isOpen, setIsOpen] = useState(false); // only local state this component owns
  const {
    messages, input, setInput, isThinking, scrollRef, handleSend, handleKeyDown,
    toggleLocation, locationStatus, 
  } = useChat("Hi! I'm your AI Stylist. Ask me anything about outfits, colors, or fashion.");

  return (
    <>
      {/* The toggle button — always visible, fixed bottom-right */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#F97373] text-white shadow-xl flex items-center justify-center z-50 hover:scale-105 transition"
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* The chat panel — only rendered when open */}
      {isOpen && (
        <div className="fixed bottom-24 right-4 left-4 sm:left-auto sm:right-6 sm:w-[380px] h-[70vh] max-h-[450px] bg-white rounded-3xl shadow-2xl border border-[#EFE7E2] flex flex-col overflow-hidden z-50">          <div className="flex items-center gap-3 px-6 py-4 border-b border-[#EFE7E2] bg-[#FFF8F6]">
            <div className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center">
              <Sparkles className="text-[#C46A8A]" size={16} />
            </div>
            <div className="flex-1">
              <h3 className="text-lg" style={{ fontFamily: "'Playfair Display', serif" }}>AI Stylist</h3>
              <p className="text-xs text-gray-500">Your fashion assistant</p>
            </div>
            {/* CHANGED — toggles location on/off instead of one-way request */}
            <button
              onClick={toggleLocation}
              disabled={locationStatus === "requesting"}
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                locationStatus === "on" ? "bg-green-50 text-green-600" : "bg-white text-graytext"
              }`}
              title={locationStatus === "on" ? "Location on — click to turn off" : "Turn on location for weather"}
            >
              <MapPin size={14} />
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 bg-white">
            {messages.map((m) => (
              <ChatBubble key={m.id} role={m.role} text={m.text} segments={m.segments} timestamp={m.timestamp} />
            ))}
            {isThinking && <p className="text-sm text-gray-400">AI Stylist is thinking...</p>}
          </div>

          <div className="border-t border-[#EFE7E2] p-3 bg-white">
            <div className="flex items-center rounded-2xl border border-[#ECE4DE] px-4 h-11">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about fashion..."
                className="flex-1 outline-none text-sm"
              />
              <button
                onClick={handleSend}
                className="w-8 h-8 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#A855F7] text-white flex items-center justify-center hover:scale-110 hover:shadow-lg transition-all duration-200"
              >
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}