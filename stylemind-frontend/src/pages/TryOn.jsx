import { useState, useEffect, useRef } from "react";import {
  User,
  Heart,
  RotateCcw,
  ChevronRight,
  ChevronLeft,
  Check,
  Save,
  Trash2,
  X,
  Pencil,
} from "lucide-react";

import Navbar from "../components/Navbar";
import FooterMini from "../components/FooterMini";
import { useLocation } from "react-router-dom";
import { startTryOn, getTryOnStatus, getWardrobe, getServerStartedAt, cancelTryOn } from "../lib/api";

import genericModelShorts from "../assets/generic-model.png";
import genericModelPant from "../assets/generic-model-pant.png";
import genericModelShortSkirt from "../assets/generic-model-short-skirt.png";
import genericModelLongSkirt from "../assets/generic-model-long-skirt.png";

/* =========================================================
   MODEL OPTIONS
========================================================= */

const MODEL_OPTIONS = [
  {
    id: "shorts",
    label: "Model 1",
    image: genericModelShorts,
  },
  {
    id: "pants",
    label: "Model 2",
    image: genericModelPant,
  },
  {
    id: "short-skirt",
    label: "Model 3",
    image: genericModelShortSkirt,
  },
  {
    id: "long-skirt",
    label: "Model 4",
    image: genericModelLongSkirt,
  },
];

// ===================== CHANGE START =====================
// NEW — lets an in-progress (or just-completed) try-on survive navigating
// to another page and back, since the actual generation happens in a
// background thread on the server regardless of whether this component
// is mounted. Cleared only when the user explicitly starts a new try-on,
// resets, or the backend has genuinely restarted since (detected via
// getServerStartedAt(), same mechanism as Recommendations.jsx).
const TRYON_STORAGE_KEY = "stylemind_active_tryon";

// ===================== CHANGE START =====================
// CHANGED — now also stores WHICH items were selected, not just the
// tryon job id. Without this, remounting after navigating away restored
// the generation STATUS correctly but showed a blank selection, making
// the page look reset even though the job was still genuinely running.
function saveActiveTryon(tryonId, serverStartedAt, selection, modelId) {
  try {
    localStorage.setItem(TRYON_STORAGE_KEY, JSON.stringify({ tryonId, serverStartedAt, selection, modelId }));
  } catch {}
}
// ===================== CHANGE END =====================
function clearActiveTryon() {
  try { localStorage.removeItem(TRYON_STORAGE_KEY); } catch {}
}
function loadActiveTryon() {
  try {
    return JSON.parse(localStorage.getItem(TRYON_STORAGE_KEY) || "null");
  } catch {
    return null;
  }
}
// ===================== CHANGE END =====================

/* =========================================================
   WARDROBE CATEGORIES

   These should match the categories coming from your backend.
========================================================= */

const TOP_CATEGORIES = [
  "Shirt",
  "Top",
  "Warmwear",
];

const BOTTOM_CATEGORIES = [
  "Formal_Pant",
  "Pants",
  "Shorts",
];

const JACKET_CATEGORIES = [
  "Jacket",
  "Blazer",
  "Coat",
  "Outerwear",
];

const SKIRT_CATEGORIES = [
  "Skirt",
];

const DRESS_CATEGORIES = [
  "Dress",
];

/* =========================================================
   SLOTS — used to build the edit modal generically
========================================================= */

const OUTFIT_SLOTS = [
  { key: "top", label: "Top" },
  { key: "bottom", label: "Bottom" },
  { key: "jacket", label: "Jacket" },
  { key: "skirt", label: "Skirt" },
  { key: "dress", label: "Dress" },
];

/* =========================================================
   HELPER
========================================================= */

function getItemImage(item) {
  return item?.processedImageUrl || item?.imageUrl;
}

/* =========================================================
   HORIZONTAL WARDROBE ROW
========================================================= */

