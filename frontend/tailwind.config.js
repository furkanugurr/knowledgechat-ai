/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        mist: "#f4f7fb",
        ocean: {
          50: "#eef9ff",
          100: "#d9f1ff",
          500: "#1687b8",
          600: "#0e6f9a",
          700: "#105a7a"
        }
      },
      boxShadow: {
        panel: "0 24px 70px -32px rgba(23, 32, 51, 0.35)"
      }
    }
  },
  plugins: []
};
