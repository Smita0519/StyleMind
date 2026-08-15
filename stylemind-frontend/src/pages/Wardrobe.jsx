// pages/Wardrobe.jsx
// The "My Wardrobe" page — lists all of the user's uploaded clothing items
// with search, category/season/intent filters, favorites, upload, and delete.
import { useState, useMemo, useEffect } from "react";
import { Search, Plus, SlidersHorizontal, X, ChevronDown, Heart, Sparkles } from "lucide-react";import Navbar from "../components/Navbar";
import FooterMini from "../components/FooterMini";
import WardrobeCard from "../components/WardrobeCard";
import UploadModal from "../components/UploadModal";
import ItemPreviewModal from "../components/ItemPreviewModal";
import { categories, seasons } from "../mock/wardrobeItems";
import ConfirmDialog from "../components/ConfirmDialog";

// occasionOptions -> filter dropdown values; getIntentsForCategory -> derives
// an item's intent(s) from its category, mirroring the backend's own mapping
// (intent isn't stored on the item itself, see filtering.py on the backend)
import { occasionOptions, getIntentsForCategory } from "../mock/outfits";
// All real backend calls this page needs — wardrobe list/upload/delete/favorite
import { getWardrobe, uploadWardrobeItem, deleteWardrobeItem, toggleFavorite, resolveDuplicate } from "../lib/api";

