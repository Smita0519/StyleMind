// pages/Home.jsx
import { Link } from "react-router-dom";
import { useRef, useState, useEffect } from "react"; // useEffect ADDED — confirms arrow visibility against the real DOM on mount
import { Upload, Shirt, User, MessageCircle, ChevronLeft, ChevronRight } from "lucide-react";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

import homeImg from "../assets/home1.png";
import casualImg from "../assets/Casual.png";
import picnicImg from "../assets/Picnic.png";
import formalImg from "../assets/Formal.png";
import travelImg from "../assets/Travel.png";

import Trending1 from "../assets/Trending1.png";
import Trending2 from "../assets/Trending2.png";
import Trending3 from "../assets/Trending3.png";
import Trending4 from "../assets/Trending4.png";
import Trending5 from "../assets/Trending5.png";
import Trending6 from "../assets/Trending6.png";
import Trending7 from "../assets/Trending7.png";
import Trending8 from "../assets/Trending8.png";
import Trending9 from "../assets/Trending9.png";
import Trending10 from "../assets/Trending10.png";
import Trending11 from "../assets/Trending11.png";

const occasions = [
  { name: "Casual", sub: "Everyday", image: casualImg, bg: "#f2d7d3" },
  { name: "Picnic", sub: "Outdoor", image: picnicImg, bg: "#f2d7d3" },
  { name: "Formal", sub: "Workwear", image: formalImg, bg: "#f2d7d3" },
  { name: "Travel", sub: "Getaway", image: travelImg, bg: "#f2d7d3" },
];

// Matched precisely to your screenshot
const trending = [
  { id: 1,  name: "Casual Chic",                image: Trending1,  bg: "#f2d7d3" },
  { id: 2,  name: "White Mini Dress",           image: Trending2,  bg: "#f2d7d3" },
  { id: 3,  name: "Red Power Suit",             image: Trending3,  bg: "#f2d7d3" },
  { id: 4,  name: "Grey Business Suit",         image: Trending4,  bg: "#f2d7d3" },
  { id: 5,  name: "Blue Shirt Dress",           image: Trending5,  bg: "#f2d7d3" },
  { id: 6,  name: "Navy Long Coat Set",         image: Trending6,  bg: "#f2d7d3" },
  { id: 7,  name: "Bridal Gown",                image: Trending7,  bg: "#f2d7d3" },
  { id: 8,  name: "Black Pantsuit",             image: Trending8,  bg: "#f2d7d3" },
  { id: 9,  name: "Off-Shoulder Evening Dress", image: Trending9,  bg: "#f2d7d3" },
  { id: 10, name: "Ruffle Couture Dress",       image: Trending10, bg: "#f2d7d3" },
  { id: 11, name: "Monochrome Elegance",       image: Trending11, bg: "#f2d7d3" },
  
];

const quickActions = [
  { icon: Upload, label: "Upload Clothes", sub: "Add to wardrobe", to: "/wardrobe" },
  { icon: Shirt, label: "Create Outfit", sub: "Mix & match", to: "/recommendations" },
  { icon: User, label: "Virtual Try-On", sub: "See it on model", to: "/tryon" },
  { icon: MessageCircle, label: "Chat with Stylist", sub: "Get AI advice", to: "/chat" },
];

