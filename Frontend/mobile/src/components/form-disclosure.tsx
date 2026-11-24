import { useEffect, useState, type PropsWithChildren } from 'react';
import { useLocalSearchParams } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { HitSize, Radius, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';
import { MotionPressable } from '@/components/motion';

/** True when the screen was opened with `?add=1`, e.g. from a Home quick action. */
export function useAutoOpenForm() {
  const params = useLocalSearchParams<{ add?: string }>();
  return params.add === '1';
}

/** Keeps the list as the main content: the form opens only when asked for. */
export function FormDisclosure({ label, openWhen, children }: PropsWithChildren<{ label: string; openWhen?: string | null }>) {
  const [open, setOpen] = useState(false);
  const t = useAppTheme();

  useEffect(() => {
    if (openWhen) setOpen(true);
  }, [openWhen]);

  return (
    <View style={styles.wrap}>
      <MotionPressable
        onPress={() => setOpen((value) => !value)}
        style={[styles.toggle, { backgroundColor: t.surface, borderColor: t.separator }]}
        accessibilityRole="button"
        accessibilityLabel={label}
        accessibilityState={{ expanded: open }}>
        <Text style={[styles.toggleText, { color: t.tint }]}>{open ? `Masquer ${label.toLowerCase()}` : label}</Text>
        <Text style={[styles.chevron, { color: t.tint }]}>{open ? '−' : '+'}</Text>
      </MotionPressable>
      {open && <View style={styles.body}>{children}</View>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 12 },
  toggle: { minHeight: HitSize, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, borderRadius: Radius.control, borderWidth: 1 },
  toggleText: { ...Type.body, fontWeight: '600' },
  chevron: { fontSize: 22, lineHeight: 24, marginLeft: 12 },
  body: { marginTop: 8 },
});
