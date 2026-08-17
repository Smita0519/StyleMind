// Top nav bar shown on every logged-in page. Handles page links, active-page
// highlighting, mobile hamburger menu, and the profile dropdown/logout.
import { useState, useRef, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, LogOut, User as UserIcon } from "lucide-react";
import logo from "../assets/StylemindLogo.png";
import ProfileModal from "./ProfileModal";
import ImageLightbox from "./ImageLightbox";

const links = [
  { to: "/home", label: "Home" },
  { to: "/wardrobe", label: "Wardrobe" },
  { to: "/outfits", label: "Outfits" },
  { to: "/avatar", label: "Tryon" },,
  { to: "/recommendations", label: "Recommendations" },
  { to: "/chat", label: "Chatbot" },
];

// The avatar + dropdown showing the logged-in user's name/email + logout.
// CHANGED — now takes `displayUser` (the freshest name/picture, which may
// be newer than the `user` prop right after a profile edit) and
// `onOpenProfile` to launch the ProfileModal instead of the old
// alert("Profile settings not implemented yet").
function ProfileMenu({ displayUser, onLogout, onOpenProfile }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const navigate = useNavigate();
  const [showLightbox, setShowLightbox] = useState(false);

  // Closes the dropdown if you click anywhere outside of it
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleLogout() {
    setOpen(false);
    onLogout();          // clears session in App.jsx
    navigate("/login");  // sends user back to login screen
  }

  const initial = displayUser?.name?.[0]?.toUpperCase() || "?";

  return (
    <div className="relative" ref={menuRef}>
      <button onClick={() => setOpen((o) => !o)} className="w-8 h-8 rounded-full bg-tan flex items-center justify-center text-white text-xs font-semibold cursor-pointer overflow-hidden">
        {/* Shows the real profile picture when one exists, falls back to the initial otherwise */}
        {displayUser?.pictureUrl ? (
          <img src={displayUser.pictureUrl} alt="Profile" className="w-full h-full object-cover" />
        ) : (
          initial
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-11 w-64 bg-white border border-[#EAEAEA] rounded-xl shadow-lg z-50 overflow-hidden">
          {/* Name + email card */}
          <div className="flex items-center gap-3 p-4 border-b border-[#EAEAEA]">
            {/* CHANGED — clickable, opens a full-size view when a real photo exists */}
            <div
              className={`w-10 h-10 rounded-full bg-tan flex items-center justify-center text-white text-sm font-semibold flex-shrink-0 overflow-hidden ${displayUser?.pictureUrl ? "cursor-pointer" : ""}`}
              onClick={() => displayUser?.pictureUrl && setShowLightbox(true)}
            >
              {displayUser?.pictureUrl ? (
                <img src={displayUser.pictureUrl} alt="Profile" className="w-full h-full object-cover" />
              ) : (
                initial
              )}
            </div>
            <div className="min-w-0">
              <div className="text-sm font-medium text-ink truncate">{displayUser?.name || "Guest"}</div>
              <div className="text-xs text-graytext truncate">{displayUser?.email}</div>
            </div>
          </div>

          <div className="py-1">
            <button onClick={() => { setOpen(false); onOpenProfile(); }} className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-ink hover:bg-[#FAF8F5] text-left">
              <UserIcon size={15} /> View Profile
            </button>
            <button onClick={handleLogout} className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 text-left">
              <LogOut size={15} /> Log Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Navbar({ user, onLogout }) {
  const location = useLocation(); // tells us which page we're currently on, for active-link styling
  const [open, setOpen] = useState(false); // controls the mobile hamburger dropdown

  // NEW — controls whether the ProfileModal is open, and holds the
  // freshest user info. Starts as the `user` prop, but gets overwritten
  // locally right after a successful profile save so the avatar/name
  // update instantly without waiting for App.jsx's state or a page
  // refresh. (Home.jsx's greeting will pick up the new name on its own
  // next re-render from App.jsx, e.g. after navigating or refreshing.)
  const [profileOpen, setProfileOpen] = useState(false);
  const [displayUser, setDisplayUser] = useState(user);

  // Keeps displayUser in sync if the `user` prop itself changes (e.g. on logout/login)
  useEffect(() => {
    setDisplayUser(user);
  }, [user]);

  return (
    // sticky top-0 keeps this bar pinned while the page scrolls beneath it
    <div className="sticky top-0 border-b border-[#8A0303] bg-[#f9f2f1] z-30">
      <div className="flex items-center justify-between px-4 sm:px-8 py-4">

        {/* Logo — clicking it always goes back to Home */}
        <Link to="/home" className="flex items-center ">
          <img src={logo} alt="StyleMind" className="w-[120px] h-[45px] object-contain block" />
        </Link>

        {/* Desktop nav links — hidden below md breakpoint */}
        <div className="hidden md:flex gap-6">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-sm pb-1 border-b-2 transition-colors ${
                location.pathname === l.to
                  ? "text-[#7E4E55] font-semibold border-tan" // active page: colored text + underline
                  : "text-graytext border-transparent hover:text-ink"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* CHANGED — Search and Notifications buttons removed (were just
            "not implemented yet" placeholders). ProfileMenu is the only
            thing left on the right side now. */}
        <div className="hidden md:flex items-center gap-4">
          <ProfileMenu displayUser={displayUser} onLogout={onLogout} onOpenProfile={() => setProfileOpen(true)} />
        </div>

        {/* Hamburger — only shown below md breakpoint */}
        <button className="md:hidden text-ink" onClick={() => setOpen((o) => !o)}>
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile dropdown menu — same active-link styling, using a left border instead of underline */}
      {open && (
        <div className="md:hidden flex flex-col border-t border-[#EAEAEA] bg-white px-4 py-2">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className={`py-3 text-sm border-l-2 pl-3 ${
                location.pathname === l.to
                  ? "text-[#7E4E55] font-semibold border-tan"
                  : "text-graytext border-transparent"
              }`}
            >
              {l.label}
            </Link>
          ))}
          {/* CHANGED — Search/Notifications icons removed here too, ProfileMenu now sits alone */}
          <div className="flex items-center justify-end py-3 border-t border-[#EAEAEA] mt-1">
            <ProfileMenu displayUser={displayUser} onLogout={onLogout} onOpenProfile={() => setProfileOpen(true)} />
          </div>
        </div>
      )}

      {/* NEW — the profile modal itself, only mounted while open.
          onSave updates displayUser immediately AND writes through to
          localStorage, so a refresh (or navigating to another page,
          e.g. Home's greeting) picks up the new name/picture too. */}
      {profileOpen && (
        <ProfileModal
          user={displayUser}
          onClose={() => setProfileOpen(false)}
          onSave={(updated) => {
            setDisplayUser(updated);
            try {
              const stored = JSON.parse(localStorage.getItem("stylemind_current_user") || "{}");
              localStorage.setItem("stylemind_current_user", JSON.stringify({ ...stored, ...updated }));
            } catch {
              // if localStorage is somehow unavailable, the in-memory update above still applies
            }
          }}
        />
      )}
    </div>
  );
}