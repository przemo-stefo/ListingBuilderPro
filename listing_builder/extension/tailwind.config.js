// extension/tailwind.config.js
// Purpose: Tailwind config for Chrome Extension popup UI
// NOT for: Frontend or backend styling

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{ts,tsx}", "./public/popup.html"],
  theme: {
    extend: {
      colors: {
        dark: {
          primary: "#1A1A1A",
          secondary: "#121212",
          border: "#333333",
          "border-light": "#2C2C2C",
        },
      },
      width: {
        popup: "400px",
      },
      height: {
        popup: "600px",
      },
    },
  },
  plugins: [],
};
