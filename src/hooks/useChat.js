// Shared "brain" for the chatbot — both Chatbot.jsx (full page) and
// FloatingChatbot.jsx (widget) call this hook so neither has to duplicate
// message state or the send logic. Each instance manages its own session
// independently — they don't live-sync with each other, but both read/write
// the same backend data.
import { useState, useRef, useEffect } from "react";
import { getChatHistory, sendChatMessage, getChatSessions, createChatSession, renameChatSession, deleteChatSession } from "../lib/api";import { getCurrentLocation } from "../lib/geolocation";

export function useChat(initialMessage) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const scrollRef = useRef(null);

  const [locationCoords, setLocationCoords] = useState(null);
  const [locationStatus, setLocationStatus] = useState("off");

  // ===================== CHANGE START =====================
  // New — session list (for the sidebar) + which one is currently open
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  // ===================== CHANGE END =====================

  async function toggleLocation() {
    if (locationStatus === "on") {
      setLocationCoords(null);
      setLocationStatus("off");
      return;
    }
    setLocationStatus("requesting");
    try {
      const coords = await getCurrentLocation();
      setLocationCoords(coords);
      setLocationStatus("on");
    } catch (err) {
      setLocationStatus("denied");
      console.error("Location request failed:", err.message);
    }
  }

  // ===================== CHANGE START =====================
  // New — loads a specific session's messages, showing the friendly
  // greeting if it's a brand new/empty conversation
  async function loadSession(sessionId) {
    setActiveSessionId(sessionId);
    try {
      const history = await getChatHistory(sessionId);
      if (history.length > 0) {
        setMessages(
          history.map((m) => ({
            id: m.id,
            role: m.role,
            text: m.role === "user" ? m.text : undefined,
            segments: m.role === "assistant" ? m.segments : undefined,
            timestamp: new Date(m.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          }))
        );
      } else {
        setMessages([{ id: "m1", role: "assistant", segments: [{ type: "text", text: initialMessage }], timestamp: "" }]);
      }
    } catch (err) {
      console.error("Failed to load session history:", err);
      setMessages([{ id: "m1", role: "assistant", segments: [{ type: "text", text: initialMessage }], timestamp: "" }]);
    }
  }

  // ===================== CHANGE START =====================
  // CHANGED — no longer creates a backend session immediately. Previously
  // EVERY click created a real, permanent, empty conversation, even if
  // the user never typed anything — so repeatedly clicking "New Chat"
  // piled up empty entries in the sidebar. Now this just resets to a
  // local "draft" state (activeSessionId = null); a real session is only
  // created lazily, in handleSend() below, on the first actual message.
  function startNewChat() {
    setActiveSessionId(null);
    setMessages([{ id: "m1", role: "assistant", segments: [{ type: "text", text: initialMessage }], timestamp: "" }]);
  }
  // ===================== CHANGE END =====================

  // Renames a session, updates the sidebar list in place
  async function renameSession(sessionId, newTitle) {
    try {
      const updated = await renameChatSession(sessionId, newTitle);
      setSessions((prev) => prev.map((s) => (s.id === sessionId ? updated : s)));
    } catch (err) {
      console.error("Failed to rename session:", err);
      alert("Failed to rename conversation: " + err.message);
    }
  }

  // Deletes a session. If it was the active one, switches to another
  // existing session, or starts a fresh one if none are left.
  async function deleteSession(sessionId) {
    try {
      await deleteChatSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (sessionId === activeSessionId) {
        if (remaining.length > 0) {
          await loadSession(remaining[0].id);
        } else {
          await startNewChat();
        }
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
      alert("Failed to delete conversation: " + err.message);
    }
  }  

  // On mount: load the session list. If the user already has at least one
  // conversation, open the most recent one. If they have NONE, just show
  // the greeting locally — same lazy-creation logic as startNewChat, so a
  // brand new user doesn't get an empty session created before they've
  // even typed anything.
  useEffect(() => {
    getChatSessions()
      .then(async (list) => {
        setSessions(list);
        if (list.length > 0) {
          await loadSession(list[0].id);
        } else {
          setMessages([{ id: "m1", role: "assistant", segments: [{ type: "text", text: initialMessage }], timestamp: "" }]);
        }
      })
      .catch((err) => {
        console.error("Failed to load chat sessions:", err);
        setMessages([{ id: "m1", role: "assistant", segments: [{ type: "text", text: initialMessage }], timestamp: "" }]);
      })
      .finally(() => setHistoryLoaded(true));
  }, []);
  // ===================== CHANGE END =====================

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking]);

  function timestamp() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  async function handleSend() {
    // ===================== CHANGE START =====================
    // CHANGED — only blocks on empty input now. Previously also required
    // activeSessionId, which meant if the backend was unreachable on
    // load (e.g. Django server not running), the button silently did
    // nothing forever with no feedback at all.
    if (!input.trim()) return;
    const userMsg = { id: crypto.randomUUID(), role: "user", text: input, timestamp: timestamp() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);

    const weatherParams = locationCoords ? { lat: locationCoords.lat, lon: locationCoords.lon } : {};

    try {
      // ===================== CHANGE START =====================
      // NEW — lazily creates the real backend session on the FIRST
      // message of a new conversation, instead of eagerly creating one
      // the instant "New Chat" is clicked. This is what actually stops
      // empty sessions from piling up in the sidebar.
      let sessionId = activeSessionId;
      if (!sessionId) {
        const session = await createChatSession();
        sessionId = session.id;
        setActiveSessionId(sessionId);
        setSessions((prev) => [session, ...prev]);
      }
      // ===================== CHANGE END =====================

      const { segments } = await sendChatMessage(userMsg.text, sessionId, weatherParams);
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", segments, timestamp: timestamp() }]);

      getChatSessions().then(setSessions).catch(() => {});
    } catch (err) {
      console.error("Chat failed:", err);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          segments: [{ type: "text", text: "Sorry, I'm having trouble connecting right now — your message was added here, but the reply couldn't be fetched." }],
          timestamp: timestamp(),
        },
      ]);
    } finally {
      setIsThinking(false);
    }
    // ===================== CHANGE END =====================
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return {
    messages, input, setInput, isThinking, historyLoaded, scrollRef, handleSend, handleKeyDown,
    toggleLocation, locationStatus,
    sessions, activeSessionId, loadSession, startNewChat,
    renameSession, deleteSession, // NEW
  };
}