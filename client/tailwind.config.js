
// tailwind.config.js
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx,css}',
    './src/.index.css'
  ],
  theme: {
    extend: {
      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
        },
      },
      fontFamily: {
        sans: ['Helvetica', 'Arial', 'sans-serif'],
      },
      colors: {
        industrial: {
          bg: '#181A1B', // dark background
          surface: '#23272A', // card/panel
          border: '#2C3136',
          accent: '#2563EB', // blue accent
          accent2: '#FBBF24', // yellow highlight
          text: '#F3F4F6', // light text
          muted: '#9CA3AF', // muted text
        },
      },
    },
  },
  plugins: [],
}
