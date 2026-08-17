import { useState, useEffect } from "react";
import {
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

import {
  startTryOn,
  getTryOnStatus,
  getWardrobe,
} from "../lib/api";

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

export default function Avatar({ user, onLogout }) {
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

  async function runGenerate(photoFileArg, topId, bottomId) {
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

    try {
      const started = await startTryOn({
        photoFile: photoFileArg,
        topId,
        bottomId,
      });
      pollUntilDone(started.id);
    } catch (e) {
      setError(e.message);
      setTryonStatus("failed");
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
    await runGenerate(photoFile, topId, bottomId);
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
    await runGenerate(file, topId, bottomId);
  }

  /* =======================================================
     POLL TRY ON STATUS
  ======================================================= */

  function pollUntilDone(tryonId) {
    const interval =
      setInterval(async () => {
        try {
          const data =
            await getTryOnStatus(
              tryonId
            );

          if (data.status === "done") {
            clearInterval(interval);

            setTryonStatus("done");

            setResultUrl(
              data.resultImageUrl
            );
          } else if (
            data.status === "failed"
          ) {
            clearInterval(interval);

            setTryonStatus("failed");

            setError(
              data.error_message ||
                "Generation failed — try again."
            );
          }
        } catch {
          clearInterval(interval);

          setTryonStatus("failed");

          setError(
            "Lost connection while checking try-on status."
          );
        }
      }, 4000);
  }

  /* =======================================================
     RESET RESULT
  ======================================================= */

  function resetResult() {
    setResultUrl(null);
    setTryonStatus(null);
    setError(null);
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

          <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(430px,0.95fr)_125px] gap-5">

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

            <section className="rounded-2xl border border-[#EAEAEA] bg-gradient-to-b from-[#F8E9DF] to-[#F5E7EA] min-h-[700px] relative overflow-hidden">

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
                    className="mt-5 text-sm text-graytext underline"
                  >
                    Try a different combination
                  </button>

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

                  <div className="h-full min-h-[700px] flex items-center justify-center p-8">

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

                  <div className="absolute bottom-5 left-5 flex gap-2">

                    <button
                      onClick={handleReset}
                      className="w-11 h-11 rounded-xl bg-white/90 backdrop-blur flex items-center justify-center hover:bg-white transition"
                      title="Reset — clears outfit and model"
                    >
                      <RotateCcw size={18} />
                    </button>

                  </div>

                  {/* DISCLAIMER — centered across the preview box,
                      at the same vertical level as the Generate
                      Try-On button (its own sibling, not nested in
                      the right-side column, so left-1/2 centers it
                      relative to the whole section instead of the
                      narrow bottom-right stack). */}

                  {photoFile && (
                    <p className="absolute bottom-8 left-1/2 -translate-x-1/2 z-10 max-w-[260px] text-center text-[10px] leading-snug text-graytext/80 bg-white/70 backdrop-blur rounded-lg px-2.5 py-1.5">
                      Results are AI-generated and may vary slightly from how the item actually looks in wardrobe.
                    </p>
                  )}

                  {/* OUTFIT PREVIEW + GENERATE — stacked in the
                      bottom-right, so the user can see exactly what
                      they've picked right next to the action button. */}

                  <div className="absolute bottom-5 right-5 flex flex-col items-end gap-2">

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

            </section>

            {/* =================================================
                RIGHT — MODEL SELECTOR
            ================================================= */}

            <aside className="rounded-2xl border border-[#EAEAEA] bg-white p-3">

              <h3 className="text-xs font-semibold text-ink text-center mb-3">
                Choose Model
              </h3>

              <div className="flex lg:flex-col gap-3">

                {MODEL_OPTIONS.map(
                  (option) => {

                    const selected =
                      selectedModelId ===
                      option.id;

                    return (
                      <button
                        key={option.id}
                        onClick={() =>
                          handleSelectModel(
                            option
                          )
                        }
                        className={`relative w-full aspect-[3/4] rounded-xl overflow-hidden border-2 bg-[#FAF8F5] transition ${
                          selected
                            ? "border-[#8F1D2C] shadow-sm"
                            : "border-[#EAEAEA] hover:border-[#D9C4A3]"
                        }`}
                      >

                        <img
                          src={option.image}
                          alt={option.label}
                          className="w-full h-full object-cover object-top"
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

                    <div className="w-full h-48 rounded-lg bg-white overflow-hidden">
                      <img
                        src={photo.url}
                        alt="Saved try-on"
                        className="w-full h-full object-cover"
                      />
                    </div>

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
                      className="relative rounded-xl border border-[#EAEAEA] bg-[#FAF8F5] p-2"
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