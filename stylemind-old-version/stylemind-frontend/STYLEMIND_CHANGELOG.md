# StyleMind — Work Completed (Changelog & Reference)

This document summarizes everything built/fixed across the frontend-backend integration work, organized by feature area. Written so any team member (or future you) can see what exists, why it exists, and what still needs attention.

---

## 1. Backend Integration Foundations

Originally the frontend ran on mock data and `localStorage` workarounds while the Django backend (built by a teammate) was developed in parallel. The following gaps were closed to connect the two:

| Feature | What was added |
|---|---|
| **Delete wardrobe item** | `DELETE /api/wardrobe/<id>/` — was called by the frontend but didn't exist |
| **Real signup fields** | `Profile` model (email + display name) added — signup previously only accepted username/password, faking email as username |
| **`GET/PATCH /api/me/`** | Lets the frontend re-fetch/update the real user profile (name, email, profile picture) instead of trusting only `localStorage` |
| **Favorites** | `favorite` field on `WardrobeItem` + `PATCH /api/wardrobe/<id>/favorite/` — was local-only before |
| **Saved outfits persistence** | `Outfit` model + `GET/POST /api/outfits/` + `DELETE /api/outfits/<id>/` — was local-only before |
| **Confirmed: PostgreSQL storage** | User/profile data was already correctly persisting to Postgres (verified via `settings.py` + direct `psql` query) — not actually broken, just unverified |

---

## 2. Wardrobe Page

- **Intent filter** — computed client-side (`getIntentsForCategory()` in `mock/outfits.js`), mirroring the backend's `INTENT_CATEGORY_MAP`, instead of requiring a new backend field.
- **Image display** — switched from `object-cover` (cropped) to `object-contain` (full garment visible); fixed a flexbox `min-w-0` bug that clipped multi-piece images.
- **Item count badge** — shows total wardrobe count + "N shown" when filters are active.
- **Sort dropdown** — Newest / Oldest / Name were previously non-functional UI stubs; now actually sorts.
- **Real selection count** — "Selected as final outfit N times" now comes from a backend `SerializerMethodField` (`selection_count`, counts real saved `Outfit` rows referencing the item) instead of a disconnected `localStorage` counter that never incremented once saving moved server-side.
- **Delete confirmation** — replaced the native browser `confirm()` with a styled `ConfirmDialog` component (reused across Wardrobe, Outfits, and the chat sidebar).
- **Async upload** — uploading no longer blocks the request through the full YOLO -> classification -> color-extraction pipeline. `POST /api/wardrobe/upload/` now returns immediately (202) with `status: "processing"`, runs the ML pipeline in a background thread, and the frontend polls every 3s until it flips to `"done"`/`"failed"`. Cards show a spinner overlay while processing.
  - *Note: uses Python `threading`, not Celery/Redis — appropriate for this project's scope, but worth knowing for a production writeup (no retry/monitoring, doesn't survive a server restart mid-job).*

---

## 3. Recommendations Page

- **Top-3 (now top-N) display** — was only ever showing `results[0]`; now shows a picker row of options with a live "Browse more" pool.
- **Weather integration** — switched from OpenWeatherMap to **WeatherAPI.com** (returns location name + region + country in one call, no separate reverse-geocoding step needed). **No caching** — every request hits the live API.
- **GPS location** — "Turn on location" button requests real browser geolocation (with the native permission prompt) via a shared `lib/geolocation.js` helper; resolved coordinates feed the same weather-resolution priority as the manual slider (GPS > manual temperature).
- **Live weather card** — shows temperature, condition, feels-like, humidity, and full location breadcrumb once resolved.
- **Rain nudge** — a small "bring an umbrella" banner when live conditions indicate rain (`precip_mm` + condition-text check), purely informational, doesn't affect filtering.
- **Off-season badge** — flags outfit pieces whose season doesn't match current weather. *(A remaining inconsistency here was diagnosed and handed off to the recommendation-engine teammate — see Section 8.)*
- **Processed (background-removed) images** — used throughout instead of raw photos with backgrounds.
- **Saved outfit now records real context** — `saveOutfit()` sends the actual resolved weather (`location_name`, `region`, `country`) and style preference, not just the slider's fallback value (previously a bug: the real GPS-resolved weather was silently dropped at save-time).
- **Persistence across refresh** — last-generated recommendation + preferences restore from `localStorage`, but auto-clear if the user was away 2+ minutes, or if the backend process has restarted since (detected via a new `GET /api/health/` boot-timestamp endpoint).

---

## 4. Outfits Page

- **Real image display** — fixed a bug where the page was reading `o.top`/`o.bottom`/`o.jacket` (plain numeric IDs) instead of `o.top_detail`/`o.bottom_detail`/`o.jacket_detail` (the actual nested item objects with images).
- **Full location breadcrumb** — shows saved location name/region/country (or temperature, if no location was used) and style preference per saved outfit.
- **Horizontal piece slider** — each card shows one piece (top/bottom/jacket) at a time with left/right arrows and position dots, instead of squeezing all pieces into one row; same component reused in the full preview modal.
- **Click-to-preview modal** — `OutfitPreviewModal` shows a larger view, saved date, full preference breakdown, and per-piece detail list.
- **Delete** — `DELETE /api/outfits/<id>/` + styled confirmation dialog (does not delete the underlying wardrobe items, only the "these go together" record).

---

## 5. Chatbot

This went through the most iteration — originally a separate Node/Express + Gemini proxy, later rebuilt **natively inside Django** (`wardrobe/chatbot.py`) so it could pull real data directly from the database instead of trusting whatever the frontend sent.

