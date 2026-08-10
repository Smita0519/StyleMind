// lib/api.js
// Central place for every call the frontend makes to the Django backend
// (and one call to the local Node/Gemini chat proxy, at the bottom).
const BACKEND = import.meta.env.VITE_BACKEND_URL;

// ────────────────────────────────────────────────────────────
// AUTH — signup, login, and fetching the logged-in user's profile
// ────────────────────────────────────────────────────────────

// Creates a new account. Sends the real email + display name now that the
// backend has a Profile model to store them (previously the backend only
// accepted username+password, so email was faked as the username and the
// name was stashed in localStorage only).
export async function signup(name, email, password) {
  const res = await fetch(`${BACKEND}/api/signup/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: email, password, email, display_name: name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.username?.[0] || err.email?.[0] || err.password?.[0] || "Signup failed");
  }
  // Signup doesn't return login tokens by itself — log in right after so
  // the caller gets back a usable access token in one step.
  return login(email, password);
}

// Logs in with email+password, gets a JWT access token back, and fetches
// the user's real display name from /api/me/ so it doesn't depend on
// anything cached in localStorage from a previous device/session.
export async function login(email, password) {
  const res = await fetch(`${BACKEND}/api/token/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: email, password }),
  });
  if (!res.ok) throw new Error("Invalid email or password");

  const { access, refresh } = await res.json();
  // Stored immediately so the getMe() call right below can use it via authHeaders()
  localStorage.setItem("stylemind_access_token", access);

  let name = "there"; // fallback greeting if the profile fetch fails for any reason
  let pictureUrl = null; // NEW — profile picture, so the navbar avatar shows the real photo right after login instead of just an initial
  try {
    const profile = await getMe();
    name = profile.display_name || "there";
    pictureUrl = profile.pictureUrl;
  } catch {
    // not fatal — the app still works, just with a generic greeting
  }

  const user = { email, name, pictureUrl }; // pictureUrl added to the user object
  return { user, token: access, refresh };
}

// Re-fetches the logged-in user's real profile (username/email/display_name/
// profile_picture) from the backend. Useful for confirming identity after
// localStorage is cleared, on a different device, or after editing the
// profile in the ProfileModal.
export async function getMe() {
  const res = await fetch(`${BACKEND}/api/me/`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch profile");
  const data = await res.json();
  // NEW — same pattern used everywhere else in this file (imageUrl /
  // processedImageUrl): the backend only returns a relative media path
  // like "/media/profile_pics/xyz.jpg", so we prepend BACKEND here once,
  // in one place, instead of every component having to remember to do it.
  return {
    ...data,
    pictureUrl: data.profile_picture ? `${BACKEND}${data.profile_picture}` : null,
  };
}

// NEW — updates the logged-in user's display name and/or profile picture.
// Uses FormData (not JSON) because a picture file may be attached — same
// pattern as uploadWardrobeItem() below. Email is intentionally NOT
// editable here since it's tied to the login username on the backend.
// ===================== CHANGE START =====================
export async function updateProfile({ displayName, pictureFile, removePicture }) {
  const formData = new FormData();
  if (displayName !== undefined) formData.append("display_name", displayName);
  if (pictureFile) formData.append("profile_picture", pictureFile);
  if (removePicture) formData.append("remove_picture", "true");

  const res = await fetch(`${BACKEND}/api/me/`, {
    method: "PATCH",
    headers: authHeaders(), // no Content-Type here on purpose — the browser
    // sets the correct multipart boundary itself when the body is FormData
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.display_name?.[0] || err.profile_picture?.[0] || "Failed to update profile");
  }
  const data = await res.json();
  return {
    ...data,
    pictureUrl: data.profile_picture ? `${BACKEND}${data.profile_picture}` : null,
  };
}

// Small helper — builds the Authorization header every authenticated
// request needs, reading the JWT access token straight out of localStorage.
function authHeaders() {
  const access = localStorage.getItem("stylemind_access_token");
  return { Authorization: `Bearer ${access}` };
}

// ────────────────────────────────────────────────────────────
// WARDROBE — list, upload, delete, and favorite-toggle a wardrobe item
// ────────────────────────────────────────────────────────────

// Fetches all of the logged-in user's wardrobe items, and attaches a full
export async function getWardrobe() {
  const res = await fetch(`${BACKEND}/api/wardrobe/`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load wardrobe");
  const items = await res.json();
  return items.map((item) => ({
    ...item,
    imageUrl: item.image ? `${BACKEND}${item.image}` : null,
    processedImageUrl: item.processed_image ? `${BACKEND}${item.processed_image}` : null,
  }));
}

// Uploads a new clothing photo — the backend runs it through the ML
// classifier (category/texture/season/colors) and returns the full item.
export async function uploadWardrobeItem(file) {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${BACKEND}/api/wardrobe/upload/`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  const item = await res.json();
  return {
    ...item,
    imageUrl: item.image ? `${BACKEND}${item.image}` : null,
    processedImageUrl: item.processed_image ? `${BACKEND}${item.processed_image}` : null,
  };
}
// Deletes a wardrobe item permanently. Backend confirms ownership before
// deleting (404s if it's not yours), so this can't be used to delete
// someone else's item even if you guessed their id.
export async function deleteWardrobeItem(id) {
  const res = await fetch(`${BACKEND}/api/wardrobe/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete item");
}

// Sets (not just toggles) the favorite flag on an item and returns the
// updated item, so the caller can swap it straight into local state.
export async function toggleFavorite(itemId, favorite) {
  const res = await fetch(`${BACKEND}/api/wardrobe/${itemId}/favorite/`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ favorite }),
  });
  if (!res.ok) throw new Error("Failed to update favorite");
  const item = await res.json();
  return {
    ...item,
    imageUrl: item.image ? `${BACKEND}${item.image}` : null,
    processedImageUrl: item.processed_image ? `${BACKEND}${item.processed_image}` : null,
  };
}
// ────────────────────────────────────────────────────────────
// RECOMMENDATIONS — asks the real recommendation engine for an outfit
// ────────────────────────────────────────────────────────────

