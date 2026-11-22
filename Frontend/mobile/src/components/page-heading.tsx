import { StyleSheet, Text, View } from 'react-native';
import { BrandLockup } from '@/components/brand-lockup';
import { FadeIn } from '@/components/motion';

export function AppPageHeading({ title, subtitle }: { title: string; subtitle: string }) {
  return <>
    <FadeIn><View style={styles.brand}><BrandLockup /></View></FadeIn>
    <FadeIn delay={70}><View style={styles.heading}>
      <View style={styles.accent} />
      <View style={styles.copy}><Text style={styles.title}>{title}</Text><Text style={styles.subtitle}>{subtitle}</Text></View>
    </View></FadeIn>
  </>;
}

const styles = StyleSheet.create({
  brand: { marginBottom: 19 },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 13, marginBottom: 22 },
  accent: { width: 4, height: 43, borderRadius: 4, backgroundColor: '#078343' },
  copy: { flex: 1 },
  title: { color: '#142039', fontSize: 29, fontWeight: '800' },
  subtitle: { color: '#6B7380', fontSize: 14, marginTop: 5 },
});
