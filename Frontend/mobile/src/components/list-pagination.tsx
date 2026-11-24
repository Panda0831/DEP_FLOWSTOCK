import { StyleSheet, Text, View } from 'react-native';

import { MotionPressable } from '@/components/motion';
import { HitSize, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export const LIST_PAGE_SIZE = 10;

/** Shared previous/next controls for mobile lists. */
export function PageNavigation({ page, totalItems, pageSize = LIST_PAGE_SIZE, onPageChange }: {
  page: number;
  totalItems: number;
  pageSize?: number;
  onPageChange: (page: number) => void;
}) {
  const t = useAppTheme();
  const pageCount = Math.max(1, Math.ceil(totalItems / pageSize));
  if (totalItems <= pageSize) return null;
  const currentPage = Math.min(page, pageCount);

  return (
    <View style={[styles.container, { borderColor: t.separator }]}>
      <MotionPressable
        onPress={() => onPageChange(Math.max(1, currentPage - 1))}
        disabled={currentPage <= 1}
        style={[styles.button, currentPage <= 1 && styles.disabled]}
        accessibilityRole="button"
        accessibilityLabel="Page précédente"
        accessibilityState={{ disabled: currentPage <= 1 }}>
        <Text style={[styles.text, { color: t.tint }]}>‹ Précédent</Text>
      </MotionPressable>
      <Text style={[styles.page, { color: t.secondaryText }]}>Page {currentPage} sur {pageCount}</Text>
      <MotionPressable
        onPress={() => onPageChange(Math.min(pageCount, currentPage + 1))}
        disabled={currentPage >= pageCount}
        style={[styles.button, currentPage >= pageCount && styles.disabled]}
        accessibilityRole="button"
        accessibilityLabel="Page suivante"
        accessibilityState={{ disabled: currentPage >= pageCount }}>
        <Text style={[styles.text, { color: t.tint }]}>Suivant ›</Text>
      </MotionPressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { minHeight: HitSize, borderTopWidth: 1, marginTop: 8, paddingTop: 8, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 6 },
  button: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 8 },
  disabled: { opacity: 0.4 },
  text: { ...Type.footnote, fontWeight: '600' },
  page: { ...Type.footnote, fontWeight: '600' },
});
