import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
import { api, getApiBaseUrl, getSessionCookieHeaders } from '@/lib/session-api';

type Summary = { chiffre_affaires: string; benefice_brut: string; depenses: string; benefice_net: string; commandes_livrees: number };
type ProductReport = { idProduit__public_id: string; idProduit__nomProduit: string; quantite_vendue: number; chiffre_affaires: string; benefice_brut: string };
type OrderReport = { public_id: string; client: string; date_livraison: string; chiffre_affaires: string; benefice: string };
const EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

function localDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export default function ReportsScreen() {
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  const today = localDate(new Date());
  const [start, setStart] = useState(`${today.slice(0, 7)}-01`);
  const [end, setEnd] = useState(today);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [products, setProducts] = useState<ProductReport[]>([]);
  const [orders, setOrders] = useState<OrderReport[]>([]);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    if (!admin) return;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end) || end < start) {
      setError('Saisissez une période valide au format AAAA-MM-JJ.');
      return;
    }
    setLoading(true); setError('');
    try {
      const params = { start_date: start, end_date: end };
      const [financialSummary, productReport, orderReport] = await Promise.all([
        api.get<Summary>('/reports/summary/', params),
        api.get<ProductReport[]>('/reports/products/', params),
        api.get<OrderReport[]>('/reports/orders/', params),
      ]);
      setSummary(financialSummary); setProducts(productReport); setOrders(orderReport);
    } catch (e) { setError(e instanceof Error ? e.message : 'Rapport indisponible.'); }
    finally { setLoading(false); }
  }, [admin, end, start]);
  useEffect(() => { void load(); }, [load]);

  const exportExcel = async () => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(start) || !/^\d{4}-\d{2}-\d{2}$/.test(end) || end < start) {
      setError('Saisissez une période valide au format AAAA-MM-JJ.');
      return;
    }
    setExporting(true); setError('');
    const url = `${getApiBaseUrl()}/exports/excel/?start_date=${encodeURIComponent(start)}&end_date=${encodeURIComponent(end)}`;
    try {
      if (Platform.OS === 'web') {
        await Linking.openURL(url);
        return;
      }
      if (!(await Sharing.isAvailableAsync())) {
        Alert.alert('Export indisponible', 'Le partage de fichiers n’est pas disponible sur cet appareil.');
        return;
      }
      const fileName = `rapport-flowstock-${start}-${end}.xlsx`;
      const file = await File.downloadFileAsync(url, new File(Paths.cache, fileName), {
        headers: await getSessionCookieHeaders(),
        idempotent: true,
      });
      await Sharing.shareAsync(file.uri, { mimeType: EXCEL_MIME, dialogTitle: 'Exporter le rapport Excel' });
    } catch (e) { setError(e instanceof Error ? e.message : 'Export impossible.'); }
    finally { setExporting(false); }
  };

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <View style={ui.pageHeading}><View style={ui.headingAccent} /><View><Text style={ui.title}>Rapports</Text><Text style={ui.subtitle}>Résultats calculés par le backend sur la période choisie.</Text></View></View>
    {!admin ? <Text style={ui.error}>Les rapports financiers sont réservés aux administrateurs.</Text> : <>
      <View style={ui.card}><Text style={ui.cardTitle}>Période</Text>
        <TextInput style={ui.input} value={start} onChangeText={setStart} placeholder="Début (AAAA-MM-JJ)" />
        <TextInput style={ui.input} value={end} onChangeText={setEnd} placeholder="Fin (AAAA-MM-JJ)" />
        <Action label={loading ? 'Chargement…' : 'Afficher le rapport'} onPress={() => void load()} disabled={loading} />
      </View>
      {!!error && <Text style={ui.error}>{error}</Text>}
      {loading && !summary ? <ActivityIndicator color="#078343" style={{ margin: 20 }} /> : null}
      {summary && <>
        <View style={styles.grid}>{[
          ['Chiffre d’affaires', summary.chiffre_affaires], ['Bénéfice brut', summary.benefice_brut],
          ['Dépenses', summary.depenses], ['Bénéfice net', summary.benefice_net],
          ['Commandes livrées', String(summary.commandes_livrees)],
        ].map(([label, value]) => <View key={label} style={styles.metric}>
          <Text style={styles.metricLabel}>{label}</Text>
          <Text style={styles.metricValue}>{label === 'Commandes livrées' ? value : `${Number(value).toLocaleString('fr-FR')} Ar`}</Text>
        </View>)}</View>
        <Action label={exporting ? 'Préparation…' : 'Exporter en Excel'} onPress={() => void exportExcel()} disabled={exporting} />
        <View style={styles.chartCard}>
          <View style={styles.chartHeading}><View><Text style={ui.section}>Ventes par produit</Text><Text style={styles.chartCaption}>Chiffre d’affaires sur la période</Text></View><Text style={styles.chartUnit}>AR</Text></View>
          {products.length === 0 ? <Text style={ui.empty}>Aucune vente sur cette période.</Text> : [...products].sort((a, b) => Number(b.chiffre_affaires) - Number(a.chiffre_affaires)).slice(0, 6).map((item, _index, rows) => {
            const maximum = Math.max(...rows.map((row) => Number(row.chiffre_affaires)), 1);
            const share = Math.max(5, Number(item.chiffre_affaires) / maximum * 100);
            return <View key={item.idProduit__public_id} style={styles.chartRow}>
              <View style={styles.chartMeta}><Text style={styles.chartName} numberOfLines={1}>{item.idProduit__nomProduit}</Text><Text style={styles.chartAmount}>{Number(item.chiffre_affaires).toLocaleString('fr-FR')} Ar</Text></View>
              <View style={styles.track}><View style={[styles.fill, { width: `${share}%` }]} /></View>
              <Text style={styles.chartDetail}>{item.quantite_vendue} vendu(s) · bénéfice brut {Number(item.benefice_brut).toLocaleString('fr-FR')} Ar</Text>
            </View>;
          })}
        </View>
        <View style={styles.chartCard}>
          <View style={styles.chartHeading}><View><Text style={ui.section}>Commandes livrées</Text><Text style={styles.chartCaption}>Ventes confirmées sur la période</Text></View><Text style={styles.chartUnit}>{orders.length}</Text></View>
          {orders.length === 0 ? <Text style={ui.empty}>Aucune commande livrée sur cette période.</Text> : orders.slice(0, 6).map((item) => <View key={item.public_id} style={styles.row}>
            <View style={{ flex: 1 }}><Text style={styles.name}>{item.client}</Text><Text style={styles.sub}>{item.date_livraison}</Text></View>
            <View style={styles.orderAmount}><Text style={styles.amountValue}>{Number(item.chiffre_affaires).toLocaleString('fr-FR')} Ar</Text><Text style={styles.sub}>Bénéfice {Number(item.benefice).toLocaleString('fr-FR')} Ar</Text></View>
          </View>)}
        </View>
      </>}
    </>}
  </ScrollView>;
}

