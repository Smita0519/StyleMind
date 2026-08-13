# StyleMind — Frontend (Member D)

Personal AI fashion stylist app. This covers frontend, wardrobe UI, and the AI Stylist chatbot.

## Tech Stack
- React (Vite) + React Router
- Tailwind CSS v4
- Gemini API (`@google/genai`) via a temporary local proxy server (see below)

## Setup

1. Install dependencies:
```bash
   cd frontend
   npm install
```

2. Create `frontend/.env`:
VITE_API_BASE_URL=http://localhost:3001

3. Run the dev server:
```bash
   npm run dev
```

**Important:** the chatbot will not work unless `chat-proxy/` is also running in a separate terminal (`node server.js`).

## Folder Structure
src/
├── components/       # Navbar, Button, Input, ChatBubble, ChatSidebar,
│                        OutfitImageCard, WardrobeCard, UploadModal
├── pages/            # Login, Signup, Home, Wardrobe, Chatbot
├── mock/             # Fake data standing in for backend endpoints
├── lib/
│   └── api.js        # ALL backend calls go through here — swap mock/proxy
│                        for real endpoints here only, nothing else changes

## Screens Status
- [x] Login / Signup — functional with mock auth, social buttons are UI-only placeholders
- [x] Home — built with placeholder trending-look cards (no real photos yet)
- [x] Wardrobe grid + filters + Upload modal — functional against mock data
- [x] AI Stylist Chatbot — functional, connected to Gemini via local proxy
- [ ] Outfit results / avatar display screen — depends on Member B's 3D avatar work
- [ ] Data labeling — see "Open Question" below, blocked on confirming scope with Member A

## Mock Data (temporary — replace once backend is live)
- `mock/chatHistory.js` — fake wardrobe items, recent chats, preference history
- `mock/wardrobeItems.js` — fake wardrobe grid items, categories, colors, seasons
- None of this persists. Wardrobe, chat history, and preferences reset on
  every page refresh since there's no database yet.

## ⚠️ Open Question — Data Labeling Scope
Not yet confirmed with Member A:
- Are we labeling raw/original photos, or re-labeling a DeepFashion subset
  into our own category/texture/season schema (21/7/3 classes)?
- Where should source images come from — DeepFashion directly, or a
  different source?
- Exact taxonomy needed: the precise list of 21 categories, 7 textures, and
  3 seasons Member A's model expects.

**Action item:** confirm with Member A before starting bulk labeling, so
work isn't duplicated or mismatched with the model's expected input format.

---

## ⚠️ Backend Integration Handoff — READ THIS

The chatbot currently calls a **temporary local Node/Express proxy**
(`chat-proxy/`), not the real Django backend, because Django wasn't built yet
when this was developed. This needs to be ported into Django before final
integration.

### Why a proxy exists at all
Gemini's API does not allow direct browser calls (no CORS support on any
endpoint) and exposing the API key in frontend code is insecure. The proxy
exists purely to move the Gemini call server-side.

### What to port into Django

**Endpoint:** `POST /api/chat`

**Request body (JSON):**
```json
{
  "userMessage": "string",
  "wardrobe": [ { "id": "string", "category": "string", "texture": "string", "season": "string", "dominant_colors": ["#hex", "#hex", "#hex"] } ],
  "weather": "string",
  "preferenceHistory": [ { "outfitId": "string", "occasion": "string", "liked": true } ],
  "previousInteractionId": "string | null"
}
```

**Response body (JSON):**
```json
{
  "text": "string — the AI's reply",
  "interactionId": "string — pass this back in as previousInteractionId on the next call"
}
```

**Reference implementation:** see `chat-proxy/server.js` — shows the exact
Gemini call, system prompt, and request/response shape to replicate in a
Django view.

**Once the Django endpoint exists:** update `VITE_API_BASE_URL` in
`frontend/.env`. No `.js` files need to change.

**Also needed from Django eventually:**
- `POST /api/login`, `POST /api/signup` — currently mocked in `lib/api.js`
- `GET /api/wardrobe`, `POST /api/wardrobe/upload` — currently mocked in
  `mock/wardrobeItems.js`; real upload should trigger Member A's CNN
  pipeline (bg removal → resize/normalize → classification → dominant colors)

### Known limitations to fix during integration
- Wardrobe, chat history, and preferences are all hardcoded mocks
- Gemini's markdown output (`**bold**`) isn't rendered as actual bold text
- Uploaded item category/color/season are placeholder "Unclassified" until
  the real classification pipeline is connected
- API key currently lives in `chat-proxy/.env` — move to Django's env config
- Google/Apple login buttons are UI-only, not wired to real OAuth



##########################################################################################################################



# StyleMind — Frontend (Member D)

Personal AI fashion stylist app. Covers all frontend UI (Login/Signup, Home,
Wardrobe/Upload, AI Stylist Chatbot — both a dedicated page and a floating
widget), plus documentation. 

## Tech Stack
- React (Vite) + React Router
- Tailwind CSS v4 (`@theme` tokens in `index.css` for design system colors/fonts)
- Gemini API (`@google/genai`) via a temporary local proxy server (see below)
- Mobile responsive throughout via Tailwind's `sm:`/`md:`/`lg:` breakpoints
  (these compile to real CSS media queries)

