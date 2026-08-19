// Root component: sets up all page routes, holds the logged-in user state,
// and decides which pages require login.
import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Home from "./pages/Home";
import Wardrobe from "./pages/Wardrobe";
import Chatbot from "./pages/Chatbot";
import FloatingChatbot from "./components/FloatingChatbot";
import Recommendations from "./pages/Recommendations";
import TryOn from "./pages/TryOn";
import Outfits from "./pages/Outfits";
import ScrollToTopButton from "./components/ScrollToTopButton";

// Wraps any page that requires the user to be logged in.
// If nobody's logged in, redirect straight to /login.
// showFloatingChat=false lets the dedicated /chat page hide the floating
// widget (no point showing both at once).
function ProtectedLayout({ user, children, showFloatingChat = true }) {
  if (!user) return <Navigate to="/login" />;
  return (
    <>
      {children}
      {showFloatingChat && <FloatingChatbot />}
      {/* Shows up on every logged-in page automatically, since every
          protected route is wrapped by this component */}
      <ScrollToTopButton />
    </>
  );
}

function App() {
  // On first load, check localStorage for a saved session so refreshing
  // the page doesn't log the user out.
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("stylemind_current_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  // Called after successful login/signup — saves the user both in React
  // state (for this session) and localStorage (so it survives a refresh).
function handleLogin(userData, token) {
  setUser(userData);
  localStorage.setItem("stylemind_current_user", JSON.stringify(userData));
  localStorage.setItem("stylemind_access_token", token);
}

function handleLogout() {
  setUser(null);
  localStorage.removeItem("stylemind_current_user");
  localStorage.removeItem("stylemind_access_token");
}

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes — no login required */}
        <Route path="/login" element={<Login onLogin={handleLogin} />} />
        <Route path="/signup" element={<Signup onLogin={handleLogin} />} />
        
        {/* Protected routes — redirect to /login if not signed in */}
        <Route path="/home" element={<ProtectedLayout user={user}><Home user={user} onLogout={handleLogout} /></ProtectedLayout>} />
        <Route path="/wardrobe" element={<ProtectedLayout user={user}><Wardrobe user={user} onLogout={handleLogout} /></ProtectedLayout>} />
        <Route path="/chat" element={<ProtectedLayout user={user} showFloatingChat={false}><Chatbot user={user} onLogout={handleLogout} /></ProtectedLayout>} />
        <Route path="/outfits" element={<ProtectedLayout user={user}><Outfits user={user} onLogout={handleLogout} /></ProtectedLayout>} />
        <Route path="/tryon" element={<ProtectedLayout user={user}><TryOn user={user} onLogout={handleLogout} /></ProtectedLayout>} />
        <Route path="/recommendations" element={<ProtectedLayout user={user}><Recommendations user={user} onLogout={handleLogout} /></ProtectedLayout>} />

        {/* Any unknown URL → send to login */}
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;