const styles = StyleSheet.create({
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginVertical: 14 },
  metric: { flexGrow: 1, flexBasis: 175, minHeight: 105, backgroundColor: '#fff', padding: 17, borderRadius: 16, borderColor: '#E5EBE6', borderWidth: 1 },
  metricLabel: { color: '#717D74', fontSize: 12, fontWeight: '600' }, metricValue: { color: '#142039', fontSize: 19, fontWeight: '800', marginTop: 12 },
  chartCard: { backgroundColor: '#FFFFFF', padding: 20, borderRadius: 18, borderColor: '#E5EBE6', borderWidth: 1, marginBottom: 16 },
  chartHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 },
  chartCaption: { color: '#7A847D', fontSize: 12, marginTop: 3 }, chartUnit: { color: '#078343', fontWeight: '800', fontSize: 16, backgroundColor: '#E7F5EC', overflow: 'hidden', borderRadius: 10, paddingHorizontal: 11, paddingVertical: 7 },
  chartRow: { marginBottom: 16 }, chartMeta: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, marginBottom: 7 }, chartName: { color: '#142039', fontSize: 13, fontWeight: '700', flex: 1 }, chartAmount: { color: '#142039', fontSize: 12, fontWeight: '800' }, track: { height: 9, backgroundColor: '#EAF0EB', borderRadius: 9, overflow: 'hidden' }, fill: { height: '100%', backgroundColor: '#078343', borderRadius: 9 }, chartDetail: { color: '#7A847D', fontSize: 11, marginTop: 5 },
  row: { backgroundColor: '#fff', padding: 14, borderRadius: 13, borderWidth: 1, borderColor: '#E5EBE6', marginBottom: 8, flexDirection: 'row', alignItems: 'center', gap: 10 },
  name: { color: '#142039', fontWeight: '800', fontSize: 13 }, sub: { color: '#758079', fontSize: 11, marginTop: 5 }, orderAmount: { alignItems: 'flex-end' }, amountValue: { color: '#142039', fontSize: 13, fontWeight: '800' },
});
