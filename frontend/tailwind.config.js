/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          DEFAULT: '#0B0C10',
          50: '#1A1C23',
          100: '#161820',
          200: '#12141A',
          300: '#0E1015',
          400: '#0B0C10',
        },
        surface: {
          DEFAULT: 'rgba(18, 20, 29, 0.72)',
          elevated: '#161922',
          hover: '#1E2330',
          border: 'rgba(255, 255, 255, 0.08)',
          'border-active': 'rgba(157, 140, 255, 0.35)',
        },
        lavender: {
          DEFAULT: '#9D8CFF',
          glow: 'rgba(157, 140, 255, 0.15)',
          light: '#BDB2FF',
          dark: '#6C5CE7',
        },
        nexus: {
          text: '#F0F1F7',
          muted: '#8E93A6',
          dim: '#55596D',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'lavender-glow': '0 0 20px -3px rgba(157, 140, 255, 0.25)',
      }
    },
  },
  plugins: [],
}