function WardrobeRow({
  title,
  items,
  selectedItem,
  onSelect,
  optional = false,
}) {
  const scrollLeft = () => {
    const container = document.getElementById(
      `wardrobe-${title.replace(/\s/g, "-")}`
    );

    if (container) {
      container.scrollBy({
        left: -300,
        behavior: "smooth",
      });
    }
  };

  const scrollRight = () => {
    const container = document.getElementById(
      `wardrobe-${title.replace(/\s/g, "-")}`
    );

    if (container) {
      container.scrollBy({
        left: 300,
        behavior: "smooth",
      });
    }
  };

  return (
    <div className="mb-7">
      {/* HEADER */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-ink">
          {title}

          {optional && (
            <span className="ml-1 text-xs font-normal text-graytext">
              (Optional)
            </span>
          )}
        </h3>

        {items.length > 5 && (
          <div className="flex gap-1">
            <button
              onClick={scrollLeft}
              className="w-7 h-7 rounded-full border border-[#E8E1DC] bg-white flex items-center justify-center hover:bg-[#F8F2EE] transition"
            >
              <ChevronLeft size={15} />
            </button>

            <button
              onClick={scrollRight}
              className="w-7 h-7 rounded-full border border-[#E8E1DC] bg-white flex items-center justify-center hover:bg-[#F8F2EE] transition"
            >
              <ChevronRight size={15} />
            </button>
          </div>
        )}
      </div>

      {/* HORIZONTAL SCROLLER */}
      <div className="relative">
        <div
          id={`wardrobe-${title.replace(/\s/g, "-")}`}
          className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin"
          style={{
            scrollbarWidth: "thin",
          }}
        >
          {/* NONE OPTION FOR OPTIONAL CATEGORIES */}
          {optional && (
            <button
              onClick={() => onSelect(null)}
              className={`relative flex-shrink-0 w-24 h-24 rounded-xl border-2 bg-[#FAF8F5] flex items-center justify-center transition ${
                selectedItem === null
                  ? "border-[#8F1D2C]"
                  : "border-[#EAEAEA] hover:border-[#D9C4A3]"
              }`}
            >
              <div className="text-2xl text-gray-300">∅</div>

              {selectedItem === null && (
                <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-[#8F1D2C] text-white flex items-center justify-center">
                  <Check size={12} />
                </div>
              )}
            </button>
          )}

          {/* ITEMS */}
          {items.map((item) => {
            const selected = selectedItem?.id === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onSelect(item)}
                className={`relative flex-shrink-0 w-24 h-24 rounded-xl border-2 overflow-hidden bg-[#FAF8F5] transition ${
                  selected
                    ? "border-[#8F1D2C] shadow-sm"
                    : "border-[#EAEAEA] hover:border-[#D9C4A3]"
                }`}
              >
                <img
                  src={getItemImage(item)}
                  alt={item.category || "Wardrobe item"}
                  className="w-full h-full object-contain"
                />

                {selected && (
                  <div className="absolute top-1 right-1 w-5 h-5 rounded-full bg-[#8F1D2C] text-white flex items-center justify-center">
                    <Check size={12} />
                  </div>
                )}
              </button>
            );
          })}

          {items.length === 0 && (
            <div className="text-xs text-graytext py-6">
              No items available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   MAIN COMPONENT
========================================================= */

export default function TryOn({ user, onLogout }) {
  const location = useLocation();

  const outfitFromChat =
    location.state?.outfitItems || null;

  /* -------------------------------------------------------
     INITIAL OUTFIT FROM CHAT
  ------------------------------------------------------- */

  const initialTop =
    outfitFromChat?.find((item) =>
      TOP_CATEGORIES.includes(item.category)
    ) || null;

  const initialBottom =
    outfitFromChat?.find((item) =>
      BOTTOM_CATEGORIES.includes(item.category)
    ) || null;

  const initialJacket =
    outfitFromChat?.find((item) =>
      JACKET_CATEGORIES.includes(item.category)
    ) || null;

  const initialSkirt =
    outfitFromChat?.find((item) =>
      SKIRT_CATEGORIES.includes(item.category)
    ) || null;

  const initialDress =
    outfitFromChat?.find((item) =>
      DRESS_CATEGORIES.includes(item.category)
    ) || null;

  /* -------------------------------------------------------
     MODEL
  ------------------------------------------------------- */

  const [selectedModelId, setSelectedModelId] =
    useState(null);

  const [photoFile, setPhotoFile] =
    useState(null);

  const [photoPreview, setPhotoPreview] =
    useState(null);

  /* -------------------------------------------------------
     WARDROBE
  ------------------------------------------------------- */

  const [wardrobe, setWardrobe] = useState([]);

  const [wardrobeLoading, setWardrobeLoading] =
    useState(true);

  const [wardrobeError, setWardrobeError] =
    useState(null);

  /* -------------------------------------------------------
     SELECTED CLOTHING
  ------------------------------------------------------- */

  const [selectedTop, setSelectedTop] =
    useState(initialTop);

  const [selectedBottom, setSelectedBottom] =
    useState(initialBottom);

  const [selectedJacket, setSelectedJacket] =
    useState(initialJacket);

  const [selectedSkirt, setSelectedSkirt] =
    useState(initialSkirt);

  const [selectedDress, setSelectedDress] =
    useState(initialDress);

  /* -------------------------------------------------------
     TRY ON
  ------------------------------------------------------- */

  const [tryonStatus, setTryonStatus] =
    useState(null);

  const [resultUrl, setResultUrl] =
    useState(null);

  const [error, setError] =
    useState(null);

  const [activeTryonId, setActiveTryonId] = 
    useState(null); // NEW — needed so Cancel knows which job to cancel
  
  const [submittedItems, setSubmittedItems] = 
    useState([]); // NEW — frozen snapshot of what's actually being generated, so changing your selection mid-generation doesn't change what this shows

  // NEW — tracks the active polling interval so it can be properly
  // cleared (both on completion and on unmount), instead of the old
  // raw setInterval that just kept ticking uselessly after navigating away
  const pollIntervalRef = useRef(null);

  /* -------------------------------------------------------
     SAVED LOOKS (outfit combinations, no photo)
  ------------------------------------------------------- */

  const [savedLooks, setSavedLooks] =
    useState(() => {
      try {
        return JSON.parse(
          localStorage.getItem("stylemind-personal-looks") || "[]"
        );
      } catch {
        return [];
      }
    });

  /* -------------------------------------------------------
     SAVED TRY-ON PHOTOS (the generated result images)
  ------------------------------------------------------- */

  const [savedPhotos, setSavedPhotos] =
    useState(() => {
      try {
        return JSON.parse(
          localStorage.getItem("stylemind-tryon-photos") || "[]"
        );
      } catch {
        return [];
      }
    });

  /* -------------------------------------------------------
     EDIT SAVED LOOK MODAL
  ------------------------------------------------------- */
  const [viewingPhoto, setViewingPhoto] = useState(null); // NEW — which saved photo (if any) is open in the lightbox
  const [editingLookId, setEditingLookId] = useState(null);
  const editingLook = savedLooks.find((l) => l.id === editingLookId) || null;

  /* =======================================================
     LOAD WARDROBE
  ======================================================= */

  useEffect(() => {
    getWardrobe()
      .then(setWardrobe)
      .catch((e) => setWardrobeError(e.message))
      .finally(() => setWardrobeLoading(false));
  }, []);

  // NEW — on mount, checks for a try-on that was already in progress (or
  // just finished) before the user navigated away, and resumes/restores
  // it instead of starting blank.
  useEffect(() => {
    const active = loadActiveTryon();
    if (!active) return;

    // ===================== CHANGE START =====================
    // NEW — arriving here via "Try on Avatar" from Recommendations/Chatbot
    // (outfitFromChat is set) means the user explicitly wants to try a
    // DIFFERENT combination right now — don't resume an old, unrelated
    // in-progress job over it.
    if (outfitFromChat) {
      clearActiveTryon();
      return;
    }
    // ===================== CHANGE END =====================

    (async () => {
      try {
        const currentServerStartedAt = await getServerStartedAt();
        if (currentServerStartedAt !== active.serverStartedAt) {
          clearActiveTryon();
          return;
        }

        // ===================== CHANGE START =====================
        // NEW — restore the actual selected items (not just the status)
        // once the real wardrobe has loaded, so the selection UI doesn't
        // look blank/reset while the job is still genuinely processing
                if (active.selection && wardrobe.length > 0) {
          const findById = (id) => wardrobe.find((w) => w.id === id) || null;
          if (active.selection.topId) setSelectedTop(findById(active.selection.topId));
          if (active.selection.bottomId) setSelectedBottom(findById(active.selection.bottomId));
          if (active.selection.jacketId) setSelectedJacket(findById(active.selection.jacketId));
          if (active.selection.skirtId) setSelectedSkirt(findById(active.selection.skirtId));
          if (active.selection.dressId) setSelectedDress(findById(active.selection.dressId));
        }

        // ===================== CHANGE START =====================
        // NEW — THE actual fix: restores which model photo was selected,
        // so photoFile/photoPreview aren't null after remounting. Without
        // this, the "Generating…" button never rendered at all (it's
        // gated on photoFile existing), making a still-running job look
        // like it had silently stopped.
        if (active.modelId) {
          const model = MODEL_OPTIONS.find((m) => m.id === active.modelId);
          if (model) {
            setSelectedModelId(model.id);
            setPhotoPreview(model.image);
            try {
              const res = await fetch(model.image);
              const blob = await res.blob();
              const file = new File([blob], `${model.id}-model.jpg`, { type: blob.type || "image/jpeg" });
              setPhotoFile(file);
            } catch {
              // non-fatal — status/result restoration below still proceeds either way
            }
          }
        }
        // ===================== CHANGE END =====================

        const data = await getTryOnStatus(active.tryonId);
        if (data.status === "done") {
          setTryonStatus("done");
          setResultUrl(data.resultImageUrl);
        } else if (data.status === "failed") {
          setTryonStatus("failed");
          setError(data.error_message || "Generation failed — try again.");
        } else {
          setTryonStatus("processing");
          pollUntilDone(active.tryonId);
        }
      } catch {
        clearActiveTryon();
      }
    })();
  }, [wardrobe]); {/* CHANGED — dependency array was [], now depends on wardrobe so the id-lookup above has real data to search once it loads */}

  /* =======================================================
     PERSIST SAVED LOOKS
  ======================================================= */

  useEffect(() => {
    localStorage.setItem(
      "stylemind-personal-looks",
      JSON.stringify(savedLooks)
    );
  }, [savedLooks]);

  /* =======================================================
     PERSIST SAVED PHOTOS
  ======================================================= */

  useEffect(() => {
    localStorage.setItem(
      "stylemind-tryon-photos",
      JSON.stringify(savedPhotos)
    );
  }, [savedPhotos]);

  /* =======================================================
     MODEL SELECTION
  ======================================================= */

  async function handleSelectModel(option) {
    // ===================== CHANGE START =====================
    // NEW — refuse to change the model while a generation is actively
    // processing. The job in progress is already locked to whatever was
    // submitted (frozen in submittedItems) — switching models here doesn't
    // affect that job at all, it just corrupts the UI by clearing
    // tryonStatus out from under an in-progress poll.
    if (tryonStatus === "processing") return;
    // ===================== CHANGE END =====================

    setError(null);
    setResultUrl(null);
    setTryonStatus(null);
    setSelectedModelId(option.id);
    setPhotoPreview(option.image);

    try {
      const response = await fetch(option.image);

      const blob = await response.blob();

      const file = new File(
        [blob],
        `${option.id}-model.jpg`,
        {
          type: blob.type || "image/jpeg",
        }
      );

      setPhotoFile(file);
    } catch {
      setError(
        "Couldn't load that model photo — try another one."
      );
    }
  }

  /* =======================================================
     SELECT TOP
  ======================================================= */

  function handleSelectTop(item) {
    setSelectedTop((prev) =>
      prev?.id === item?.id ? null : item
    );

    setResultUrl(null);
  }

  /* =======================================================
     SELECT BOTTOM
  ======================================================= */

  function handleSelectBottom(item) {
    setSelectedBottom((prev) =>
      prev?.id === item?.id ? null : item
    );

    setResultUrl(null);
  }

  /* =======================================================
     SELECT JACKET
  ======================================================= */

  function handleSelectJacket(item) {
    setSelectedJacket(item);

    setResultUrl(null);
  }

  /* =======================================================
     SELECT SKIRT
  ======================================================= */

  function handleSelectSkirt(item) {
    setSelectedSkirt(item);

    /*
      If a skirt is selected, remove bottom and dress.

      This prevents the UI from showing:
      Top + Pants + Skirt
      or
      Skirt + Dress
      at the same time.
    */

    if (item) {
      setSelectedBottom(null);
      setSelectedDress(null);
    }

    setResultUrl(null);
  }

  /* =======================================================
     SELECT DRESS
  ======================================================= */

  function handleSelectDress(item) {
    setSelectedDress(item);

    /*
      A dress replaces top + bottom + skirt entirely —
      keeps the UI from showing Top + Bottom + Dress together.
    */

    if (item) {
      setSelectedTop(null);
      setSelectedBottom(null);
      setSelectedSkirt(null);
    }

    setResultUrl(null);
  }

  /* =======================================================
     RESET — clears the clothing selection AND the chosen
     model, so the user lands back on "choose a model" with
     an empty preview area, per their request.
  ======================================================= */

  function handleReset() {
    setSelectedTop(null);
    setSelectedBottom(null);
    setSelectedJacket(null);
    setSelectedSkirt(null);
    setSelectedDress(null);

    setSelectedModelId(null);
    setPhotoFile(null);
    setPhotoPreview(null);

   setResultUrl(null);
    setTryonStatus(null);
    setError(null);
    clearActiveTryon(); // NEW
  }

  /* =======================================================
     SAVE LOOK (outfit combo only, no generated photo)
  ======================================================= */

  function handleSaveLook() {
    if (
      !selectedTop &&
      !selectedBottom &&
      !selectedJacket &&
      !selectedSkirt &&
      !selectedDress
    ) {
      setError(
        "Choose at least one clothing item before saving."
      );

      return;
    }

    const newLook = {
      id: Date.now(),

      modelId: selectedModelId,

      top: selectedTop,

      bottom: selectedBottom,

      jacket: selectedJacket,

      skirt: selectedSkirt,

      dress: selectedDress,

      createdAt:
        new Date().toISOString(),
    };

    setSavedLooks((prev) => [
      newLook,
      ...prev,
    ]);

    setError(null);
  }

  /* =======================================================
     DELETE SAVED LOOK
  ======================================================= */

  function handleDeleteLook(id) {
    setSavedLooks((prev) =>
      prev.filter((look) => look.id !== id)
    );

    if (editingLookId === id) {
      setEditingLookId(null);
    }
  }

  /* =======================================================
     REMOVE A SINGLE PIECE FROM A SAVED LOOK (edit modal)
  ======================================================= */

  function handleRemovePieceFromLook(lookId, slotKey) {
    setSavedLooks((prev) =>
      prev.map((look) =>
        look.id === lookId ? { ...look, [slotKey]: null } : look
      )
    );
  }

  /* =======================================================
     SAVE THE GENERATED RESULT PHOTO
  ======================================================= */

  function handleSaveResultPhoto() {
    if (!resultUrl) return;
    const alreadySaved = savedPhotos.some((p) => p.url === resultUrl);
    if (alreadySaved) return;

    setSavedPhotos((prev) => [
      { id: Date.now(), url: resultUrl, createdAt: new Date().toISOString() },
      ...prev,
    ]);
  }

  /* =======================================================
     DELETE A SAVED PHOTO
  ======================================================= */

  function handleDeleteSavedPhoto(id) {
    setSavedPhotos((prev) => prev.filter((p) => p.id !== id));
  }

  /* =======================================================
     CORE GENERATE LOGIC — takes explicit args instead of
     reading straight from state, so it can be called right
     after loading a saved look (before React has re-rendered
     with the new state) as well as from the manual button.
  ======================================================= */

    async function runGenerate(photoFileArg, topId, bottomId, selection, modelId, itemsForDisplay) {
    if (!photoFileArg) {
      setError("Choose a model first.");
      return;
    }
    if (!topId && !bottomId) {
      setError("Pick at least one wardrobe item first.");
      return;
    }

    setError(null);
    setTryonStatus("processing");
    setResultUrl(null);
    setSubmittedItems(itemsForDisplay || []); // NEW — freezes the thumbnail strip to what's actually being generated

    try {
      const started = await startTryOn({
        photoFile: photoFileArg,
        topId,
        bottomId,
      });
      setActiveTryonId(started.id); // NEW
      // NEW — persists this try-on so it survives navigating away. Also
      // captures the server's current boot timestamp, so a later resume
      // can tell whether the backend has restarted since (in which case
      // the background thread is dead and shouldn't be "resumed")
      try {
                const startedAt = await getServerStartedAt();
        saveActiveTryon(started.id, startedAt, selection, modelId); // CHANGED — also pass which model, so it can be restored on resume
      } catch {
        // health check failed — still poll normally in this tab, it just
        // won't be resumable after a page refresh
      }
      pollUntilDone(started.id);
    } catch (e) {
      setError(e.message);
      setTryonStatus("failed");
      clearActiveTryon();
    }
  }

  /* =======================================================
     GENERATE TRY ON — manual button, used while building an
     outfit yourself in the Personal Styling / recommendation
     flow.
  ======================================================= */

  async function handleGenerate() {
    const topId = selectedDress ? undefined : selectedTop?.id;
    const bottomId = selectedDress?.id || selectedBottom?.id || selectedSkirt?.id;
    // ===================== CHANGE START =====================
    // NEW — captures the FULL selection (including jacket, which never
    // goes to the try-on API itself but still needs to display correctly
    // if the user navigates away and back)
    const selection = {
      topId: selectedTop?.id, bottomId: selectedBottom?.id, jacketId: selectedJacket?.id,
      skirtId: selectedSkirt?.id, dressId: selectedDress?.id,
    };
    const itemsForDisplay = [selectedTop, selectedBottom, selectedJacket, selectedSkirt, selectedDress].filter(Boolean);
    await runGenerate(photoFile, topId, bottomId, selection, selectedModelId, itemsForDisplay);
  }

  /* =======================================================
     LOAD SAVED LOOK — triggered by "Try On" on a saved look
     card. Loads the outfit + model into the workspace AND
     immediately generates the try-on, no extra click needed.
  ======================================================= */

  async function handleLoadLook(look) {
    setSelectedTop(look.top || null);
    setSelectedBottom(look.bottom || null);
    setSelectedJacket(look.jacket || null);
    setSelectedSkirt(look.skirt || null);
    setSelectedDress(look.dress || null);

    setResultUrl(null);
    setTryonStatus(null);
    setError(null);

    const model = MODEL_OPTIONS.find((m) => m.id === look.modelId);
    if (!model) {
      setError("This look doesn't have a model saved with it.");
      return;
    }

    setSelectedModelId(model.id);
    setPhotoPreview(model.image);

    let file = null;
    try {
      const res = await fetch(model.image);
      const blob = await res.blob();
      file = new File([blob], `${model.id}-model.jpg`, { type: blob.type || "image/jpeg" });
      setPhotoFile(file);
    } catch {
      setError("Couldn't load that model photo — try another one.");
      return;
    }

    const topId = look.dress ? undefined : look.top?.id;
    const bottomId = look.dress?.id || look.bottom?.id || look.skirt?.id;
    // CHANGED — pass the look's own items as the selection to persist
    const selection = {
      topId: look.top?.id, bottomId: look.bottom?.id, jacketId: look.jacket?.id,
      skirtId: look.skirt?.id, dressId: look.dress?.id,
    };
    const itemsForDisplay = [look.top, look.bottom, look.jacket, look.skirt, look.dress].filter(Boolean);
    await runGenerate(file, topId, bottomId, selection, model.id, itemsForDisplay);
  }

async function handleCancel() {
    const idToCancel = activeTryonId;
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    pollIntervalRef.current = null;
    setTryonStatus(null);
    setResultUrl(null);
    setSubmittedItems([]);
    clearActiveTryon();
    if (idToCancel) {
      try {
        await cancelTryOn(idToCancel);
      } catch {
        // even if the cancel request itself fails, the UI has already
        // moved on and won't be tracking/showing this job anymore
      }
    }
  }

  /* =======================================================
     POLL TRY ON STATUS
  ======================================================= */

  function pollUntilDone(tryonId) {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current); // guard against a duplicate poll ever running at once
    pollIntervalRef.current = setInterval(async () => {
      try {
        const data = await getTryOnStatus(tryonId);

        if (data.status === "done") {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setTryonStatus("done");
          setResultUrl(data.resultImageUrl);
          // NOT cleared from localStorage here on purpose — the result
          // should still show if the user navigates away and comes back;
          // only an explicit reset/new-generation clears it (see below)
        } else if (data.status === "failed") {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
          setTryonStatus("failed");
          setError(data.error_message || "Generation failed — try again.");
        }
      } catch {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
        setTryonStatus("failed");
        setError("Lost connection while checking try-on status.");
      }
    }, 4000);
  }

  // NEW — stops the polling interval if the user navigates away
  // mid-generation, so it doesn't keep running uselessly in the
  // background of this specific tab's memory (the actual server-side
  // generation is unaffected either way — this only stops THIS tab from
  // continuing to check on it while unmounted)
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  /* =======================================================
     RESET RESULT
  ======================================================= */

  function resetResult() {
    setResultUrl(null);
    setTryonStatus(null);
    setError(null);
    clearActiveTryon(); // NEW — "try a different combination" is an explicit fresh start
  }

  /* =======================================================
     FILTER WARDROBE
  ======================================================= */

  const tops = wardrobe.filter(
    (item) =>
      TOP_CATEGORIES.includes(
        item.category
      )
  );

  const bottoms = wardrobe.filter(
    (item) =>
      BOTTOM_CATEGORIES.includes(
        item.category
      )
  );

  const jackets = wardrobe.filter(
    (item) =>
      JACKET_CATEGORIES.includes(
        item.category
      )
  );

  const skirts = wardrobe.filter(
    (item) =>
      SKIRT_CATEGORIES.includes(
        item.category
      )
  );

  const dresses = wardrobe.filter(
    (item) =>
      DRESS_CATEGORIES.includes(
        item.category
      )
  );

  /* =======================================================
     CURRENT MODEL
  ======================================================= */

  const currentModel =
    MODEL_OPTIONS.find(
      (model) =>
        model.id === selectedModelId
    );

  const hasSelectedClothing =
    selectedTop || selectedBottom || selectedJacket || selectedSkirt || selectedDress;

  const resultAlreadySaved =
    resultUrl && savedPhotos.some((p) => p.url === resultUrl);

  /* =======================================================
     RENDER
  ======================================================= */

  return (
    <div className="min-h-screen bg-[#FBF8F5]">
      <Navbar
        user={user}
        onLogout={onLogout}
      />

      {/* =================================================
          MAIN
      ================================================= */}

      <main className="px-4 sm:px-6 lg:px-8 py-6">
        <div className="max-w-[1600px] mx-auto">

          {/* =================================================
              PAGE GRID
          ================================================= */}

          {/* CHANGED — added items-start. CSS Grid stretches every column in a
              row to match the TALLEST one by default (align-items: stretch) — that's
              exactly why "Choose Model" and "Personal Styling" were growing to match
              a taller sibling column with empty space at the bottom. items-start
              makes each column only as tall as its own content. */}
          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(430px,0.95fr)_125px] gap-5 items-start">

            {/* =================================================
                LEFT — PERSONAL STYLING
            ================================================= */}

            <section className="rounded-2xl border border-[#EAEAEA] bg-white overflow-hidden">

              {/* HEADER */}

              <div className="px-6 py-5 border-b border-[#EEE8E3] bg-gradient-to-r from-[#FFF8F5] to-white">
                <div className="flex items-center gap-3">

                  <div className="w-11 h-11 rounded-xl bg-[#F8E8E3] flex items-center justify-center text-[#8F1D2C]">
                    <User size={21} />
                  </div>

                  <div>
                    <h2 className="text-lg font-semibold text-ink">
                      Personal Styling
                    </h2>

                    <p className="text-xs text-graytext mt-0.5">
                      Build your own style by selecting each item.
                    </p>
                  </div>

                </div>
              </div>

              {/* WARDROBE */}

              <div className="p-6">

                {wardrobeLoading ? (
                  <div className="py-10 text-center text-sm text-graytext">
                    Loading your wardrobe…
                  </div>
                ) : wardrobeError ? (
                  <div className="py-10 text-center text-sm text-red-500">
                    {wardrobeError}
                  </div>
                ) : (
                  <>
                    <WardrobeRow
                      title="1. Choose a Top"
                      items={tops}
                      selectedItem={selectedTop}
                      onSelect={handleSelectTop}
                    />

                    <WardrobeRow
                      title="2. Choose a Bottom"
                      items={bottoms}
                      selectedItem={selectedBottom}
                      onSelect={handleSelectBottom}
                    />

                    <WardrobeRow
                      title="3. Choose a Jacket"
                      items={jackets}
                      selectedItem={selectedJacket}
                      onSelect={handleSelectJacket}
                      optional
                    />

                    <WardrobeRow
                      title="4. Choose a Skirt"
                      items={skirts}
                      selectedItem={selectedSkirt}
                      onSelect={handleSelectSkirt}
                      optional
                    />

                    <WardrobeRow
                      title="5. Choose a Dress"
                      items={dresses}
                      selectedItem={selectedDress}
                      onSelect={handleSelectDress}
                      optional
                    />
                  </>
                )}

                {/* =================================================
                    SAVE LOOK
                ================================================= */}

                <button
                  onClick={handleSaveLook}
                  className="w-full mt-2 py-3 rounded-xl bg-[#8F1D2C] text-white font-medium text-sm flex items-center justify-center gap-2 hover:bg-[#761623] transition"
                >
                  <Heart size={17} />
                  Save Look
                </button>

                {/* ERROR */}

                {error && (
                  <p className="text-xs text-red-500 text-center mt-3">
                    {error}
                  </p>
                )}

              </div>
            </section>

            {/* =================================================
                CENTER — MODEL PREVIEW
            ================================================= */}

            <section className="rounded-2xl border border-[#EAEAEA] bg-gradient-to-b from-[#F8E9DF] to-[#F5E7EA] min-h-[760px] relative overflow-hidden">

              {/* RESULT */}

              {resultUrl ? (
                <div className="h-full flex flex-col items-center justify-center p-6 relative">

                  {/* SAVE PHOTO — save the generated try-on image */}

                  <button
                    onClick={handleSaveResultPhoto}
                    className="absolute top-5 right-5 z-10 w-11 h-11 rounded-xl bg-white/80 backdrop-blur flex items-center justify-center hover:bg-white transition"
                    title={resultAlreadySaved ? "Already saved" : "Save this photo"}
                  >
                    <Heart
                      size={19}
                      className="text-[#8F1D2C]"
                      fill={resultAlreadySaved ? "#8F1D2C" : "none"}
                    />
                  </button>

                  <img
                    src={resultUrl}
                    alt="Try-on result"
                    className="max-h-[580px] max-w-full object-contain rounded-xl shadow-lg"
                  />

                  <button
                    onClick={resetResult}
                    className="mt-5 mb-8 text-sm text-graytext underline"
                  >
                    Try a different combination
                  </button>

                </div>
              ) : tryonStatus === "processing" ? (
                <div className="h-full min-h-[850px] flex items-center justify-center p-8 relative">
                  {photoPreview && (
                    <img
                      src={photoPreview}
                      alt="Selected model"
                      className="max-h-[620px] max-w-full object-contain opacity-40"
                    />
                  )}

                  <div className="absolute inset-0 flex items-center justify-center px-6">
                    <div className="bg-white rounded-2xl shadow-lg px-7 py-6 flex flex-col items-center text-center max-w-[300px]">
                      <div className="w-10 h-10 border-4 border-[#8F1D2C] border-t-transparent rounded-full animate-spin mb-4" />
                      <p className="text-base text-ink font-semibold">Generating your look…</p>
                      <p className="text-sm text-graytext mt-2">
                        This may take a few minutes. Feel free to browse other pages while it continues working in the background.
                      </p>
                      {/* NEW — lets the user actually stop this generation, instead of just watching it */}
                      <button
                        onClick={handleCancel}
                        className="mt-4 text-xs text-graytext underline hover:text-red-500 transition"
                      >
                        Cancel generation
                      </button>
                    </div>
                  </div>

                  {/* CHANGED — uses submittedItems (frozen at generation
                      start), NOT the live selectedTop/etc, so changing
                      your selection mid-generation doesn't alter what
                      this strip shows — it always reflects what's
                      actually being generated right now. Also moved from
                      bottom-5 to bottom-14 so it clears the disclaimer bar
                      at the very bottom of the panel instead of overlapping it. */}
                  {submittedItems.length > 0 && (
                    <div className="absolute bottom-14 right-5 bg-white/90 backdrop-blur rounded-xl p-2 shadow-sm flex gap-1.5">
                      {submittedItems.map((item) => (
                        <img
                          key={item.id}
                          src={getItemImage(item)}
                          alt={item.category}
                          className="w-10 h-10 object-contain rounded-lg border border-[#EAEAEA] bg-[#FAF8F5]"
                        />
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <>

                  {/* TOP CONTROLS */}

                  <div className="absolute top-5 left-5 z-10 flex flex-col gap-2">

                    <div className="px-3 py-2 rounded-xl bg-white/80 backdrop-blur text-xs font-medium text-ink">
                      Personal Look
                    </div>

                    {selectedModelId && (
                      <div className="px-3 py-2 rounded-xl bg-white/80 backdrop-blur text-xs text-graytext">
                        {currentModel?.label}
                      </div>
                    )}

                  </div>

                  {/* MODEL */}

                  <div className="h-full min-h-[850px] flex items-center justify-center p-8">

                    {photoPreview ? (
                      <img
                        src={photoPreview}
                        alt="Selected model"
                        className="max-h-[620px] max-w-full object-contain"
                      />
                    ) : (
                      <div className="text-center">

                        <div className="w-52 h-72 rounded-2xl border-2 border-dashed border-[#D9C4A3] flex items-center justify-center text-sm text-graytext px-8">
                          Choose one of the four models on the right
                        </div>

                      </div>
                    )}

                  </div>

                  {/* RESET — only control left, undo removed */}

                  <div className="absolute bottom-14 left-5 flex gap-2">

                    <button
                      onClick={handleReset}
                      className="w-11 h-11 rounded-xl bg-white/90 backdrop-blur flex items-center justify-center hover:bg-white transition"
                      title="Reset — clears outfit and model"
                    >
                      <RotateCcw size={18} />
                    </button>

                  </div>

                  {/* OUTFIT PREVIEW + GENERATE — stacked in the
                      bottom-right, so the user can see exactly what
                      they've picked right next to the action button. */}

                  <div className="absolute bottom-14 right-5 flex flex-col items-end gap-2">

                    {hasSelectedClothing && (
                      <div className="bg-white/90 backdrop-blur rounded-xl p-2 shadow-sm flex gap-1.5">
                        {[selectedTop, selectedBottom, selectedJacket, selectedSkirt, selectedDress]
                          .filter(Boolean)
                          .map((item) => (
                            <img
                              key={item.id}
                              src={getItemImage(item)}
                              alt={item.category}
                              className="w-10 h-10 object-contain rounded-lg border border-[#EAEAEA] bg-[#FAF8F5]"
                            />
                          ))}
                      </div>
                    )}

                    {photoFile && (
                      <button
                        onClick={handleGenerate}
                        disabled={
                          tryonStatus === "processing"
                        }
                        className="px-5 py-3 rounded-xl bg-[#8F1D2C] text-white text-sm font-medium shadow-lg hover:bg-[#761623] disabled:opacity-60 transition"
                      >
                        {tryonStatus === "processing"
                          ? "Generating…"
                          : "Generate Try-On"}
                      </button>
                    )}

                  </div>

                </>
              )}

              {/* CHANGED — moved out of the "no result" branch, so this
                  now shows in EVERY state (browsing, processing, and after
                  the result is generated), not just before generating.
                  Also redesigned from a small floating pill into a slim
                  full-width footer bar, which reads more cleanly than a
                  cramped box sitting in the middle of the preview area. */}
              <div className="absolute bottom-0 left-0 right-0 bg-white/85 backdrop-blur-sm border-t border-[#EEE0D8] py-2.5 px-4 text-center">
                <p className="text-[11px] text-graytext">
                  Results are AI-generated and may vary slightly from how the item actually looks in wardrobe.
                </p>
              </div>

            </section>

            {/* =================================================
                RIGHT — MODEL SELECTOR
            ================================================= */}

            <aside className="rounded-2xl border border-[#EAEAEA] bg-white p-3">

              <h3 className="text-xs font-semibold text-ink text-center mb-3">
                Choose Model
              </h3>

              <div className="flex h-[500px] lg:flex-col gap-3">

                {MODEL_OPTIONS.map(
                  (option) => {

                    const selected =
                      selectedModelId ===
                      option.id;

                    return (
                      <button
                        key={option.id}
                        onClick={() => handleSelectModel(option)}
                        disabled={tryonStatus === "processing"}
                        className={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 bg-[#FAF8F5] transition ${
                          selected ? "border-[#8F1D2C] shadow-sm" : "border-[#EAEAEA] hover:border-[#D9C4A3]"
                        } ${tryonStatus === "processing" ? "opacity-40 cursor-not-allowed" : ""}`}
                      >

                        <img
                          src={option.image}
                          alt={option.label}
                          className="w-full h-full object-contain p-2"
                        />

                        {selected && (
                          <div className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-[#8F1D2C] text-white flex items-center justify-center">
                            <Check size={13} />
                          </div>
                        )}

                      </button>
                    );
                  }
                )}

              </div>

            </aside>

          </div>

          {/* =================================================
              SAVED LOOKS
          ================================================= */}

          <section className="mt-6 rounded-2xl border border-[#EAEAEA] bg-white p-5">

            <div className="flex items-center justify-between mb-4">

              <div>
                <h3 className="text-sm font-semibold text-ink">
                  My Saved Looks
                </h3>

                <p className="text-xs text-graytext mt-1">
                  Your personally created outfits
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-graytext">
                <Save size={14} />
                {savedLooks.length} saved
              </div>

            </div>

            {savedLooks.length === 0 ? (
              <div className="py-8 text-center text-xs text-graytext border border-dashed border-[#E5DED9] rounded-xl">
                Your saved personal looks will appear here.
              </div>
            ) : (
              <div className="flex gap-4 overflow-x-auto pb-2">

                {savedLooks.map((look) => (

                  <div
                    key={look.id}
                    className="flex-shrink-0 w-36 rounded-xl border border-[#EAEAEA] bg-[#FAF8F5] p-2"
                  >

                    {/* CLOTHING — static preview, just the saved pieces, no model shown here */}

                    <div className="w-full h-40 rounded-lg bg-white flex items-center justify-center p-3">
                      <div className="grid grid-cols-2 gap-1.5 w-full">
                        {[
                          look.top,
                          look.bottom,
                          look.jacket,
                          look.skirt,
                          look.dress,
                        ]
                          .filter(Boolean)
                          .slice(0, 4)
                          .map((item) => (
                            <img
                              key={item.id}
                              src={getItemImage(item)}
                              alt={item.category}
                              className="w-full aspect-square object-contain rounded border border-[#EAEAEA] bg-[#FAF8F5]"
                            />
                          ))}
                      </div>
                    </div>

                    {/* TRY ON — loads outfit + model AND generates immediately */}

                    <button
                      onClick={() =>
                        handleLoadLook(look)
                      }
                      className="mt-2 w-full py-1.5 rounded-lg bg-[#8F1D2C] text-white text-[11px] font-medium hover:bg-[#761623] transition flex items-center justify-center gap-1"
                    >
                      <User size={12} />
                      Try On
                    </button>

                    {/* EDIT — opens the modal to remove individual pieces */}

                    <button
                      onClick={() => setEditingLookId(look.id)}
                      className="mt-1.5 w-full py-1.5 rounded-lg border border-[#EAEAEA] text-[11px] text-ink hover:bg-[#F8F2EE] transition flex items-center justify-center gap-1"
                    >
                      <Pencil size={12} />
                      Edit
                    </button>

                    {/* DELETE */}

                    <button
                      onClick={() =>
                        handleDeleteLook(
                          look.id
                        )
                      }
                      className="mt-1.5 w-full py-1.5 rounded-lg text-[11px] text-graytext hover:text-red-500 hover:bg-white transition flex items-center justify-center gap-1"
                    >
                      <Trash2 size={12} />
                      Remove
                    </button>

                  </div>

                ))}

              </div>
            )}

          </section>

          {/* =================================================
              SAVED TRY-ON PHOTOS
          ================================================= */}

          <section className="mt-6 rounded-2xl border border-[#EAEAEA] bg-white p-5">

            <div className="flex items-center justify-between mb-4">

              <div>
                <h3 className="text-sm font-semibold text-ink">
                  My Saved Try-On Photos
                </h3>

                <p className="text-xs text-graytext mt-1">
                  Generated photos you've saved
                </p>
              </div>

              <div className="flex items-center gap-2 text-xs text-graytext">
                <Heart size={14} />
                {savedPhotos.length} saved
              </div>

            </div>

            {savedPhotos.length === 0 ? (
              <div className="py-8 text-center text-xs text-graytext border border-dashed border-[#E5DED9] rounded-xl">
                Generate a try-on and tap the heart to save it here.
              </div>
            ) : (
              <div className="flex gap-4 overflow-x-auto pb-2">

                {savedPhotos.map((photo) => (

                  <div
                    key={photo.id}
                    className="flex-shrink-0 w-36 rounded-xl border border-[#EAEAEA] bg-[#FAF8F5] p-2"
                  >

                    {/* NEW — clicking the thumbnail opens the full-size popup */}
                    <button
                      onClick={() => setViewingPhoto(photo)}
                      className="w-full h-48 rounded-lg bg-white overflow-hidden block"
                    >
                      <img
                        src={photo.url}
                        alt="Saved try-on"
                        className="w-full h-full object-cover hover:scale-105 transition-transform"
                      />
                    </button>

                    <button
                      onClick={() => handleDeleteSavedPhoto(photo.id)}
                      className="mt-2 w-full py-1.5 rounded-lg text-[11px] text-graytext hover:text-red-500 hover:bg-white transition flex items-center justify-center gap-1"
                    >
                      <Trash2 size={12} />
                      Remove
                    </button>

                  </div>

                ))}

              </div>
            )}

          </section>

        </div>
      </main>

      {/* =================================================
          EDIT SAVED LOOK MODAL
      ================================================= */}
      {/* NEW — full-size popup for a saved try-on photo */}
      {viewingPhoto && (
        <div
          className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
          onClick={() => setViewingPhoto(null)}
        >
          <div className="relative max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setViewingPhoto(null)}
              className="absolute -top-3 -right-3 w-9 h-9 rounded-full bg-white shadow-md flex items-center justify-center text-graytext hover:text-red-500 transition"
            >
              <X size={18} />
            </button>
            <img
              src={viewingPhoto.url}
              alt="Saved try-on"
              className="w-full max-h-[80vh] object-contain rounded-2xl shadow-2xl bg-white"
            />
          </div>
        </div>
      )}
      
      {editingLook && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
          onClick={() => setEditingLookId(null)}
        >
          <div
            className="bg-white rounded-2xl p-6 w-full max-w-sm"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-ink">Edit Saved Look</h3>
              <button
                onClick={() => setEditingLookId(null)}
                className="w-7 h-7 rounded-full hover:bg-[#F8F2EE] flex items-center justify-center text-graytext"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-5">
              {OUTFIT_SLOTS.filter(({ key }) => editingLook[key]).map(
                ({ key, label }) => {
                  const item = editingLook[key];
                  return (
                    <div
                      key={key}
                      className="relative rounded-xl border border-[#EAEAEA] bg-[#FAF8F5] p-9"
                    >
                      <button
                        onClick={() =>
                          handleRemovePieceFromLook(editingLook.id, key)
                        }
                        className="absolute top-1 right-1 w-5 h-5 rounded-full bg-white border border-[#EAEAEA] flex items-center justify-center text-graytext hover:text-red-500 hover:border-red-300 transition"
                        title={`Remove ${label}`}
                      >
                        <X size={11} />
                      </button>
                      <img
                        src={getItemImage(item)}
                        alt={item.category}
                        className="w-full aspect-square object-contain"
                      />
                      <p className="text-[10px] text-graytext text-center mt-1">
                        {label}
                      </p>
                    </div>
                  );
                }
              )}
            </div>

            {OUTFIT_SLOTS.every(({ key }) => !editingLook[key]) && (
              <p className="text-xs text-graytext text-center mb-4">
                No pieces left in this look.
              </p>
            )}

            <button
              onClick={() => setEditingLookId(null)}
              className="w-full py-2.5 rounded-xl bg-[#8F1D2C] text-white text-sm font-medium hover:bg-[#761623] transition"
            >
              Done
            </button>
          </div>
        </div>
      )}

      <FooterMini />
    </div>
  );
}