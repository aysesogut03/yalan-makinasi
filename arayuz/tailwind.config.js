/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#131B31",
          cardNav: "#1C2640",
          orange: "#EE6C4D",
          cream: "#F8F7F2",
          yellow: "#FEEA2B"
        },
        signal: {
          hr: "#FB7C45",
          gsr: "#4F8CFF",
          resp: "#2DD4A7"
        }
      },
      boxShadow: {
        card: "0 1px 2px rgba(19,27,49,0.04), 0 8px 24px -12px rgba(19,27,49,0.12)",
        glow: "0 10px 40px -10px rgba(238,108,77,0.45)"
      },
      keyframes: {
        fadeUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        }
      },
      animation: {
        fadeUp: "fadeUp 0.5s ease-out both"
      }
    },
  },
  plugins: [],
}