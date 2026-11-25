import '@/global.css';

import { Platform } from 'react-native';

/**
 * Semantic tokens used by the shared components.
 * Roles come first, raw values second: one color means one thing.
 * Accent contrast against `surface`: 6.99:1 in light and 8.73:1 in dark.
 */
export const AppColors = {
  light: {
    background: '#F3F7F5',
    surface: '#FFFFFF',
    text: '#18332F',
    secondaryText: '#526864',
    separator: '#DCE7E2',
    tint: '#11645D',
    onTint: '#FFFFFF',
    tintSurface: '#E5F2EF',
    danger: '#A43D32',
    dangerSurface: '#FBECE9',
    warning: '#80520B',
    warningSurface: '#FFF3D9',
  },
  dark: {
    background: '#101917',
    surface: '#1B2623',
    text: '#EFF6F3',
    secondaryText: '#B0C0BA',
    separator: '#34443F',
    tint: '#69D4BF',
    onTint: '#10221E',
    tintSurface: '#203B35',
    danger: '#FF8C7D',
    dangerSurface: '#3B2522',
    warning: '#FFD080',
    warningSurface: '#3A301E',
  },
} as const;

export type AppTheme = { [K in keyof (typeof AppColors)['light']]: string };

/** Compatibility names for the remaining themed starter components. */
export const Colors = {
  light: {
    text: AppColors.light.text,
    background: AppColors.light.background,
    backgroundElement: AppColors.light.surface,
    backgroundSelected: AppColors.light.tintSurface,
    textSecondary: AppColors.light.secondaryText,
  },
  dark: {
    text: AppColors.dark.text,
    background: AppColors.dark.background,
    backgroundElement: AppColors.dark.surface,
    backgroundSelected: AppColors.dark.tintSurface,
    textSecondary: AppColors.dark.secondaryText,
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'sans-serif',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const BottomTabInset = Platform.select({ ios: 50, android: 80 }) ?? 0;
export const MaxContentWidth = 800;

export const Type = {
  title: { fontSize: 28, lineHeight: 34, fontWeight: '700' as const },
  headline: { fontSize: 17, lineHeight: 22, fontWeight: '600' as const },
  body: { fontSize: 16, lineHeight: 22, fontWeight: '400' as const },
  footnote: { fontSize: 13, lineHeight: 18, fontWeight: '400' as const },
  caption: { fontSize: 13, lineHeight: 18, fontWeight: '500' as const },
};

export const Radius = { control: 12, card: 16, sheet: 24 } as const;
export const HitSize = 44;