### Grounding in the real recommendation engine
- Calls the **exact same** `get_recommendations()` function the Recommendations page uses — not a separate/simplified version.
- **Critical fix**: was building a minimal wardrobe dict (`id, category, texture, season, dominant_colors` only) instead of the full serialized item data. This caused `filtering.py`'s `season_confidence` bypass logic to behave differently, sometimes making the chatbot report "no match found" when the Recommendations page correctly found several. Now both paths use the identical `WardrobeItemSerializer` output.
- **Deterministic ordering** — added `.order_by("id")` to wardrobe queries in both `chatbot.py` and `views.py`'s `recommend()`, so tied-score outfits resolve to the same winner consistently across both features (previously could differ due to unordered DB row order).
- **"I don't like this, suggest something else"** — now steps through the actual ranked list the engine computed (position 0, then 1, then 2...), remembered per chat session (`ChatSession.last_intent`, `last_outfit_index`, `last_temp_c`), instead of Gemini inventing a substitute. Only falls back to a plainly-labeled non-algorithmic wardrobe mention once that ranked list is genuinely exhausted.
- **Context continuity** — restating the same occasion/temperature mid-conversation no longer resets back to the already-rejected #1 pick; only a genuinely new occasion or a >2C temperature change resets.
- **Missing-temperature fallback** — if an occasion is named but no temperature can be resolved (no location, nothing stated), falls back to a default (22C) rather than skipping grounding entirely — and is instructed to disclose that it assumed a temperature.
- **No freelance alternatives** — system prompt explicitly forbids presenting a second, ungrounded outfit combination alongside the real engine's pick (was previously happening — e.g. suggesting a Dress for a Formal occasion despite the engine's actual category rules excluding dresses from Formal).
- **Optional jacket/blazer phrasing** — instructed to present jacket/blazer as an optional layer ("grab it if you want the extra layer"), matching how the engine itself treats it, not as a mandatory piece.

### Weather
- Real GPS location (shared `lib/geolocation.js` helper, same as Recommendations) or a typed city, both wired into the actual chat request.
- Fixed: temperature parsing only recognized the degree symbol — now also recognizes "degree", "degrees", "degree celsius" (and the common "celcius" typo), "deg C", and bare numbers with any of those markers.
- Displayed temperature is rounded for readability (e.g. "20C") while the underlying precise value still feeds the actual scoring logic unchanged.

### Item images in chat
- Gemini references specific items via a `[[item:ID]]` marker in its reply text, parsed server-side into structured `segments` (`{type: "text"}` / `{type: "item", item: {...}}`), so the frontend can render real photos inline rather than plain text.
- Fixed a formatting drift where Gemini would sometimes write "(ID 14)" instead of the required marker (silently producing no image) — prompt now explicitly lists the wrong formats to avoid.
- **Hover-to-enlarge popup** — hovering an inline item chip shows a larger product-card-style preview (image + category + texture/season), rendered via a React Portal directly into `document.body` so it can't be clipped by the scrolling message list or the fixed navbar.

### Chat sessions (real multi-conversation support)
- `ChatSession` + `ChatMessage` models — real persisted conversation threads, replacing the earlier single continuous history.
- Sidebar shows real sessions with rename (inline edit) and delete (three-dot menu + styled confirmation dialog, matching Wardrobe/Outfits).
- **Lazy session creation** — fixed a bug where clicking "New Chat" immediately created a permanent empty backend session every time, even if nothing was ever sent. Now a session is only created on the first actual message.

### Other
- **"Try this on Avatar"** — a button appears under any chatbot reply that referenced real wardrobe items, passing them via router state to the Avatar page. Since the 3D avatar rendering itself is a teammate's separate unfinished feature, this currently displays which items are "being tried on" as a placeholder rather than rendering them on a 3D body.

---

## 6. Home Page

- **Trending Looks** — converted from a static grid to a horizontal snap-scroll slider with left/right arrow buttons; left arrow only appears once actually scrolled away from the start (uses a `ResizeObserver`, not just a one-time check, so it stays accurate as images load in).

---

## 7. Cross-Cutting / Polish

- **Scroll-to-top button** — added once, in the shared `ProtectedLayout` wrapper, so it applies to every logged-in page automatically.
- **Processed (background-removed) images** — used consistently across Wardrobe, Recommendations, Outfits, and Chatbot instead of raw photos.
- **Google/Facebook login** — built out (backend token-verification endpoints + frontend SDK wrappers), but **currently not in use** — deprioritized per team decision; the code exists in prior conversation history if revisited later, but was intentionally not carried forward into active use.

---

## 8. Known Issues / Handed Off

- **Off-season badge inconsistency** (`src/recommend/filtering.py`) — the "off-season" badge only catches items pulled in via the explicit category-fallback pass, not items that passed the *normal* filter only because their `season_confidence` was too low to trust. Diagnosis and exact fix were written up and **handed to the recommendation-engine team member** to apply, since it's their file.

---

## 9. Environment Variables Reference

**Backend `.env`:**
```
WEATHERAPI_KEY=your-weatherapi-com-key
GEMINI_API_KEY=your-gemini-api-key
# Database (PostgreSQL) — see settings.py
```

**Frontend `.env`:**
```
VITE_BACKEND_URL=http://localhost:8000
```
*(The separate `VITE_API_BASE_URL` for the old Node chat proxy is no longer needed — chat now goes through the Django backend directly.)*

---

## 10. Migrations Required

If pulling this work fresh, run:
```bash
python manage.py makemigrations wardrobe
python manage.py migrate
```
Covers: `Profile`, `Outfit` (+ `location_name`/`region`/`country`/`style_preference` fields), `WardrobeItem.favorite`, `WardrobeItem.status`, `WardrobeItem.processed_image`, `ChatSession`, `ChatMessage`, and `ChatSession.last_intent`/`last_outfit_index`/`last_temp_c`.
