import { useMemo } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import type { DeliveryMapPoint } from './delivery-location-map.types';
import type { AppTheme } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export type { DeliveryMapPoint } from './delivery-location-map.types';

function getMapUrl(point: DeliveryMapPoint) {
  const hasCoordinates = Number.isFinite(point.latitude) && Number.isFinite(point.longitude);
  if (hasCoordinates) {
    return `https://www.google.com/maps/@?api=1&map_action=map&center=${point.latitude},${point.longitude}&zoom=16&basemap=satellite`;
  }
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(point.address || point.title)}`;
}

export function DeliveryLocationMap({ points }: { points: DeliveryMapPoint[] }) {
  const theme = useAppTheme();
  const styles = useMemo(() => makeStyles(theme), [theme]);
  return <View style={styles.card}>
    <View style={styles.header}>
      <View style={styles.headingCopy}>
        <Text style={styles.title}>Emplacements des livraisons</Text>
        <Text style={styles.caption}>Ouvrez une adresse pour consulter son emplacement.</Text>
      </View>
    </View>
    {points.length === 0 ? <Text style={styles.empty}>Aucune adresse de livraison disponible pour le moment.</Text> : points.slice(0, 5).map((point) => <Pressable key={point.id} onPress={() => void Linking.openURL(getMapUrl(point))} style={styles.point} accessibilityRole="link">
      <View style={styles.pin}><Text style={styles.pinText}>⌖</Text></View>
      <View style={styles.pointCopy}><Text style={styles.pointTitle}>{point.title}</Text><Text style={styles.pointAddress} numberOfLines={2}>{point.address || 'Adresse non renseignée'}</Text><Text style={styles.pointDetail}>{point.detail}</Text></View>
      <Text style={styles.open}>{Number.isFinite(point.latitude) && Number.isFinite(point.longitude) ? 'Satellite ›' : 'Voir ›'}</Text>
    </Pressable>)}
    {points.length > 5 && <Text style={styles.more}>+ {points.length - 5} autres livraisons sont visibles sur mobile.</Text>}
  </View>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  card: { backgroundColor: t.surface, borderRadius: 18, padding: 15, borderWidth: 1, borderColor: t.separator, marginBottom: 18 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 10 },
  headingCopy: { flex: 1 },
  title: { color: t.text, fontSize: 14, fontWeight: '800' },
  caption: { color: t.secondaryText, fontSize: 12, lineHeight: 17, marginTop: 3 },
  empty: { color: t.secondaryText, fontSize: 14, lineHeight: 21, paddingVertical: 10 },
  point: { flexDirection: 'row', alignItems: 'center', gap: 9, paddingVertical: 10, borderTopWidth: 1, borderTopColor: t.separator },
  pin: { width: 30, height: 30, borderRadius: 10, alignItems: 'center', justifyContent: 'center', backgroundColor: t.tintSurface },
  pinText: { color: t.tint, fontSize: 18, fontWeight: '800' },
  pointCopy: { flex: 1 },
  pointTitle: { color: t.text, fontSize: 14, lineHeight: 20, fontWeight: '800' },
  pointAddress: { color: t.secondaryText, fontSize: 13, lineHeight: 18, marginTop: 3 },
  pointDetail: { color: t.secondaryText, fontSize: 12, lineHeight: 17, marginTop: 3 },
  open: { color: t.tint, fontSize: 13, lineHeight: 18, fontWeight: '800' },
  more: { color: t.secondaryText, fontSize: 13, lineHeight: 18, paddingTop: 7 },
});
