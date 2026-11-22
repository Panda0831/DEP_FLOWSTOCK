import { useCallback, useMemo, useState } from 'react';
import { ActivityIndicator, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { AppleMaps, GoogleMaps } from 'expo-maps';
import * as Location from 'expo-location';
import type { DeliveryMapPoint } from './delivery-location-map.types';

type Coordinates = { latitude: number; longitude: number };
type SelectedLocation = { coordinates: Coordinates; title: string; address: string; detail: string };

const DEFAULT_CENTER: Coordinates = { latitude: -18.8792, longitude: 47.5079 };

function formatAddress(value: Location.LocationGeocodedAddress | undefined) {
  if (!value) return '';
  return [value.name, value.street, value.district, value.city, value.region, value.postalCode, value.country]
    .filter((part, index, all): part is string => Boolean(part) && all.indexOf(part) === index)
    .join(', ');
}

function coordinatesFromMap(value: { latitude?: number; longitude?: number }): Coordinates | null {
  if (!Number.isFinite(value.latitude) || !Number.isFinite(value.longitude)) return null;
  return { latitude: value.latitude!, longitude: value.longitude! };
}

export function DeliveryLocationMap({ points }: { points: DeliveryMapPoint[] }) {
  const [mapType, setMapType] = useState<'satellite' | 'plan'>('satellite');
  const [selected, setSelected] = useState<SelectedLocation | null>(null);
  const [lookingUp, setLookingUp] = useState(false);

  const validPoints = useMemo(() => points.filter((point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude)), [points]);
  const initialCenter = validPoints[0]
    ? { latitude: validPoints[0].latitude!, longitude: validPoints[0].longitude! }
    : DEFAULT_CENTER;

  const markers = useMemo(() => [
    ...validPoints.map((point) => ({
      id: point.id,
      coordinates: { latitude: point.latitude!, longitude: point.longitude! },
      title: point.title,
      snippet: point.detail,
      showCallout: true,
    })),
    ...(selected ? [{ id: 'selected-location', coordinates: selected.coordinates, title: selected.title, snippet: selected.address || selected.detail, showCallout: true }] : []),
  ], [selected, validPoints]);

  const annotations = useMemo(() => [
    ...validPoints.map((point) => ({
      id: point.id,
      coordinates: { latitude: point.latitude!, longitude: point.longitude! },
      text: point.title,
    })),
    ...(selected ? [{ id: 'selected-location', coordinates: selected.coordinates, text: selected.title }] : []),
  ], [selected, validPoints]);

  const reverseGeocode = useCallback(async (coordinates: Coordinates, title = 'Emplacement sélectionné') => {
    setSelected({ coordinates, title, address: '', detail: '' });
    setLookingUp(true);
    try {
      if (Platform.OS === 'android') {
        const permission = await Location.getForegroundPermissionsAsync();
        const granted = permission.granted || (await Location.requestForegroundPermissionsAsync()).granted;
        if (!granted) return;
      }
      const [result] = await Location.reverseGeocodeAsync(coordinates);
      const address = formatAddress(result);
      setSelected({
        coordinates,
        title,
        address,
        detail: result?.city || result?.region || result?.country || '',
      });
    } catch {
      // Keep the selected coordinates visible when address lookup is unavailable.
    } finally {
      setLookingUp(false);
    }
  }, []);

  const selectPoint = useCallback((id?: string) => {
    const point = validPoints.find((item) => item.id === id);
    if (!point || point.latitude === undefined || point.longitude === undefined) return;
    setSelected({
      coordinates: { latitude: point.latitude, longitude: point.longitude },
      title: point.title,
      address: point.address,
      detail: point.detail,
    });
  }, [validPoints]);

  return <View style={styles.card}>
    <View style={styles.header}>
      <View style={styles.headingCopy}>
        <Text style={styles.title}>Carte des livraisons</Text>
        <Text style={styles.caption}>Touchez un point pour afficher ses informations.</Text>
      </View>
      <View style={styles.mapModes}>
        <Pressable onPress={() => setMapType('plan')} style={[styles.modeButton, mapType === 'plan' && styles.modeActive]} accessibilityRole="button" accessibilityState={{ selected: mapType === 'plan' }}>
          <Text style={[styles.modeText, mapType === 'plan' && styles.modeTextActive]}>Plan</Text>
        </Pressable>
        <Pressable onPress={() => setMapType('satellite')} style={[styles.modeButton, mapType === 'satellite' && styles.modeActive]} accessibilityRole="button" accessibilityState={{ selected: mapType === 'satellite' }}>
          <Text style={[styles.modeText, mapType === 'satellite' && styles.modeTextActive]}>Satellite</Text>
        </Pressable>
      </View>
    </View>

    <PlatformView mapType={mapType} initialCenter={initialCenter} markers={markers} annotations={annotations} reverseGeocode={reverseGeocode} selectPoint={selectPoint} />

    {selected ? <View style={styles.locationDetails} accessibilityLiveRegion="polite">
      <View style={styles.locationPin}><Text style={styles.locationPinText}>⌖</Text></View>
      <View style={styles.locationCopy}>
        <Text style={styles.locationTitle}>{selected.title}</Text>
        {lookingUp ? <View style={styles.lookupRow}><ActivityIndicator size="small" color="#078343" /><Text style={styles.locationAddress}>Recherche de l’adresse…</Text></View> :
          <Text style={styles.locationAddress}>{selected.address || `${selected.coordinates.latitude.toFixed(5)}, ${selected.coordinates.longitude.toFixed(5)}`}</Text>}
        {!!selected.detail && !lookingUp && <Text style={styles.locationMeta}>{selected.detail}</Text>}
      </View>
    </View> : <Text style={styles.hint}>{validPoints.length === 0 && points.length > 0 ? 'Les livraisons n’ont pas encore de coordonnées GPS. Touchez la carte pour afficher les informations du lieu choisi.' : 'Aucune saisie requise : touchez la carte pour lire l’adresse et les coordonnées du lieu.'}</Text>}
  </View>;
}

function PlatformView({ mapType, initialCenter, markers, annotations, reverseGeocode, selectPoint }: {
  mapType: 'satellite' | 'plan';
  initialCenter: Coordinates;
  markers: GoogleMaps.Marker[];
  annotations: AppleMaps.Annotation[];
  reverseGeocode: (coordinates: Coordinates, title?: string) => void;
  selectPoint: (id?: string) => void;
}) {
  if (Platform.OS === 'ios') {
    return <AppleMaps.View
      style={styles.map}
      cameraPosition={{ coordinates: initialCenter, zoom: 12 }}
      annotations={annotations}
      properties={{ mapType: mapType === 'satellite' ? AppleMaps.MapType.HYBRID : AppleMaps.MapType.STANDARD, selectionEnabled: true }}
      onMapClick={({ coordinates }) => {
        const point = coordinatesFromMap(coordinates);
        if (point) reverseGeocode(point);
      }}
      onAnnotationClick={(event) => selectPoint(event.id)}
    />;
  }

  return <GoogleMaps.View
    style={styles.map}
    cameraPosition={{ coordinates: initialCenter, zoom: 12 }}
    markers={markers}
    properties={{ mapType: mapType === 'satellite' ? GoogleMaps.MapType.HYBRID : GoogleMaps.MapType.NORMAL, selectionEnabled: true }}
    onMapClick={({ coordinates }) => {
      const point = coordinatesFromMap(coordinates);
      if (point) reverseGeocode(point);
    }}
    onPOIClick={({ name, coordinates }) => {
      const point = coordinatesFromMap(coordinates);
      if (point) reverseGeocode(point, name);
    }}
    onMarkerClick={(event) => selectPoint(event.id)}
  />;
}

const styles = StyleSheet.create({
  card: { backgroundColor: '#FFFFFF', borderRadius: 18, padding: 15, borderWidth: 1, borderColor: '#DDE9DF', marginBottom: 18, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 7, elevation: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10, marginBottom: 12 },
  headingCopy: { flex: 1 },
  title: { color: '#173D2B', fontSize: 14, fontWeight: '800' },
  caption: { color: '#77827A', fontSize: 10, marginTop: 3 },
  mapModes: { flexDirection: 'row', padding: 3, borderRadius: 11, backgroundColor: '#F0F4F1' },
  modeButton: { paddingHorizontal: 9, paddingVertical: 7, borderRadius: 8 },
  modeActive: { backgroundColor: '#078343' },
  modeText: { color: '#65736A', fontSize: 10, fontWeight: '700' },
  modeTextActive: { color: '#FFFFFF' },
  map: { height: 240, width: '100%', overflow: 'hidden', borderRadius: 14, backgroundColor: '#E7F5EC' },
  locationDetails: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12, padding: 11, borderRadius: 13, backgroundColor: '#F0F8F2', borderWidth: 1, borderColor: '#DDE9DF' },
  locationPin: { width: 34, height: 34, alignItems: 'center', justifyContent: 'center', borderRadius: 11, backgroundColor: '#E1F2E6' },
  locationPinText: { color: '#078343', fontSize: 20, fontWeight: '800' },
  locationCopy: { flex: 1 },
  lookupRow: { flexDirection: 'row', alignItems: 'center', gap: 7, marginTop: 4 },
  locationTitle: { color: '#173D2B', fontSize: 11, fontWeight: '800' },
  locationAddress: { color: '#526259', fontSize: 11, marginTop: 4 },
  locationMeta: { color: '#77827A', fontSize: 10, marginTop: 3 },
  hint: { color: '#77827A', fontSize: 11, lineHeight: 16, marginTop: 10 },
});