export default function Wardrobe({ user, onLogout }) {
  // ── Data state ──
  const [items, setItems] = useState([]);       // the user's real wardrobe items, fetched from the backend
  const [loading, setLoading] = useState(true);  // true while the initial fetch is in flight
  const [loadError, setLoadError] = useState(""); // set if the initial fetch fails

  // ── Filter/search state ──
  const [category, setCategory] = useState("All Items");
  const [season, setSeason] = useState("All Season");
  const [intent, setIntent] = useState("All Intents");
  const [search, setSearch] = useState("");
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false);
  const [sortBy, setSortBy] = useState("Newest"); // controls the sort dropdown — Newest/Oldest/Name

  // ── UI state (modals/panels) ──
  const [showUpload, setShowUpload] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [previewItem, setPreviewItem] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null); // NEW — id of item pending delete confirmation

  // Fetch the real wardrobe once when the page loads
  useEffect(() => {
    getWardrobe()
      .then(setItems)
      .catch((err) => setLoadError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Calls the real backend to flip an item's favorite flag, then swaps that
  // one item in local state with whatever the server sends back.
  async function handleToggleFavorite(id) {
    const current = items.find((item) => item.id === id);
    if (!current) return;
    try {
      const updated = await toggleFavorite(id, !current.favorite);
      setItems((prev) => prev.map((item) => (item.id === id ? updated : item)));
    } catch (err) {
      alert("Failed to update favorite: " + err.message);
    }
  }

  async function handleResolveDuplicate(id, keep) {
    try {
      const result = await resolveDuplicate(id, keep);
      if (keep && result) {
        setItems((prev) => prev.map((item) => (item.id === id ? result : item)));
      } else {
        setItems((prev) => prev.filter((item) => item.id !== id));
      }
    } catch (err) {
      alert("Failed to resolve: " + err.message);
    }
  }

  // Recomputes the visible list whenever any filter/search/sort value or
  // the underlying items list changes.
  const filtered = useMemo(() => {
    const result = items.filter((item) => {
      const matchesCategory = category === "All Items" || item.category === category;
      const matchesSeason = season === "All Season" || item.season === season;
      // Intent is derived from category client-side (not a real backend field)
      const matchesIntent = intent === "All Intents" || getIntentsForCategory(item.category).includes(intent);
      const matchesFavorite = !showFavoritesOnly || item.favorite;
      const matchesSearch = !search || (item.category || "").toLowerCase().includes(search.toLowerCase());
      return matchesCategory && matchesSeason && matchesIntent && matchesFavorite && matchesSearch;
    });

    // Sort AFTER filtering, so the dropdown just reorders whatever already
    // matched the filters/search — doesn't change which items show up.
    const sorted = [...result]; // copy first — never sort the array in place, that would mutate state
    if (sortBy === "Newest") {
      sorted.sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at));
    } else if (sortBy === "Oldest") {
      sorted.sort((a, b) => new Date(a.uploaded_at) - new Date(b.uploaded_at));
    } else if (sortBy === "Name") {
      // There's no separate "name" field on a wardrobe item — category is
      // the closest thing to a display name, so sort alphabetically by that.
      sorted.sort((a, b) => (a.category || "").localeCompare(b.category || ""));
    }
    return sorted;
  }, [items, category, season, intent, showFavoritesOnly, search, sortBy]);

  // Uploads a new photo — backend runs it through the ML classifier and
  // returns the fully-populated item, which gets prepended to the list.
// Uploads new photos — backend runs each through the ML classifier and
  // returns the fully-populated item, which gets prepended to the list.
  // Uploads happen one at a time (not Promise.all) so a single failed
  // file doesn't cancel the others, and successes still show up even if
  // one fails partway through.
  async function handleAddItem(files) {
    const fileList = Array.isArray(files) ? files : [files]; // keep back-compat if anything still passes a single file
    const failed = [];

    for (const file of fileList) {
      try {
        const newItem = await uploadWardrobeItem(file); // returns almost instantly, status: "processing"
        setItems((prev) => [newItem, ...prev]);
      } catch (err) {
        failed.push(file.name);
      }
    }

    if (failed.length) {
      alert(`Failed to upload: ${failed.join(", ")}`);
    }
  }

  // NEW — while any item is still "processing", re-fetch the wardrobe
  // every 3s so its card updates to the real classification once the
  // background thread finishes, without the user needing to refresh.
  useEffect(() => {
    const hasProcessing = items.some((item) => item.status === "processing");
    if (!hasProcessing) return;
    const interval = setInterval(() => {
      getWardrobe().then(setItems).catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, [items]);

// Opens the styled confirm dialog instead of deleting right away
  function handleDeleteItem(id) {
    setConfirmDeleteId(id);
  }

  // Runs the actual delete only after the user confirms in the dialog
  async function confirmDeleteItem() {
    const id = confirmDeleteId;
    setConfirmDeleteId(null);
    try {
      await deleteWardrobeItem(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      alert("Failed to delete item: " + err.message);
    }
  }

  // The filter sidebar — reused both in the desktop <aside> and the mobile slide-over panel
  const FilterPanel = (
    <>
      <h3 className="text-sm font-semibold text-[#444] mb-5">FILTERS</h3>

      {/* Category filter */}
      <div className="mb-8">
        <p className="text-xs font-bold text-gray-500 mb-3 uppercase">Category</p>
        <div className="relative">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full appearance-none rounded-lg border border-[#EAEAEA] bg-white px-3 py-2.5 text-sm text-ink outline-none cursor-pointer focus:border-tan transition-colors pr-9"
          >
            <option>All Items</option>
            {categories.filter((c) => c !== "All Items").map((c) => <option key={c}>{c}</option>)}
          </select>
          <ChevronDown size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-graytext pointer-events-none" />
        </div>
      </div>

      {/* Intent filter — Formal/Casual/Picnic/Travel, derived from category */}
      <div className="mb-8">
        <p className="text-xs font-bold text-gray-500 mb-3 uppercase">Intent</p>
        <div className="relative">
          <select
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            className="w-full appearance-none rounded-lg border border-[#EAEAEA] bg-white px-3 py-2.5 text-sm text-ink outline-none cursor-pointer focus:border-tan transition-colors pr-9"
          >
            <option>All Intents</option>
            {occasionOptions.map((o) => <option key={o}>{o}</option>)}
          </select>
          <ChevronDown size={15} className="absolute right-3 top-1/2 -translate-y-1/2 text-graytext pointer-events-none" />
        </div>
      </div>

      {/* Season filter */}
      <div className="mb-8">
        <p className="text-xs font-bold text-gray-500 mb-3 uppercase">Season</p>
        <div className="space-y-2">
          {seasons.map((s) => (
            <label key={s} className="flex items-center gap-2 cursor-pointer text-sm text-gray-700">
              <input type="radio" checked={season === s} onChange={() => setSeason(s)} className="accent-[#A66F79]" />
              {s}
            </label>
          ))}
        </div>
      </div>

      {/* Favorites-only toggle */}
      <div>
        <button
          onClick={() => setShowFavoritesOnly((v) => !v)}
          className={`w-full flex items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm border transition-colors ${
            showFavoritesOnly ? "bg-ink text-white border-ink" : "bg-white text-ink border-[#EAEAEA]"
          }`}
        >
          <Heart
            size={14}
            className={showFavoritesOnly ? "fill-white text-white" : "fill-[#A66F79] text-[#A66F79]"}
          />
          Favorites
        </button>
      </div>
    </>
  );

  return (
    <div className="min-h-screen bg-[#FBF8F5] flex flex-col">
      <Navbar user={user} onLogout={onLogout} />

      <div className="px-8 py-8 flex-1">
       {/* Page header + item count badge + "Add New Item" button */}
        <div className="flex flex-wrap justify-between items-center gap-5 mb-8">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-4xl text-[#222]" style={{ fontFamily: "'Playfair Display', serif" }}>My Wardrobe</h1>
              {/* Item count pill — only rendered once the initial fetch has settled,
                  so it doesn't flash "0 items" while still loading */}
              {!loading && !loadError && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-[#F7E6D9] to-[#F3D9E8] border border-[#EAD2D9] px-3.5 py-1.5 text-sm font-medium text-[#8A4B5C]">
                  <Sparkles size={13} className="text-[#C46A8A]" />
                  {items.length} {items.length === 1 ? "item" : "items"}
                </span>
              )}
            </div>
            <p className="text-gray-500 mt-2">
              Organize, manage & love your collection

              {!loading && !loadError && filtered.length !== items.length && (
                <span className="ml-2 inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-[#F7E6D9] to-[#F3D9E8] border border-[#EAD2D9] px-3.5 py-1.5 text-sm font-medium text-[#8A4B5C]">
                  <Sparkles size={13} className="text-[#C46A8A]" />
                  {filtered.length} shown
                </span>
              )}
            </p>
            
          </div>
          <button onClick={() => setShowUpload(true)} className="flex items-center gap-2 rounded-xl bg-[#171B29] text-white px-6 py-3 hover:bg-black transition">
            <Plus size={18} />
            Add New Item
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Desktop filter sidebar — hidden on mobile, replaced by the slide-over panel below */}
          <aside className="hidden lg:block w-[260px] flex-shrink-0 h-fit rounded-2xl p-6 border border-[#E7D8CD] shadow-sm bg-[#F7E6D9]">
            {FilterPanel}
          </aside>

          <main className="flex-1 min-w-0">
            {/* Search bar + mobile filter button + sort dropdown */}
            <div className="flex flex-wrap justify-between gap-4 mb-8">
              <div className="relative w-[360px] max-w-full">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search in wardrobe..."
                  className="w-full h-12 rounded-xl border border-[#E7DDD5] bg-white pl-11 pr-4 text-sm outline-none"
                />
              </div>
              <div className="flex gap-3">
                <button className="lg:hidden border rounded-xl px-4" onClick={() => setShowFilters(true)}>
                  <SlidersHorizontal size={18} />
                </button>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="h-12 rounded-xl border border-[#E7DDD5] bg-white px-4 text-sm cursor-pointer focus:border-tan transition-colors"
                >
                  <option>Newest</option>
                  <option>Oldest</option>
                  <option>Name</option>
                </select>
              </div>
            </div>

            {/* Loading / error / empty states */}
            {loading && <p className="text-sm text-graytext mb-4">Loading your wardrobe...</p>}
            {loadError && <p className="text-sm text-red-600 mb-4">{loadError}</p>}
            {!loading && !loadError && filtered.length === 0 && (
              <p className="text-sm text-graytext">No items match your filters yet — try uploading something!</p>
            )}

            {/* The actual wardrobe grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-6">
              {filtered.map((item) => (
                <WardrobeCard
                  key={item.id}
                  item={item}
                  onDelete={handleDeleteItem}
                  isFavorite={item.favorite}
                  onToggleFavorite={handleToggleFavorite}
                  onOpen={setPreviewItem}
                  onResolveDuplicate={handleResolveDuplicate}
                />
              ))}
            </div>
          </main>
        </div>
      </div>

      {/* Mobile filter slide-over panel */}
      {showFilters && (
        <div className="fixed inset-0 bg-black/40 z-50 lg:hidden" onClick={() => setShowFilters(false)}>
          <div className="absolute right-0 top-0 h-full w-72 bg-white p-6 overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-semibold"></h3>
              <button onClick={() => setShowFilters(false)}><X size={20} /></button>
            </div>
            {FilterPanel}
          </div>
        </div>
      )}

      {/* Upload modal and single-item preview modal */}
      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onAdd={handleAddItem} />}
      {previewItem && <ItemPreviewModal item={previewItem} onClose={() => setPreviewItem(null)} />}

      {/* NEW — styled delete confirmation, replaces the native browser confirm() */}
      <ConfirmDialog
        open={!!confirmDeleteId}
        title="Remove this item?"
        message="This will permanently delete it from your wardrobe."
        onConfirm={confirmDeleteItem}
        onCancel={() => setConfirmDeleteId(null)}
      />
      <FooterMini />
    </div>
  );
}