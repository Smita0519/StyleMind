// Full-screen login page. Left panel is decorative (photo + branding,
// hidden on mobile); right panel has the actual form.
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Input from "../components/Input";
import Button from "../components/Button";
import FooterMini from "../components/FooterMini";
import { login } from "../lib/api";
import loginBg from "../assets/login-bg1.png";
import logo from "../assets/logo.png";
import { Sparkles } from "lucide-react";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { user, token } = await login(email, password);
      onLogin(user, token);
      navigate("/home");
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen w-full">

      {/* Left panel — decorative photo + branding, hidden on mobile */}
      <div
        className="hidden md:flex relative flex-col justify-between w-1/2 p-12 text-white overflow-hidden"
        style={{
          backgroundImage: `linear-gradient(160deg, rgba(43,36,28,0.75) 0%, rgba(107,92,71,0.65) 100%), url(${loginBg})`,
          backgroundSize: "cover",
          backgroundPosition: "left center",
        }}
      >
        <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full opacity-20" style={{ background: "radial-gradient(circle, #D4B996, transparent 70%)" }} />
        <div className="absolute bottom-10 -left-10 w-64 h-64 rounded-full opacity-10" style={{ background: "radial-gradient(circle, #FAF8F5, transparent 70%)" }} />

        <div className="relative z-10 flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-white shadow-sm flex items-center justify-center">
            <Sparkles className="text-[#C46A8A]" size={16} />
          </div>
          <span className="text-sm tracking-widest uppercase opacity-80">StyleMind</span>
        </div>

        <div className="relative z-10">
          <h1 className="text-4xl lg:text-5xl leading-tight mb-3" style={{ fontFamily: "'Playfair Display', serif" }}>
            Your Personal<br />AI Stylist
          </h1>
          <p className="text-sm opacity-70 max-w-xs">Discover outfits tailored to your wardrobe, your weather, and your taste.</p>
        </div>

        <p className="relative z-10 text-xs opacity-60 tracking-wide">ELEVATE YOUR STYLE. EVERY DAY.</p>
      </div>

      {/* Right panel — shiny gradient, no card, no tagline, no social
          login. Gradient back to the liked palette but with the near-white
          end stops warmed up so the top isn't washed out. Sparkle dots
          flicker gently — the only motion on this page. */}
      <div
        className="relative flex flex-1 flex-col items-center justify-center px-6 sm:px-8 py-10 overflow-hidden"
        style={{
          background: "linear-gradient(120deg, #F0DCC8 0%, #F7E6D9 22%, #F3D9E8 45%, #f0dbbf 68%, #F7E6D9 86%, #F0DCC8 100%)",
        }}
      >
        <style>{`
          @keyframes sm-dot-flicker {
            0%, 100% { opacity: 0.25; transform: scale(0.85); }
            50%      { opacity: 1;    transform: scale(1.15); }
          }
        `}</style>

        <div
          className="absolute -top-24 -right-10 w-[22rem] h-[22rem] rounded-full opacity-[0.08] blur-2xl pointer-events-none"
          style={{ background: "radial-gradient(circle, #D4B996, transparent 70%)" }}
        />
        <div
          className="absolute -bottom-24 -left-16 w-[22rem] h-[22rem] rounded-full opacity-20 blur-2xl pointer-events-none"
          style={{ background: "radial-gradient(circle, #C46A8A, transparent 70%)" }}
        />

        {[
          { top: "14%", left: "18%", size: 6, delay: "0s" },
          { top: "24%", left: "82%", size: 4, delay: "0.6s" },
          { top: "68%", left: "12%", size: 5, delay: "1.2s" },
          { top: "78%", left: "88%", size: 4, delay: "1.8s" },
          { top: "8%", left: "55%", size: 4, delay: "2.4s" },
        ].map((dot, i) => (
          <div
            key={i}
            className="absolute rounded-full pointer-events-none"
            style={{
              top: dot.top, left: dot.left, width: dot.size, height: dot.size,
              background: "#FFFFFF",
              boxShadow: "0 0 8px 2px rgba(212,185,150,0.8)",
              animation: "sm-dot-flicker 2.6s ease-in-out infinite",
              animationDelay: dot.delay,
            }}
          />
        ))}

        <form onSubmit={handleSubmit} className="relative z-10 w-full max-w-sm">
          <div className="flex flex-col items-center text-center mb-4">
            <img src={logo} alt="StyleMind logo" className="w-70 h-60 object-contain mb-1 drop-shadow-sm" />
          </div>

          <h2 className="text-xl font-semibold text-ink mb-1 text-center">Welcome back!</h2>
          <p className="text-sm text-graytext mb-4 text-center">Sign in to continue your style journey</p>

          <Input label="Email address" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="youremail@mail.com" />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />

          {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

          <Button type="submit" disabled={loading}>{loading ? "Signing in..." : "Sign In"}</Button>

          <p className="text-sm text-graytext py-4 text-center mt-2">
            Don't have an account? <Link to="/signup" className="text-ink font-medium">Create one</Link>
          </p>
        </form>
      </div>
    </div>
  );
}