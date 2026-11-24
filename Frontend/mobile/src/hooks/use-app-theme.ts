import { useColorScheme } from '@/hooks/use-color-scheme';
import { AppColors, type AppTheme } from '@/constants/theme';

export type { AppTheme } from '@/constants/theme';

/** Light/dark semantic palette. The system setting is the only appearance switch. */
export function useAppTheme(): AppTheme {
  const scheme = useColorScheme();
  return AppColors[scheme === 'dark' ? 'dark' : 'light'];
}
