// Fake data standing in for real backend endpoints. Once Member C's
// Django backend + Member A's CNN pipeline exist, these arrays get
// replaced by real fetch() calls in lib/api.js — nothing else changes.

// The REAL taxonomy Member A's trained model uses (confirmed from their
// INTERFACE.md handoff) — not something we invented.
export const categories = ["All Items", "Blazer", "Dress", "Formal_Pant", "Jacket", "Pants", "Shirt", "Shorts", "Skirt", "Top", "Warmwear"];
export const seasons = ["All Season", "summer", "winter", "fall", "all-season"];

// Fake wardrobe items shown in the /wardrobe grid before real uploads exist.
export const initialWardrobeItems = [
  { id: "w1", name: "White Shirt", category: "Shirt", texture: "solid", season: "summer", intent: "Casual", dominant_colors: ["#FFFFFF", "#EAEAEA", "#D4D4D4"] },
  { id: "w2", name: "Black Blazer", category: "Blazer", texture: "solid", season: "winter", intent: "Formal", dominant_colors: ["#111827", "#3B3B3B", "#6B6B6B"] },
  { id: "w3", name: "Blue Denim Pants", category: "Pants", texture: "solid", season: "all-season", intent: "Casual", dominant_colors: ["#2563EB", "#1E3A8A", "#93C5FD"] },
  { id: "w4", name: "Beige Trench Jacket", category: "Jacket", texture: "solid", season: "winter", intent: "Travel", dominant_colors: ["#D4B996", "#E8D9C0", "#F3ECE0"] },
  { id: "w5", name: "Striped T-Shirt", category: "Top", texture: "striped", season: "summer", intent: "Picnic", dominant_colors: ["#FFFFFF", "#111827"] },
  { id: "w6", name: "Black Wide Leg Pants", category: "Pants", texture: "solid", season: "all-season", intent: "Formal", dominant_colors: ["#111827"] },
  { id: "w7", name: "Floral Summer Dress", category: "Dress", texture: "floral", season: "summer", intent: "Picnic", dominant_colors: ["#EC4899", "#FAF8F5", "#78350F"] },
  { id: "w8", name: "Grey Wool Warmwear", category: "Warmwear", texture: "solid", season: "winter", intent: "Travel", dominant_colors: ["#6B7280", "#374151"] },
];

// Fake recent-chats list shown in ChatSidebar (Chatbot.jsx's sidebar).
export const mockRecentChats = [
  { id: "1", title: "Outfit for wedding", time: "10:30 AM" },
  { id: "2", title: "Rainy day looks", time: "Yesterday" },
];

// Fake "previously liked outfits" — sent to Gemini so its advice can
// reference past preferences. Not yet actually updated when you like something.
export const mockPreferenceHistory = [
  { outfitId: "o1", occasion: "date night", liked: true },
];