## Setup

1. Install dependencies:
```bash
   cd frontend
   npm install
```

2. Create `frontend/.env`:
VITE_API_BASE_URL=http://localhost:3001

3. Run the dev server:
```bash
   npm run dev
```

**Important:** the chatbot will not work unless `chat-proxy/` is also running
in a separate terminal (`node server.js`).

## Folder Structure
src/
├── components/   # Navbar (incl. ProfileMenu), Button, Input, ChatBubble,
│                   ChatSidebar, OutfitImageCard, WardrobeCard, UploadModal,
│                   FloatingChatbot
├── pages/        # Login, Signup, Home, Wardrobe, Chatbot
├── mock/         # Fake data standing in for backend endpoints
├── lib/
│   └── api.js    # ALL backend calls go through here — swap mock/proxy for
│                   real endpoints here only, nothing else changes

## Screens Status
- [x] Login / Signup — full-screen layout, real name captured at signup,
      mock auth persisted via localStorage (so refresh doesn't log you out),
      password show/hide toggle, social buttons are UI-only placeholders
- [x] Home — hero section with background photo, occasion cards, quick
      actions, greets the logged-in user by their real name
- [x] Wardrobe — grid + category/season filters + color swatch selector +
      mobile filter drawer + Upload modal, all against mock data
- [x] AI Stylist Chatbot — both a dedicated `/chat` page (with sidebar +
      chat history) and a floating toggle widget available on Home/Wardrobe;
      connected to Gemini via local proxy
- [x] Navbar — responsive (hamburger menu on mobile), active-page indicator
      (red underline/left-border), search/notification/profile icons
- [x] Profile dropdown — shows real logged-in user's name + email, includes
      working Log Out (clears session, redirects to login)
- [ ] Outfit results / avatar display screen — depends on Member B's 3D
      avatar work being ready to integrate against
- [ ] Data labeling — see "ML Integration Update" below; likely no longer
      needed as originally scoped

## ML Integration Update (from Member A's handoff)
Member A's `INTERFACE.md`/`README.md` shows the model is already trained,
with labeling done automatically via CLIP zero-shot classification — not
manually by hand. Real taxonomy now used in mock data:
- **Category** (10): Blazer, Dress, Formal_Pant, Jacket, Pants, Shirt,
  Shorts, Skirt, Top, Warmwear
- **Texture** (7): solid, striped, floral, graphic, embroidered, pleated,
  checkered
- **Season** (4): summer, winter, fall, all-season
- **Dominant colors**: extracted via K-Means, not manually labeled

This replaces the earlier placeholder 21/7/3 taxonomy used in early mock
data. Confirmed with Member A that manual data labeling is no longer needed
on my end — worth re-confirming this is still accurate before final submission.

## Mock Data / Auth (temporary — replace once backend is live)
- `mock/wardrobeItems.js` — wardrobe items, categories, textures, seasons,
  color swatches
- `mock/chatHistory.js` — fake recent chats, preference history
- `lib/api.js` — `login`/`signup` currently simulate a backend using
  `localStorage` as a lightweight mock "database," so signup → login
  round-trips correctly with the real name/email entered, without a real
  server. This only works within the same browser and must be replaced
  with real Django auth endpoints.
- None of the wardrobe/chat data persists across sessions — resets on
  every page refresh since there's no real database yet.

## ⚠️ Backend Integration Handoff — READ THIS

The chatbot currently calls a **temporary local Node/Express proxy**
(`chat-proxy/`), not the real Django backend, since Django wasn't built yet.
This needs to be ported into Django before final integration.

### Why a proxy exists at all
Gemini's API does not support CORS from a browser, and exposing the API key
in frontend code is insecure. The proxy moves the Gemini call server-side.

### What to port into Django

**Endpoint:** `POST /api/chat`

**Request body:**
```json
{
  "userMessage": "string",
  "wardrobe": [ { "id": "string", "category": "string", "texture": "string", "season": "string", "dominant_colors": ["#hex"] } ],
  "weather": "string",
  "preferenceHistory": [ { "outfitId": "string", "occasion": "string", "liked": true } ],
  "previousInteractionId": "string | null"
}
```

**Response body:**
```json
{ "text": "string", "interactionId": "string" }
```

**Reference implementation:** `chat-proxy/server.js` — shows the exact
Gemini call, system prompt, and request/response shape to replicate.

**Once the Django endpoint exists:** update `VITE_API_BASE_URL` in
`frontend/.env`. No `.js` files need to change.

**Also needed from Django eventually:**
- `POST /api/login`, `POST /api/signup` — replacing the `localStorage` mock
- `GET /api/wardrobe`, `POST /api/wardrobe/upload` — real upload should
  trigger Member A's CNN pipeline (bg removal → resize/normalize →
  classification → dominant colors)

### Known limitations to fix during integration
- Auth, wardrobe, chat history, and preferences are all mocked/localStorage
- Gemini's markdown output (`**bold**`) isn't rendered as actual bold text
- Uploaded item category/texture/season are placeholder "Unclassified"
  until the real classification pipeline is connected
- API key lives in `chat-proxy/.env` — move to Django's env config
- Google/Facebook login buttons are UI-only, not wired to real OAuth
- Search and notification icons in the navbar are placeholders