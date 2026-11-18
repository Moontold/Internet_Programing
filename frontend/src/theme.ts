import { createTheme, type MantineColorsTuple } from '@mantine/core';

const ink: MantineColorsTuple = [
  '#e6f4f2',
  '#cfe6e2',
  '#a3cfc8',
  '#74b7ad',
  '#4fa397',
  '#399789',
  '#2b8f80',
  '#1d7c6e',
  '#0f6f62',
  '#005f53',
];

const slate: MantineColorsTuple = [
  '#f5f6f8',
  '#e9ebf0',
  '#d5d9e2',
  '#b8bfcc',
  '#9aa3b5',
  '#7c869c',
  '#646e85',
  '#4e5870',
  '#36405a',
  '#182033',
];

export const theme = createTheme({
  fontFamily: '"Golos Text Variable", "Golos Text", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  headings: {
    fontFamily: '"Golos Text Variable", "Golos Text", system-ui, sans-serif',
    fontWeight: '700',
    sizes: {
      h1: { fontSize: '2rem', lineHeight: '1.2' },
      h2: { fontSize: '1.625rem', lineHeight: '1.25' },
      h3: { fontSize: '1.25rem', lineHeight: '1.3' },
      h4: { fontSize: '1.0625rem', lineHeight: '1.35' },
      h5: { fontSize: '0.9375rem', lineHeight: '1.4' },
    },
  },
  primaryColor: 'ink',
  primaryShade: 7,
  colors: { ink, slate },
  black: '#182033',
  defaultRadius: 'sm',
  radius: { xs: '3px', sm: '6px', md: '10px', lg: '14px', xl: '20px' },
  fontSizes: { xs: '0.8125rem', sm: '0.875rem', md: '1rem', lg: '1.125rem', xl: '1.25rem' },
  lineHeights: { xs: '1.4', sm: '1.45', md: '1.55', lg: '1.6', xl: '1.65' },
  shadows: { xs: 'none', sm: 'none', md: '0 8px 24px rgba(24, 32, 51, 0.10)', lg: '0 12px 32px rgba(24, 32, 51, 0.14)', xl: '0 16px 40px rgba(24, 32, 51, 0.16)' },
  components: {
    Card: {
      defaultProps: { padding: 'lg', radius: 'md', withBorder: true },
      styles: { root: { borderColor: 'var(--mantine-color-slate-1)', backgroundColor: '#ffffff' } },
    },
    Button: {
      defaultProps: { radius: 'sm' },
      styles: { root: { fontWeight: 600 } },
    },
    Badge: {
      defaultProps: { radius: 'sm' },
      styles: { root: { textTransform: 'none', fontWeight: 600, letterSpacing: 0 } },
    },
    Table: {
      styles: { th: { fontWeight: 600, color: 'var(--mantine-color-slate-6)' } },
    },
    Modal: {
      defaultProps: { radius: 'md', overlayProps: { backgroundOpacity: 0.35, blur: 2 } },
    },
    Title: {
      styles: { root: { letterSpacing: '-0.01em' } },
    },
  },
});