export default function Home({ user, onLogout }) {
  // Controls the horizontal Trending Looks slider
  const trendingRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  // Scrolls the row by roughly one "page" worth of cards at a time
  function scrollTrending(direction) {
    const el = trendingRef.current;
    if (!el) return;
    const amount = el.clientWidth * 0.8;
    el.scrollBy({ left: direction === "right" ? amount : -amount, behavior: "smooth" });
  }

  // Keeps the arrow buttons' visibility in sync with actual scroll position
  // (e.g. hides the left arrow when already at the start)
  function handleTrendingScroll() {
    const el = trendingRef.current;
    if (!el) return;
    // Slightly larger threshold (8px, up from 4px) to absorb sub-pixel
    // rounding differences some browsers introduce during layout/scroll
    setCanScrollLeft(el.scrollLeft > 8);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 8);
  }

  // ===================== CHANGE START =====================
  // CHANGED — a single one-time check on mount wasn't enough: the row's
  // width can shift as its 10 images finish loading in, which can nudge
  // scrollLeft in some browsers even without any manual scrolling,
  // leaving the arrow visibility stale/wrong. A ResizeObserver instead
  // re-measures every time the row's actual size/content changes (e.g.
  // each image loading in), keeping canScrollLeft/canScrollRight accurate
  // throughout, not just at the first render.
  useEffect(() => {
    const el = trendingRef.current;
    if (!el) return;

    handleTrendingScroll(); // initial check right away

    const resizeObserver = new ResizeObserver(() => handleTrendingScroll());
    resizeObserver.observe(el);

    return () => resizeObserver.disconnect(); // cleanup on unmount
  }, []);
  // ===================== CHANGE END =====================

  return (
    <div className="min-h-screen bg-[#F8F1EB]">
      <Navbar user={user} onLogout={onLogout} />

      {/* Hero Section */}
      <div
        className="relative overflow-hidden mb-6 p-6 sm:p-10 lg:p-12 h-[350px] lg:h-[500px] flex flex-col justify-center"
        style={{ background: "linear-gradient(135deg, #FAF8F5, #F0ECE4)" }}
      >
        <img
          src={homeImg}
          alt="Fashion inspiration"
          className="absolute inset-0 w-full h-full object-cover object-[65%_10%] md:object-[80%_10%]"
        />
        <div className="relative z-10 max-w-3xl lg:p-8">
          <p className="text-sm md:text-xl lg:text-2xl text-graytext mb-2">
            Hello, {user?.name || "there"} ❤️
          </p>
          <h1 className="text-2xl sm:text-5xl md:text-6xl lg:text-7xl leading-tight tracking-wide mb-6" style={{ fontFamily: "'Playfair Display', serif" }}>
            Let's find your<br /><span className="text-[#ac1c1c] italic">perfect</span> look today
          </h1>
          <p className="text-sm sm:text-base text-[#3A3A3A] leading-7 mb-6 tracking-wide">
            AI-powered styling recommendations <br />tailored just for you.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link to="/recommendations" className="inline-block bg-ink text-white font-medium px-6 py-3 rounded-lg hover:opacity-90 transition">
              Get Recommendations
            </Link>
            <Link to="/wardrobe" className="inline-block border border-ink text-ink font-medium px-6 py-3 rounded-lg bg-white/70 hover:bg-white hover:-translate-y-0.5 hover:shadow-md transition-all duration-200">
              Explore Wardrobe
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content Container - Minimal horizontal padding */}
      <div className="w-full px-5 sm:px-12 lg:px-20 py-5 mx-auto">

        {/* Occasions Section */}
        <h2 className="text-xl sm:text-2xl md:text-3xl font-semibold font-[Poppins] text-ink mb-4 px-2">
          What are you styling for?
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 mb-10">
          {occasions.map((o) => (
            <div key={o.name} className="cursor-pointer group">
              <div
                className="relative rounded-2xl overflow-hidden flex items-end justify-center border border-black/5 shadow-sm group-hover:shadow-lg transition-all duration-300 group-hover:-translate-y-1 aspect-square"
                style={{ backgroundColor: o.bg }}
              >
                <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-40 pointer-events-none" style={{ background: `radial-gradient(circle, white, transparent 70%)` }} />
                <img src={o.image} alt={o.name} className="relative z-10 h-[95%] w-auto object-contain object-bottom p-2" />
              </div>
              <div className="mt-2 text-center">
                <h3 className="text-sm font-semibold text-ink">{o.name}</h3>
                <p className="text-xs text-graytext">{o.sub}</p>
              </div>
            </div>
          ))}
        </div>

        {/* ===================== CHANGE START ===================== */}
        {/* Trending Section — horizontal snap-scroll slider. "View all"
            link REMOVED — plain heading again, arrow buttons handle
            navigation. Left arrow is only shown once actually scrolled
            right (see canScrollLeft / handleTrendingScroll above). */}
        <h2 className="text-xl sm:text-2xl md:text-3xl font-semibold font-[Poppins] text-ink mb-4 px-2">
          Trending Looks
        </h2>

        <div className="relative mb-10">
          {/* Scrollable row — snap-x makes each card settle into place when
              scrolling/dragging; scrollbar hidden via inline style + the
              .trending-scroll class below */}
          <div
            ref={trendingRef}
            onScroll={handleTrendingScroll}
            className="trending-scroll flex gap-5 overflow-x-auto scroll-smooth snap-x snap-mandatory pt-4 pb-2 px-2 -mx-2"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
          >
            {trending.map((t) => (
              <div key={t.id} className="cursor-pointer group flex-shrink-0 snap-start w-[42%] sm:w-[28%] lg:w-[19%]">
                <div
                  className="relative rounded-2xl overflow-hidden flex items-end justify-center border border-black/5 shadow-sm group-hover:shadow-lg transition-all duration-300 group-hover:-translate-y-1 aspect-square"
                  style={{ backgroundColor: t.bg }}
                >
                  <div className="absolute -top-10 -right-10 w-32 h-32 rounded-full opacity-40 pointer-events-none" style={{ background: `radial-gradient(circle, white, transparent 70%)` }} />
                  <img src={t.image} alt={t.name} className="relative z-10 h-[95%] w-auto object-contain object-bottom p-2" />
                </div>
              </div>
            ))}
          </div>

          {/* Hides the scrollbar in WebKit browsers (Chrome/Safari); the
              inline scrollbarWidth/msOverflowStyle above covers Firefox/IE */}
          <style>{`.trending-scroll::-webkit-scrollbar { display: none; }`}</style>

          {/* Left arrow — only visible once scrolled away from the start */}
          {canScrollLeft && (
            <button
              onClick={() => scrollTrending("left")}
              aria-label="Scroll left"
              className="absolute left-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-ink text-white shadow-lg flex items-center justify-center hover:scale-105 transition-transform z-10"
            >
              <ChevronLeft size={18} />
            </button>
          )}

          {/* Right arrow — hides once scrolled all the way to the end */}
          {canScrollRight && (
            <button
              onClick={() => scrollTrending("right")}
              aria-label="Scroll right"
              className="absolute right-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-ink text-white shadow-lg flex items-center justify-center hover:scale-105 transition-transform z-10"
            >
              <ChevronRight size={18} />
            </button>
          )}
        </div>
        {/* ===================== CHANGE END ===================== */}

        {/* Quick Actions Section */}
        <div className="rounded-2xl p-4 sm:p-6 mb-8" style={{ background: "linear-gradient(135deg, #111827, #2b241c)" }}>
          <h2 className="text-white text-sm font-medium mb-4">Quick Actions</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {quickActions.map((a) => (
              <Link key={a.label} to={a.to} className="flex flex-col items-center text-center bg-white/10 hover:bg-white/15 transition-colors rounded-xl p-4">
                <a.icon size={20} className="text-tan mb-2" />
                <span className="text-white text-sm font-medium">{a.label}</span>
                <span className="text-white/60 text-xs">{a.sub}</span>
              </Link>
            ))}
          </div>
        </div>

      </div>

      <Footer />
    </div>
  );
}