// Priority is: GPS location (if turned on) > manual temperature slider.
export async function getOutfitRecommendations({ tempC, lat, lon, intent, stylePreference, topK = 3 }) {
  const params = new URLSearchParams({
    intent,
    style_preference: stylePreference,
    top_k: topK,
  });
  if (lat != null && lon != null) {
    params.set("lat", lat);
    params.set("lon", lon);
  } else {
    params.set("temp_c", tempC);
  }

  const res = await fetch(`${BACKEND}/api/recommend/?${params}`, { headers: authHeaders() });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || "Failed to get recommendations");
  }
  const { weather, recommendations, initial_count, rain_nudge } = await res.json();

  const withImageUrl = (piece) =>
    piece
      ? {
          ...piece,
          imageUrl: piece.image ? `${BACKEND}${piece.image}` : null,
          processedImageUrl: piece.processed_image ? `${BACKEND}${piece.processed_image}` : null,
        }
      : piece;

  const results = recommendations.map((r) => ({
    ...r,
    top: withImageUrl(r.top),
    bottom: withImageUrl(r.bottom),
    jacket: withImageUrl(r.jacket),
  }));

  return {
    weather, // weather is null when a manual temp was used instead of a city
    results,
    // NEW — `results` already holds the full ranked pool (up to
    // browse_pool_size on the backend), initialCount says how many to
    // show upfront so the page can offer "browse more" from data it
    // already has, with zero extra requests. rainNudge is a purely
    // informational { icon, message } pair, or null when it's not raining
    // (or no live weather was resolved at all).
    initialCount: initial_count,
    rainNudge: rain_nudge,
  };
}

// ────────────────────────────────────────────────────────────
// OUTFITS — persisting outfits saved from the Recommendations page
// ────────────────────────────────────────────────────────────

