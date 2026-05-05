/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0B0E14',
          50: '#1A2030',
          100: '#161B26',
          200: '#11151E',
          300: '#0E1219',
          400: '#0B0E14',
          500: '#080A0F',
        },
        line: '#1F2632',
        line2: '#2A3242',
        bone: '#E5E7EB',
        muted: '#8B95A7',
        dim: '#5A6377',
        signal: {
          DEFAULT: '#D4F542',
          dim: '#8AA320',
          glow: '#E4FF6A',
        },
        plus: '#4ADE80',
        minus: '#F87171',
        warn: '#FACC15',
        info: '#60A5FA',
      },
      fontFamily: {
        display: ['Fraunces', 'ui-serif', 'Georgia', 'serif'],
        sans: ['"Hanken Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.6875rem', { lineHeight: '1rem', letterSpacing: '0.06em' }],
      },
      letterSpacing: {
        widest2: '0.18em',
      },
      boxShadow: {
        ring: '0 0 0 1px rgba(212, 245, 66, 0.4)',
        'ring-soft': '0 0 0 1px rgba(229, 231, 235, 0.08)',
        glow: '0 0 24px rgba(212, 245, 66, 0.15)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulse_dot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.35' },
        },
        marquee: {
          '0%': { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.5s ease-out forwards',
        'pulse-dot': 'pulse_dot 2.4s ease-in-out infinite',
        marquee: 'marquee 40s linear infinite',
      },
    },
  },
  plugins: [],
};
