/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        dashboard: "#0a0f1e",
        card: "#0f172a",
        accent: "#06b6d4",
      },
      fontFamily: {
        inter: ["Inter", "sans-serif"],
      },
      boxShadow: {
        redGlow: "0 0 12px rgba(239, 68, 68, 0.4)",
        amberGlow: "0 0 12px rgba(245, 158, 11, 0.4)",
        cyanGlow: "0 0 12px rgba(6, 182, 212, 0.4)",
      },
    },
  },
  plugins: [],
};
