import { StyleSheet, Text, View } from 'react-native';

import { useAppTheme } from '@/hooks/use-app-theme';

/** Static brand mark: the name never changes and nothing loops in the background. */
export function BrandLockup({ variant = 'compact', tagline = false }: { variant?: 'compact' | 'hero'; tagline?: boolean }) {
  const t = useAppTheme();
  const hero = variant === 'hero';

  return (
    <View style={hero ? styles.hero : styles.compact} accessibilityRole="text" accessibilityLabel="FlowStock">
      <View style={[hero ? styles.heroMark : styles.compactMark, { backgroundColor: t.tint }]}>
        <Text style={[hero ? styles.heroLetter : styles.compactLetter, { color: t.onTint }]}>S</Text>
      </View>
      <View style={hero ? styles.heroCopy : styles.compactCopy}>
        <Text style={[hero ? styles.heroName : styles.compactName, { color: t.text }]}>FlowStock</Text>
        {!!tagline && <Text style={[styles.tagline, { color: t.secondaryText }]}>Gérez votre activité en toute simplicité</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  compact: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  compactMark: { width: 44, height: 44, borderRadius: 14, alignItems: 'center', justifyContent: 'center' },
  compactLetter: { fontSize: 26, fontWeight: '700', lineHeight: 31 },
  compactCopy: { gap: 2 },
  compactName: { fontSize: 22, lineHeight: 27, fontWeight: '700', letterSpacing: -0.4 },
  hero: { alignItems: 'center', gap: 12 },
  heroMark: { width: 64, height: 64, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  heroLetter: { fontSize: 38, fontWeight: '700', lineHeight: 45 },
  heroCopy: { alignItems: 'center', gap: 4 },
  heroName: { fontSize: 32, lineHeight: 38, fontWeight: '700', letterSpacing: -0.6 },
  tagline: { fontSize: 13, lineHeight: 18, textAlign: 'center' },
});
