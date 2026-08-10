// Reusable styled text input. Automatically adds a show/hide eye icon
// when type="password" is passed in, so Login/Signup don't each need
// their own password-toggle logic.
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function Input({ label, type = "text", value, onChange, placeholder, ...props }) {
  const [showPassword, setShowPassword] = useState(false);
  const isPassword = type === "password";
  // Swap the actual input type between "password" and "text" when toggled
  const inputType = isPassword && showPassword ? "text" : type;

  return (
    <div className="mb-4">
      {label && <label className="block text-sm text-graytext mb-1.5">{label}</label>}
      <div className="relative">
        <input
          type={inputType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="w-full rounded-lg border border-[#EAEAEA] px-4 py-2.5 text-sm text-ink bg-white outline-none focus:border-tan transition-colors pr-10"
          {...props}
        />
        {/* Eye icon only shows up for password fields */}
        {isPassword && (
          <button type="button" onClick={() => setShowPassword((s) => !s)} className="absolute right-3 top-1/2 -translate-y-1/2 text-graytext" tabIndex={-1}>
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
}