// Fetches all outfits the user has saved (used by Outfits.jsx). The backend
// returns top/bottom/jacket as plain ids, and top_detail/bottom_detail/
// jacket_detail as the full nested item — we attach real imageUrl AND
// processedImageUrl to each detail object here, same as every other
// endpoint in this file that returns wardrobe items.
export async function getOutfits() {
  const res = await fetch(`${BACKEND}/api/outfits/`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to fetch outfits");
  const outfitsList = await res.json();

  const withImageUrls = (piece) =>
    piece
      ? {
          ...piece,
          imageUrl: piece.image ? `${BACKEND}${piece.image}` : null,
          processedImageUrl: piece.processed_image ? `${BACKEND}${piece.processed_image}` : null,
        }
      : piece;

  return outfitsList.map((o) => ({
    ...o,
    top_detail: withImageUrls(o.top_detail),
    bottom_detail: withImageUrls(o.bottom_detail),
    jacket_detail: withImageUrls(o.jacket_detail),
  }));
}

// Saves a new outfit — top/bottom/jacket are wardrobe item ids (jacket optional).
export async function saveOutfit({ top, bottom, jacket, occasion, tempC, locationName, region, country, stylePreference }) {
  const res = await fetch(`${BACKEND}/api/outfits/`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({
      top, bottom, jacket, occasion,
      temp_c: tempC,
      location_name: locationName || "",
      region: region || "",
      country: country || "",
      style_preference: stylePreference,
    }),
  });
  if (!res.ok) throw new Error("Failed to save outfit");
  return res.json();
}

// Permanently deletes a saved outfit. Only removes the "these items go
// together" record — the underlying wardrobe items themselves stay untouched.
export async function deleteOutfit(id) {
  const res = await fetch(`${BACKEND}/api/outfits/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const bodyText = await res.text().catch(() => "");
    console.error("deleteOutfit failed:", res.status, bodyText); // TEMP — check browser console
    throw new Error(`Failed to delete outfit (${res.status})`);
  }
}

// ────────────────────────────────────────────────────────────
// CHATBOT — talks directly to the Django backend. Gemini is called
// server-side, using real wardrobe/weather/preference data pulled
// straight from the database.
// ────────────────────────────────────────────────────────────

// Attaches full, browser-ready image URLs to any item objects embedded
// inside a message's segments (the [[item:ID]] chips Gemini references).
function withImageUrlsInSegments(segments) {
  return (segments || []).map((seg) => {
    if (seg.type !== "item" || !seg.item) return seg;
    return {
      ...seg,
      item: {
        ...seg.item,
        imageUrl: seg.item.image ? `${BACKEND}${seg.item.image}` : null,
        processedImageUrl: seg.item.processed_image ? `${BACKEND}${seg.item.processed_image}` : null,
      },
    };
  });
}

export async function getChatHistory(sessionId) {
  const res = await fetch(`${BACKEND}/api/chat/?session=${sessionId}`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load chat history");
  const messages = await res.json();
  return messages.map((m) => ({ ...m, segments: withImageUrlsInSegments(m.segments) }));
}

export async function sendChatMessage(message, sessionId, { lat, lon } = {}) {
  const res = await fetch(`${BACKEND}/api/chat/`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ message, session: sessionId, lat, lon }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || "Chat request failed");
  }
  const { segments } = await res.json();
  return { segments: withImageUrlsInSegments(segments) };
}

// List/create chat sessions
export async function getChatSessions() {
  const res = await fetch(`${BACKEND}/api/chat/sessions/`, { headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to load chat sessions");
  return res.json();
}

export async function createChatSession() {
  const res = await fetch(`${BACKEND}/api/chat/sessions/`, { method: "POST", headers: authHeaders() });
  if (!res.ok) throw new Error("Failed to start a new chat");
  return res.json();
}

// Renames a conversation (used by the sidebar's three-dot menu)
export async function renameChatSession(sessionId, title) {
  const res = await fetch(`${BACKEND}/api/chat/sessions/${sessionId}/`, {
    method: "PATCH",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to rename conversation");
  return res.json();
}

// Permanently deletes a conversation and all its messages
export async function deleteChatSession(sessionId) {
  const res = await fetch(`${BACKEND}/api/chat/sessions/${sessionId}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error("Failed to delete conversation");
}

export async function getServerStartedAt() {
  const res = await fetch(`${BACKEND}/api/health/`);
  if (!res.ok) throw new Error("Health check failed");
  const data = await res.json();
  return data.started_at;
}