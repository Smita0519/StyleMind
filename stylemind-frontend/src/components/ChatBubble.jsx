// Renders ONE message in a conversation — styled differently depending
// on whether it came from the user or the AI assistant. Assistant
// messages are made of "segments" (alternating text and real wardrobe
// item chips) so images appear exactly where they're mentioned, not
// bunched below the whole message.
import { Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import OutfitImageCard from "./OutfitImageCard";

export default function ChatBubble({ role, text, segments, timestamp }) {
  const isUser = role === "user";
  const navigate = useNavigate();

  // NEW — collects every real wardrobe item mentioned in this message,
  // so "Try on Avatar" can pass the whole recommended outfit along
  const itemsInMessage = (segments || [])
    .filter((seg) => seg.type === "item" && seg.item)
    .map((seg) => seg.item);

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-6`}>

      {/* Assistant message: avatar icon + light bubble, aligned left */}
      {!isUser && (
        <div className="flex items-start gap-3 max-w-[78%]">
          <div className="w-10 h-10 rounded-full bg-[#FFF4EF] border border-[#F0E4DE] flex items-center justify-center flex-shrink-0 shadow-sm">
            <Sparkles size={16} className="text-[#C46A8A]" />
          </div>
          <div>
            <div className="bg-white border border-[#E8DDD6] rounded-2xl rounded-tl-md px-5 py-4 shadow-sm">
              <p className="text-[15px] leading-8 text-[#333] whitespace-pre-wrap">
                {(segments || []).map((seg, i) =>
                  seg.type === "item" ? (
                    <OutfitImageCard key={i} item={seg.item} />
                  ) : (
                    <span key={i}>{seg.text}</span>
                  )
                )}
              </p>

              {/* NEW — only shown when this message actually referenced
                  real wardrobe items, so it doesn't appear on plain chat */}
              {itemsInMessage.length > 0 && (
                <button
                  onClick={() => navigate("/avatar", { state: { outfitItems: itemsInMessage } })}
                  className="mt-3 text-xs font-medium text-white bg-ink px-3 py-1.5 rounded-full hover:opacity-90 transition"
                >
                  Try this on Avatar →
                </button>
              )}
            </div>
            {timestamp && <p className="text-xs text-gray-400 mt-2 ml-2">{timestamp}</p>}
          </div>
        </div>
      )}

      {/* User message: gradient bubble, aligned right, no avatar */}
      {isUser && (
        <div className="max-w-[70%] flex flex-col items-end">
          <div className="bg-gradient-to-br from-[#6B35A7] via-[#7A3DB7] to-[#8644C4] rounded-2xl rounded-br-md px-5 py-4 shadow-md whitespace-pre-wrap">
            <p className="text-[15px] text-white leading-7 whitespace-pre-wrap">{text}</p>
          </div>
          {timestamp && <p className="text-xs text-gray-400 mt-2 mr-2">{timestamp}</p>}
        </div>
      )}
    </div>
  );
}