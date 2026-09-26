import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        /* Semantic Tokens required by SPEC.md */
        canvas: {
          DEFAULT: '#FAF8F5',
          warm: '#FAF8F5',
          cream: '#FFF8F3',
          sheet: '#FFFFFF',
          tint: '#EEE6DE',
        },
        surface: {
          DEFAULT: '#FFF8F3',
          dim: '#DFD9D4',
          bright: '#FFF8F3',
          card: '#FFFFFF',
          lowest: '#FFFFFF',
          low: '#F9F2ED',
          container: '#F3EDE7',
          high: '#EDE7E2',
          highest: '#E8E1DC',
          variant: '#E8E1DC',
          tint: '#366666',
        },
        hairline: {
          DEFAULT: '#E2DDD5',
          dark: '#D8D2C7',
          light: '#EAE5DC',
        },
        ink: {
          DEFAULT: '#1A1815',
          carbon: '#1A1815',
          deep: '#1D1B18',
        },
        'ink-muted': '#68625B',
        'ink-subtle': '#8C847A',
        accent: {
          DEFAULT: '#0F5C5C',
          deep: '#002B2B',
          hover: '#0A4242',
          wash: '#E6F0F0',
        },

        /* Risk Spectrum Data Scale: 100 / 300 / 500 / 700 / 900 */
        risk: {
          100: '#E8D5B7', /* Sand Ochre / Low */
          300: '#D89B4A', /* Regulatory Amber / Moderate */
          500: '#B4472F', /* Investigative Rust / High */
          700: '#7A2418', /* Civic Maroon / Critical */
          900: '#400100', /* Deepest Maroon */
          low: '#E8D5B7',
          moderate: '#D89B4A',
          high: '#B4472F',
          critical: '#7A2418',
          'low-bg': '#FAF5EE',
          'low-border': '#E8D5B7',
          'low-text': '#68625B',
          'moderate-bg': '#FDF6EC',
          'moderate-border': '#D89B4A',
          'moderate-text': '#7A4C10',
          'high-bg': '#FBF0ED',
          'high-border': '#B4472F',
          'high-text': '#87230E',
          'critical-bg': '#F7ECEB',
          'critical-border': '#7A2418',
          'critical-text': '#7A2418',
        },

        /* Stitch Export Direct Tokens (ensures 100% faithful class compatibility) */
        primary: {
          DEFAULT: '#002b2b',
          container: '#0a4242',
          fixed: '#b9eceb',
          'fixed-dim': '#9ed0cf',
        },
        'on-primary': '#ffffff',
        'on-primary-container': '#7daead',
        'on-primary-fixed': '#002020',
        'on-primary-fixed-variant': '#1b4e4e',
        'inverse-primary': '#9ed0cf',

        secondary: {
          DEFAULT: '#635d57',
          container: '#eae1d8',
          fixed: '#eae1d8',
          'fixed-dim': '#cec5bd',
        },
        'on-secondary': '#ffffff',
        'on-secondary-container': '#69635c',
        'on-secondary-fixed': '#1f1b16',
        'on-secondary-fixed-variant': '#4b463f',

        tertiary: {
          DEFAULT: '#510501',
          container: '#701d12',
          fixed: '#ffdad4',
          'fixed-dim': '#ffb4a7',
        },
        'on-tertiary': '#ffffff',
        'on-tertiary-container': '#f98370',
        'on-tertiary-fixed': '#400100',
        'on-tertiary-fixed-variant': '#80281c',

        error: {
          DEFAULT: '#ba1a1a',
          container: '#ffdad6',
        },
        'on-error': '#ffffff',
        'on-error-container': '#93000a',

        outline: '#707978',
        'outline-variant': '#c0c8c7',
        background: '#fff8f3',
        'on-background': '#1d1b18',
        'on-surface': '#1d1b18',
        'on-surface-variant': '#404848',
        'inverse-surface': '#33302d',
        'inverse-on-surface': '#f6f0ea',

        'surface-dim': '#dfd9d4',
        'surface-bright': '#fff8f3',
        'surface-container-lowest': '#ffffff',
        'surface-container-low': '#f9f2ed',
        'surface-container': '#f3ede7',
        'surface-container-high': '#ede7e2',
        'surface-container-highest': '#e8e1dc',
        'surface-variant': '#e8e1dc',
        'surface-tint': '#366666',
      },

      borderRadius: {
        DEFAULT: '0.125rem',
        sm: '0.125rem',
        md: '0.25rem',
        lg: '0.25rem',
        xl: '0.5rem',
        full: '9999px',
      },

      spacing: {
        'margin-tablet': '2rem',
        'space-md': '0.875rem',
        'space-sm': '0.5rem',
        'space-xl': '2.5rem',
        'margin-desktop': '3rem',
        'space-xs': '0.25rem',
        'space-2xl': '4rem',
        gutter: '1.25rem',
        'space-lg': '1.5rem',
        'gutter-desktop': '1.75rem',
        margin: '1rem',
      },

      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Newsreader', 'Georgia', 'serif'],
        'display-figure': ['Newsreader', 'serif'],
        'headline-lg': ['Newsreader', 'serif'],
        'headline-md': ['Newsreader', 'serif'],
        'headline-sm': ['Newsreader', 'serif'],
        'headline-lg-mobile': ['Newsreader', 'serif'],
        'body-lg': ['Newsreader', 'serif'],
        'body-md': ['Inter', 'sans-serif'],
        'body-sm': ['Inter', 'sans-serif'],
        'label-caps': ['Inter', 'sans-serif'],
        'display-figure-mobile': ['Newsreader', 'serif'],
        'data-metric': ['Inter', 'sans-serif'],
        'code-tabular': ['Inter', 'monospace'],
      },

      fontSize: {
        'display-figure': ['3.75rem', { lineHeight: '1.05', letterSpacing: '-0.025em', fontWeight: '500' }],
        'headline-lg': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.015em', fontWeight: '600' }],
        'headline-md': ['1.5rem', { lineHeight: '1.3', letterSpacing: '-0.01em', fontWeight: '600' }],
        'label-caps': ['0.6875rem', { lineHeight: '1.3', letterSpacing: '0.08em', fontWeight: '600' }],
        'display-figure-mobile': ['2.5rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '500' }],
        'data-metric': ['1.25rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body-lg': ['1.125rem', { lineHeight: '1.75', fontWeight: '400' }],
        'body-md': ['0.9375rem', { lineHeight: '1.6', fontWeight: '400' }],
        'headline-sm': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
        'headline-lg-mobile': ['1.75rem', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '600' }],
        'body-sm': ['0.8125rem', { lineHeight: '1.5', fontWeight: '400' }],
        'code-tabular': ['0.8125rem', { lineHeight: '1.4', fontWeight: '500' }],
      },
    },
  },
  plugins: [],
};

export default config;
