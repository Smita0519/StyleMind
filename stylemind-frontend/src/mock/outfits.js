// mock/outfits.js
// The real, exact intents the backend accepts — matches
// src/recommend/filtering.py's INTENT_CATEGORY_MAP keys.
export const occasionOptions = ["Formal", "Casual", "Picnic", "Travel"];

// Mirrors src/recommend/filtering.py's INTENT_CATEGORY_MAP exactly.
// Intent isn't a stored field on a wardrobe item — the backend only ever
// derives it from `category` at recommend-time — so we recompute the same
// mapping here for the Wardrobe page's "Intent" filter instead of asking
// the backend to expose it. If filtering.py's map ever changes, update
// this to match.
const INTENT_CATEGORY_MAP = {
  Formal: ["Formal_Pant", "Shirt"],
  Casual: ["Top", "Warmwear", "Shirt", "Pants", "Shorts"],
  Picnic: ["Dress", "Top", "Skirt", "Shorts"],
  Travel: ["Top", "Warmwear", "Pants"],
};

// A category can belong to more than one intent (e.g. "Shirt" is both
// Formal and Casual), so this returns an array, not a single value.
const OUTERWEAR_CATEGORIES = ["Blazer", "Jacket"];

export function getIntentsForCategory(category) {
  if (OUTERWEAR_CATEGORIES.includes(category)) {
    return occasionOptions; // weather-gated only — valid for every intent
  }
  return occasionOptions.filter((intent) => INTENT_CATEGORY_MAP[intent].includes(category));
}

// Real style_preference options from color_harmony.py — not "moods".
// "safe": neutral colors always score high (0.9). "bold": lowers that
// fallback so genuine color-wheel matches can outrank neutral pairings.
export const stylePreferenceOptions = [
  { value: "safe", label: "Safe (neutrals first)" },
  { value: "bold", label: "Bold (color-forward)" },
];

// Mirrors filtering.py's get_weather_bucket() exactly — so the UI can
// show the user which season bucket their temperature maps to, matching
// what the real backend would compute.
export function getWeatherBucket(tempC) {
  if (tempC >= 25) return "summer";
  if (tempC <= 15) return "winter";
  return "fall";
}

// A handful of fake wardrobe items, shaped exactly like predict()'s real
// output (per INTERFACE.md) — category/texture/season plus confidences,
// season_probs, dominant_colors, mask_found.
export const sampleWardrobe = [
  {
    id: 1, filename: "shirt1.jpg",
    category: "Shirt", category_confidence: 0.94,
    texture: "solid", texture_confidence: 0.81,
    season: "summer", season_confidence: 0.88,
    season_probs: { summer: 0.88, fall: 0.08, winter: 0.02, "all-season": 0.02 },
    dominant_colors: ["#FFFFFF", "#EAEAEA", "#D4D4D4"],
    mask_found: true,
  },
  {
    id: 2, filename: "pants1.jpg",
    category: "Formal_Pant", category_confidence: 0.91,
    texture: "solid", texture_confidence: 0.77,
    season: "all-season", season_confidence: 0.6,
    season_probs: { "all-season": 0.6, fall: 0.25, summer: 0.1, winter: 0.05 },
    dominant_colors: ["#111827", "#3B3B3B"],
    mask_found: true,
  },
  {
    id: 3, filename: "blazer1.jpg",
    category: "Blazer", category_confidence: 0.89,
    texture: "solid", texture_confidence: 0.7,
    season: "winter", season_confidence: 0.85,
    season_probs: { winter: 0.85, fall: 0.1, summer: 0.03, "all-season": 0.02 },
    dominant_colors: ["#D4B996", "#E8D9C0"],
    mask_found: true,
  },
];

// Shaped exactly like ONE object in get_recommendations()'s returned
// list — this is the contract to match when the real endpoint exists.
export const sampleRecommendation = {
  type: "top_bottom",
  top: sampleWardrobe[0],
  bottom: sampleWardrobe[1],
  jacket: sampleWardrobe[2],
  jacket_color_score: 0.82,
  knn_similarity: 0.74,
  color_score: 0.9,
  final_score: 0.816, // 0.6 * knn_similarity + 0.4 * color_score
};

// "More looks you'll love" — simple placeholder thumbnails, purely visual
export const moreLooks = Array.from({ length: 6 }, (_, i) => ({
  id: `look-${i + 1}`,
  bg: ["#F3E4E8", "#E8EDE0", "#E0E8ED", "#E9E4F5"][i % 4],
}));

// Saved/browsable outfits for the Outfits page — occasion values now
// match the real 4 intents exactly, not invented ones.
export const savedOutfits = [
  { id: "o1", name: "Wedding Guest", occasion: "Formal", pieces: 4, bg: "#F3E4E8" },
  { id: "o2", name: "Weekend Layers", occasion: "Casual", pieces: 3, bg: "#E0E8ED" },
  { id: "o3", name: "Summer Picnic", occasion: "Picnic", pieces: 3, bg: "#E8EDE0" },
  { id: "o4", name: "Vacation Ready", occasion: "Travel", pieces: 5, bg: "#E9E4F5" },
  { id: "o5", name: "Office Formal", occasion: "Formal", pieces: 4, bg: "#F3E4E8" },
  { id: "o6", name: "Casual Weekend", occasion: "Casual", pieces: 3, bg: "#E8EDE0" },
];

