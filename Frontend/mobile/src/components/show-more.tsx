import { StyleSheet, Text } from 'react-native';

import { MotionPressable } from '@/components/motion';
import { HitSize, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export const LIST_PAGE_SIZE = 20;

/** Reveals the next slice of an already loaded list. */
export function ShowMore({ remaining, onPress }: { remaining: number; onPress: () => void }) {
  const t = useAppTheme();
  if (remaining <= 0) return null;

  return (
    <MotionPressable
      onPress={onPress}
      style={[styles.button, { borderColor: t.separator }]}
      accessibilityRole="button"
      accessibilityLabel={`Afficher ${remaining} éléments de plus`}>
      <Text style={[styles.text, { color: t.tint }]}>Afficher {remaining} de plus</Text>
    </MotionPressable>
  );
}

const styles = StyleSheet.create({
  button: { minHeight: HitSize, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderRadius: 12, marginTop: 8 },
  text: { ...Type.footnote, fontWeight: '600' },
});
