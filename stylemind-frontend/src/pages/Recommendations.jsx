// pages/Recommendations.jsx
import { useState, useEffect } from "react"; // useEffect ADDED — needed for the localStorage sync below
import { useNavigate } from "react-router-dom";
import { MapPin } from "lucide-react";
import Navbar from "../components/Navbar";
import FooterMini from "../components/FooterMini";
import { occasionOptions, stylePreferenceOptions, getWeatherBucket } from "../mock/outfits";
import { getOutfitRecommendations, saveOutfit } from "../lib/api";
import { getCurrentLocation } from "../lib/geolocation";
import {getServerStartedAt} from "../lib/api"

const STORAGE_KEY = "stylemind_last_recommendation";
// ===================== CHANGE START =====================
// NEW — two extra localStorage keys: one stamps "the user was last seen
// here at time X" (updated periodically while the page is open), the
// other remembers which backend boot we last talked to.
const LAST_ACTIVE_KEY = "stylemind_recs_last_active";
const SERVER_STARTED_KEY = "stylemind_recs_server_started_at";
const INACTIVITY_LIMIT_MS = 2 * 60 * 1000; // 2 minutes

function loadSaved() {
  try {
    // If the user was away from this page for 2+ minutes, treat the
    // saved recommendation as stale and drop it before even reading it.
    const lastActive = Number(localStorage.getItem(LAST_ACTIVE_KEY) || 0);
    if (Date.now() - lastActive > INACTIVITY_LIMIT_MS) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}
// ===================== CHANGE END =====================

export default function Recommendations({ user, onLogout }) {
  const navigate = useNavigate();
  const saved0 = loadSaved(); // read once per mount, used only to seed initial state below

  // Each of these restores from localStorage (via saved0) instead of
  // always starting from a blank default.
  const [occasion, setOccasion] = useState(saved0?.occasion ?? occasionOptions[0]);
  const [tempC, setTempC] = useState(saved0?.tempC ?? 22);
  const [style, setStyle] = useState(saved0?.style ?? "safe");
  const [recommendations, setRecommendations] = useState(saved0?.recommendations ?? []);
  const [weather, setWeather] = useState(saved0?.weather ?? null);

  // rainNudge is the backend's purely-informational { icon, message }
  // umbrella nudge (null when it's not rainy / no live weather). visibleCount
  // controls how many of the already-fetched pool of outfits (up to
  // browse_pool_size on the backend) are shown; "Browse more" just raises
  // this number instead of hitting the network again. Both are restored
  // from localStorage on mount, so a refresh keeps whatever you'd already
  // revealed via "Browse more" instead of collapsing back to 5.
  const [rainNudge, setRainNudge] = useState(saved0?.rainNudge ?? null);
  const [visibleCount, setVisibleCount] = useState(5);

  // Location persists exactly like the other preferences (occasion/tempC/
  // style), instead of silently resetting to "off" on every refresh or
  // re-generate. It only clears when Reset is clicked.
  const [locationCoords, setLocationCoords] = useState(saved0?.locationCoords ?? null);
  const [locationStatus, setLocationStatus] = useState(saved0?.locationStatus ?? "off");

  const [selectedIndex, setSelectedIndex] = useState(0);
  const recommendation = recommendations[selectedIndex] || null;
  // true if this outfit had to reach into an off-season item via the
  // backend's season_fallback flag (src/recommend/filtering.py).
  // detail view banner
  const recommendationHasFallback = recommendation
  ? [recommendation.top, recommendation.bottom, recommendation.jacket].some((p) => p?.season_fallback || p?.off_season)
  : false;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const weatherBucket = getWeatherBucket(tempC);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      occasion, tempC, style, recommendations, weather, locationCoords, locationStatus,
      rainNudge,
    }));
  }, [occasion, tempC, style, recommendations, weather, locationCoords, locationStatus, rainNudge]);

  // NEW — periodically stamps "I'm still here", so a LATER mount can tell
  // whether the user was away for 2+ minutes (loadSaved() above reads this)
  useEffect(() => {
    function stamp() { localStorage.setItem(LAST_ACTIVE_KEY, String(Date.now())); }
    stamp();
    const interval = setInterval(stamp, 15000); // re-stamp every 15s while the page stays open
    return () => clearInterval(interval);
  }, []);

  // NEW — detects a backend restart: compares the server's boot timestamp
  // to whatever we saw last time. A mismatch means the backend process
  // restarted since we last generated a recommendation, so cached item
  // data could be stale — clear it to be safe.
  useEffect(() => {
    getServerStartedAt()
      .then((startedAt) => {
        const lastKnown = localStorage.getItem(SERVER_STARTED_KEY);
        if (lastKnown && lastKnown !== String(startedAt)) {
          localStorage.removeItem(STORAGE_KEY);
          setRecommendations([]);
          setWeather(null);
          setRainNudge(null);
        }
        localStorage.setItem(SERVER_STARTED_KEY, String(startedAt));
      })
      .catch(() => {}); // backend unreachable on mount — nothing to compare, skip silently
  }, []);
  // Triggers the browser's native GPS permission prompt, or turns location off if already on
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

  async function handleGenerate() {
    setLoading(true);
    setError("");
    setSaved(false);
    setWeather(null);
    try {
      // Priority: GPS coords (if location is on) > manual slider
      // topK controls how many candidates the backend scores and returns
      // as the browse pool (see initialCount/"Browse more" below).
      const { weather: weatherInfo, results, initialCount, rainNudge: nudge } = await getOutfitRecommendations({
        tempC,
        lat: locationCoords?.lat,
        lon: locationCoords?.lon,
        intent: occasion,
        stylePreference: style,
        topK: 5,
      });
      setWeather(weatherInfo);
      // Sort by final_score descending so higher-ranked outfits always
      // display first. The backend already sorts its main pass, but its
      // "backfill" pass (used when there aren't enough distinct items to
      // fill the pool) appends extra outfits at the end without re-merging
      // them into the overall score order, so we guarantee it here too.
      const sortedResults = [...results].sort((a, b) => b.final_score - a.final_score);
      setRecommendations(sortedResults);
      setRainNudge(nudge);
      // Backend already returns the full browse pool; only reveal
      // initialCount up front and let "Browse more" page into the rest
      // that's already sitting in `results`.
      setVisibleCount(initialCount || 5);
      setSelectedIndex(0);
      if (results.length === 0) {
        setError("No matching outfit found in your wardrobe for these preferences.");
      }
      // Scrolls back to the top so the newly generated recommendation
      // (weather card, option picker, etc.) is visible from the start.
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setOccasion(occasionOptions[0]);
    setTempC(22);
    setStyle("safe");
    setLocationCoords(null);
    setLocationStatus("off");
    setRecommendations([]);
    setSelectedIndex(0);
    setError("");
    setSaved(false);
    setWeather(null);
    setRainNudge(null);
    setVisibleCount(5);
  }

  function handleSelectRecommendation(index) {
    setSelectedIndex(index);
    setSaved(false);
  }

  async function handleSaveOutfit() {
    if (!recommendation) return;
    try {
      await saveOutfit({
        top: recommendation.top?.id,
        bottom: recommendation.bottom?.id,
        jacket: recommendation.jacket?.id,
        occasion,
        // Prefer the real resolved weather temp, and only fall back to the
        // slider value when there's no live weather (location was off).
        tempC: weather?.temp_c ?? tempC,
        locationName: weather?.location_name,
        region: weather?.region,
        country: weather?.country,
        stylePreference: style,
      });
      setSaved(true);
    } catch (err) {
      setError(err.message || "Failed to save outfit");
    }
  }

  return (
    <div className="min-h-screen bg-[#FBF8F5] flex flex-col">
      <Navbar user={user} onLogout={onLogout} />

      <div className="px-4 sm:px-8 py-8 flex-1">
        <div className="flex flex-col lg:flex-row gap-8">
          <aside className="w-full lg:w-[300px] flex-shrink-0 rounded-2xl p-6 border border-[#E7D8CD] bg-[#F7E6D9] h-fit">
            <h2 className="text-lg font-semibold text-ink mb-4" style={{ fontFamily: "'Playfair Display', serif" }}>
              Preferences
            </h2>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Occasion</label>
              <select
                value={occasion}
                onChange={(e) => setOccasion(e.target.value)}
                className="w-full border border-[#E7DDD5] rounded-xl px-3 py-2.5 text-sm text-ink bg-white outline-none"
              >
                {occasionOptions.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Weather</label>
              <button
                onClick={toggleLocation}
                disabled={locationStatus === "requesting"}
                className={`w-full flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-xs font-medium border transition-colors ${
                  locationStatus === "on"
                    ? "border-green-300 bg-green-50 text-green-700"
                    : locationStatus === "requesting"
                    ? "border-amber-300 bg-amber-50 text-amber-700 animate-pulse"
                    : "border-[#E7DDD5] bg-white text-graytext hover:border-tan"
                }`}
              >
                <MapPin size={12} />
                {locationStatus === "on" ? "Location on. Tap to turn off." : locationStatus === "requesting" ? "Requesting…" : "Turn on location"}
              </button>
              {locationStatus === "denied" && (
                <p className="text-[11px] text-red-500 mt-1">Permission denied, use the temperature slider instead.</p>
              )}
              <p className="text-xs text-graytext mt-1">When location is on, live weather is used instead of the slider below.</p>
            </div>

            <div className="mb-5">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">
                Temperature (fallback) <span className="text-ink font-semibold normal-case">{tempC}°C</span>
              </label>
              <input
                type="range" min="0" max="40" value={tempC}
                onChange={(e) => setTempC(Number(e.target.value))}
                className="w-full accent-ink"
                disabled={locationStatus === "on"}
              />
              <p className="text-xs text-graytext mt-1">Weather bucket: <span className="text-ink font-medium">{weatherBucket}</span></p>
            </div>

            <div className="mb-6">
              <label className="text-xs font-bold text-gray-500 uppercase block mb-2">Style</label>
              <div className="flex gap-2">
                {stylePreferenceOptions.map((s) => (
                  <button
                    key={s.value}
                    onClick={() => setStyle(s.value)}
                    className={`flex-1 py-2 rounded-xl text-xs border ${style === s.value ? "border-ink bg-white text-ink font-medium" : "border-[#E7DDD5] text-graytext"}`}
                  >
                    {s.value === "safe" ? "Safe" : "Bold"}
                  </button>
                ))}
              </div>
              <p className="text-xs text-graytext mt-1">{stylePreferenceOptions.find((s) => s.value === style)?.label}</p>
            </div>

            <button
              onClick={handleGenerate}
              disabled={loading}
              className="w-full py-3 rounded-xl text-white font-medium bg-gradient-to-r from-[#7C3AED] to-[#F97373] hover:opacity-90 transition mb-3 disabled:opacity-60"
            >
              {loading ? "Generating..." : "Generate Outfits"}
            </button>
            <button onClick={handleReset} className="w-full py-3 rounded-xl border border-[#E7DDD5] bg-white text-sm text-ink">
              Reset
            </button>
          </aside>

          <main className="flex-1 min-w-0">
            {error && (
              <div className="rounded-2xl border border-red-200 bg-red-50 text-red-700 text-sm p-4 mb-6">{error}</div>
            )}

            {weather && (
              <div className="rounded-2xl border border-[#E7D8CD] bg-gradient-to-r from-[#F7E6D9] to-[#F3D9E8] p-4 mb-6 flex items-center gap-4">
                <div className="text-3xl">🌤️</div>
                <div>
                  <p className="text-sm font-semibold text-ink">
                    {Math.round(weather.temp_c)}°C in {[weather.location_name, weather.region, weather.country].filter(Boolean).join(", ")}
                  </p>
                  <p className="text-xs text-graytext capitalize">
                    {weather.description}
                    {weather.feels_like_c != null && ` • feels like ${Math.round(weather.feels_like_c)}°C`}
                    {weather.humidity != null && ` • ${weather.humidity}% humidity`}
                  </p>
                </div>
              </div>
            )}

            {/* Rain nudge — styled to match the weather card above it. */}
            {rainNudge && (
              <div className="rounded-2xl border border-[#E7D8CD] bg-gradient-to-r from-[#F7E6D9] to-[#F3D9E8] p-4 mb-6 flex items-center gap-4">
                <div className="text-3xl">☔</div>
                <div>
                  <p className="text-sm font-semibold text-ink">Rain expected</p>
                  <p className="text-xs text-graytext capitalize">{rainNudge.message}</p>
                </div>
              </div>
            )}

            {recommendations.length === 0 && !error && !loading && (
              <div className="rounded-2xl border border-[#EAEAEA] bg-white p-10 text-center text-graytext text-sm">
                Set your preferences and click "Generate Outfits" to see recommendations.
              </div>
            )}

            {recommendations.length > 1 && (
              <>
                <div className="mb-3">
                  <p className="text-xs text-graytext">
                    Showing {Math.min(visibleCount, recommendations.length)} of {recommendations.length} options generated
                  </p>
                </div>
                <div className="flex gap-3 mb-3 overflow-x-auto pb-1">
                {recommendations.slice(0, visibleCount).map((rec, i) => {
                  // card thumbnail badge
                  const hasFallback = [rec.top, rec.bottom, rec.jacket].some((p) => p?.season_fallback || p?.off_season);
                  return (
                    <button
                      key={i}
                      onClick={() => handleSelectRecommendation(i)}
                      className={`flex-shrink-0 w-32 rounded-xl border-2 p-2 text-left transition-all relative ${
                        i === selectedIndex ? "border-ink bg-white shadow-sm" : "border-[#EAEAEA] bg-white/60 hover:border-[#D8C7BC]"
                      }`}
                    >
                      <div className="w-full h-20 rounded-lg bg-[#F3E4E8] overflow-hidden flex">
                        {[rec.top, rec.bottom, rec.jacket].filter(Boolean).map((p, j) => (
                          <img
                            key={j}
                            src={p.processedImageUrl || p.imageUrl}
                            alt={p.category}
                            className="flex-1 h-full min-w-0 object-contain p-0.5"
                          />
                        ))}
                      </div>
                      <p className="text-[11px] font-medium text-ink mt-1.5">Option {i + 1}</p>
                      <p className="text-[10px] text-graytext">{Math.round(rec.final_score * 100)}% match</p>
                      {hasFallback && (
                        <span className="absolute top-1.5 right-1.5 bg-amber-100 text-amber-700 text-[9px] font-medium px-1.5 py-0.5 rounded-full">
                          off-season
                        </span>
                      )}
                    </button>
                  );
                })}
                </div>
                {/* "Browse more" — styled like the page's other secondary
                    buttons (Reset / Save Outfit): bordered white rounded-xl. */}
                <div className="mb-6">
                  {visibleCount < recommendations.length && (
                    <button
                      onClick={() => setVisibleCount((c) => Math.min(c + 5, recommendations.length))}
                      className="px-4 py-2.5 rounded-xl border border-[#D8B8A8] bg-[#F7E6D9] text-sm text-ink hover:bg-[#F2D8C7] transition-colors"
                    >
                      Browse more ({recommendations.length - visibleCount} left)
                    </button>
                  )}
                </div>
              </>
            )}

            {recommendation && (
              <div className="rounded-2xl border border-[#EAEAEA] bg-white p-6 mb-8">
                <h2 className="text-xl font-semibold text-ink mb-1" style={{ fontFamily: "'Playfair Display', serif" }}>
                  Recommended for you ✨
                </h2>
                <p className="text-sm text-[#ac1c1c] mb-1">Perfect for {occasion}</p>
                <p className={`text-xs text-graytext ${recommendationHasFallback ? "mb-1" : "mb-6"}`}>
                  Match score: {Math.round(recommendation.final_score * 100)}%
                </p>
                {recommendationHasFallback && (
                  <p className="text-xs text-amber-700 mb-6">
                    ⚠ Off season pick. Nothing in your wardrobe matched today’s weather better.
                  </p>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {["top", "bottom", "jacket"].map((slot) => {
                    const piece = recommendation[slot];
                    if (!piece) return null;
                    return (
                      <div key={slot} className={`flex items-center gap-3 rounded-xl border border-[#EAEAEA] p-3 relative ${slot === "jacket" ? "sm:col-span-2" : ""}`}>
                        {(piece.processedImageUrl || piece.imageUrl) && (
                          <img
                            src={piece.processedImageUrl || piece.imageUrl}
                            alt={piece.category}
                            className="w-20 h-20 rounded-lg object-contain bg-[#F3E4E8] p-0.5 flex-shrink-0"
                          />
                        )}
                        <div>
                          <div className="text-sm font-medium text-ink">
                            {piece.category}
                            {slot === "jacket" && <span className="text-xs text-graytext font-normal"> (optional layer)</span>}
                          </div>
                          <div className="text-xs text-graytext">{piece.texture} • {piece.season}</div>
                        </div>
                        
                        {(piece.season_fallback || piece.off_season) && (
                          <span className="absolute top-2 right-2 bg-amber-100 text-amber-700 text-[9px] font-medium px-1.5 py-0.5 rounded-full">
                            off-season
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>

                <div className="flex flex-col sm:flex-row gap-3 mt-6">
                  <button
                    onClick={() =>
                      navigate("/tryon", {
                        state: {
                          outfitItems: [recommendation.top, recommendation.bottom, recommendation.jacket].filter(Boolean),
                        },
                      })
                    }
                    className="flex-1 py-3 rounded-xl bg-ink text-white text-sm font-medium"
                  >
                    TryOn
                  </button>
                  <button
                    onClick={handleSaveOutfit}
                    disabled={saved}
                    className="flex-1 py-3 rounded-xl border border-[#EAEAEA] text-sm text-ink disabled:opacity-60"
                  >
                    {saved ? "Saved ✓" : "Save Outfit"}
                  </button>
                </div>
                {saved && (
                  <p className="text-xs text-graytext mt-2">
                    Saved to your account, view it anytime on the Outfits page.
                  </p>
                )}
              </div>
            )}
          </main>
        </div>
      </div>

      <FooterMini />
    </div>
  );
}