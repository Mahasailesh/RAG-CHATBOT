import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0b1220",
          900: "#111827",
          800: "#1f2937"
        },
        steel: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5f5",
          400: "#94a3b8",
          500: "#64748b",
          600: "#475569",
          700: "#334155"
        },
        trust: {
          500: "#1d4ed8",
          600: "#1e40af",
          700: "#1e3a8a"
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"]
      },
      boxShadow: {
        soft: "0 18px 45px -30px rgba(15, 23, 42, 0.45)"
      },
      borderRadius: {
        lg: "0.9rem",
        md: "0.65rem",
        sm: "0.45rem"
      }
    }
  },
  plugins: []
};

export default config;
