// Reusable button with two styles: "primary" (solid dark) and "secondary"
// (outlined). Used across Login/Signup so every button looks consistent.
export default function Button({ children, variant = "primary", ...props }) {
  const base = "w-full rounded-lg py-2.5 text-sm font-medium transition-colors";
  const variants = {
    primary: "bg-ink text-white hover:bg-black",
    secondary: "border border-[#EAEAEA] text-ink hover:bg-[#FAF8F5]",
  };
  // ...props spreads onClick, type, disabled, etc. through to the real <button>
  return <button className={`${base} ${variants[variant]}`} {...props}>{children}</button>;
}