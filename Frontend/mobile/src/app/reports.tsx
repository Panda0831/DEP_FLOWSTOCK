import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
import { api, getApiBaseUrl, getSessionCookieHeaders } from '@/lib/session-api';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

type Summary = { chiffre_affaires: string; benefice_brut: string; depenses: string; benefice_net: string; commandes_livrees: number };
type ProductReport = { idProduit__public_id: string; idProduit__nomProduit: string; quantite_vendue: number; chiffre_affaires: string; benefice_brut: string };
type OrderReport = { public_id: string; client: string; date_livraison: string; chiffre_affaires: string; benefice: string };
const EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

function localDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export default function ReportsScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
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

  return <ScrollView style={[ui.page, { backgroundColor: t.background }]} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Rapports" subtitle="Résultats calculés par le backend sur la période choisie." />
    {!admin ? <Text style={styles.error}>Les rapports financiers sont réservés aux administrateurs.</Text> : <>
      <FadeIn delay={130}><View style={styles.periodCard}>
        <View style={styles.periodHeading}><View style={styles.periodIcon}><Text style={styles.periodIconText}>⌁</Text></View><View><Text style={styles.periodTitle}>Période du rapport</Text><Text style={styles.periodCaption}>Choisissez les dates à analyser.</Text></View></View>
        <Text style={styles.fieldLabel}>Du</Text>
        <TextInput style={styles.input} value={start} onChangeText={setStart} placeholder="AAAA-MM-JJ" placeholderTextColor={t.secondaryText} />
        <Text style={styles.fieldLabel}>Au</Text>
        <TextInput style={styles.input} value={end} onChangeText={setEnd} placeholder="AAAA-MM-JJ" placeholderTextColor={t.secondaryText} />
        <Action label={loading ? 'Chargement…' : 'Afficher'} onPress={() => void load()} disabled={loading} />
      </View></FadeIn>
      {!!error && <Text style={styles.error}>{error}</Text>}
      {loading && !summary ? <ActivityIndicator color={t.tint} style={{ margin: 20 }} /> : null}
      {summary && <>
        <FadeIn delay={180}><View style={styles.grid}>{[
          ['Chiffre d’affaires', summary.chiffre_affaires], ['Bénéfice brut', summary.benefice_brut],
          ['Dépenses', summary.depenses], ['Bénéfice net', summary.benefice_net],
          ['Commandes livrées', String(summary.commandes_livrees)],
        ].map(([label, value], index) => <View key={label} style={[styles.metric, index === 3 && styles.netMetric]}>
          <Text style={styles.metricLabel}>{label}</Text>
          <Text style={styles.metricValue}>{label === 'Commandes livrées' ? value : `${Number(value).toLocaleString('fr-FR')} Ar`}</Text>
        </View>)}</View></FadeIn>
        <View style={styles.exportCard}>
          <View style={styles.exportCopy}><Text style={styles.exportTitle}>Votre rapport, prêt à partager</Text><Text style={styles.exportCaption}>Téléchargez les résultats au format Excel.</Text></View>
          <Action label={exporting ? 'Préparation…' : 'Exporter'} onPress={() => void exportExcel()} disabled={exporting} />
        </View>
        <View style={styles.chartCard}>
          <View style={styles.chartHeading}><View><Text style={styles.sectionTitle}>Ventes par produit</Text><Text style={styles.chartCaption}>Chiffre d’affaires sur la période</Text></View><Text style={styles.chartUnit}>AR</Text></View>
          {products.length === 0 ? <Text style={styles.empty}>Aucune vente sur cette période.</Text> : [...products].sort((a, b) => Number(b.chiffre_affaires) - Number(a.chiffre_affaires)).slice(0, 6).map((item, _index, rows) => {
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
          <View style={styles.chartHeading}><View><Text style={styles.sectionTitle}>Commandes livrées</Text><Text style={styles.chartCaption}>Ventes confirmées sur la période</Text></View><Text style={styles.chartUnit}>{orders.length}</Text></View>
          {orders.length === 0 ? <Text style={styles.empty}>Aucune commande livrée sur cette période.</Text> : orders.slice(0, 6).map((item) => <View key={item.public_id} style={styles.row}>
            <View style={{ flex: 1 }}><Text style={styles.name}>{item.client}</Text><Text style={styles.sub}>{item.date_livraison}</Text></View>
            <View style={styles.orderAmount}><Text style={styles.amountValue}>{Number(item.chiffre_affaires).toLocaleString('fr-FR')} Ar</Text><Text style={styles.sub}>Bénéfice {Number(item.benefice).toLocaleString('fr-FR')} Ar</Text></View>
          </View>)}</View>
      </>}
    </>}
  </ScrollView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  input: { minHeight: 48, borderWidth: 1, borderColor: t.separator, borderRadius: 12, paddingHorizontal: 14, fontSize: 16, color: t.text, marginBottom: 12, backgroundColor: t.surface },
  empty: { color: t.secondaryText, fontSize: 15, textAlign: 'center', marginVertical: 24 },
  error: { color: t.danger, fontSize: 14, lineHeight: 20, marginBottom: 12 },
  periodCard: { backgroundColor: t.surface, borderRadius: 18, padding: 20, borderColor: t.separator, borderWidth: 1, marginBottom: 14 },
  sectionTitle: { color: t.text, fontSize: 17, lineHeight: 22, fontWeight: '600' },
  periodHeading: { flexDirection: 'row', alignItems: 'center', gap: 11, marginBottom: 16 },
  periodIcon: { width: 40, height: 40, borderRadius: 13, backgroundColor: t.tintSurface, alignItems: 'center', justifyContent: 'center' },
  periodIconText: { color: t.tint, fontSize: 23, fontWeight: '700' },
  periodTitle: { color: t.text, fontSize: 16, fontWeight: '700' },
  periodCaption: { color: t.secondaryText, fontSize: 13, marginTop: 3 },
  fieldLabel: { color: t.text, fontSize: 13, fontWeight: '600', marginBottom: 6 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginVertical: 14 },
  metric: { flexGrow: 1, flexBasis: 175, minHeight: 105, backgroundColor: t.surface, padding: 17, borderRadius: 16, borderColor: t.separator, borderWidth: 1 },
  netMetric: { backgroundColor: t.tintSurface, borderColor: t.tintSurface },
  metricLabel: { color: t.secondaryText, fontSize: 13, fontWeight: '600' },
  metricValue: { color: t.text, fontSize: 19, fontWeight: '700', marginTop: 12 },
  exportCard: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: 12, backgroundColor: t.tintSurface, padding: 16, borderRadius: 16, borderWidth: 1, borderColor: t.separator, marginBottom: 16 },
  exportCopy: { flex: 1, minWidth: 170 },
  exportTitle: { color: t.text, fontSize: 14, fontWeight: '700' },
  exportCaption: { color: t.secondaryText, fontSize: 13, marginTop: 4 },
  chartCard: { backgroundColor: t.surface, padding: 20, borderRadius: 18, borderColor: t.separator, borderWidth: 1, marginBottom: 16 },
  chartHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18 },
  chartCaption: { color: t.secondaryText, fontSize: 13, marginTop: 3 },
  chartUnit: { color: t.tint, fontWeight: '700', fontSize: 14, backgroundColor: t.tintSurface, overflow: 'hidden', borderRadius: 10, paddingHorizontal: 11, paddingVertical: 7 },
  chartRow: { marginBottom: 16 },
  chartMeta: { flexDirection: 'row', justifyContent: 'space-between', gap: 12, marginBottom: 7 },
  chartName: { color: t.text, fontSize: 14, fontWeight: '600', flex: 1 },
  chartAmount: { color: t.text, fontSize: 13, fontWeight: '700' },
  track: { height: 9, backgroundColor: t.separator, borderRadius: 9, overflow: 'hidden' },
  fill: { height: '100%', backgroundColor: t.tint, borderRadius: 9 },
  chartDetail: { color: t.secondaryText, fontSize: 13, marginTop: 5 },
  row: { backgroundColor: t.surface, padding: 14, borderRadius: 13, borderWidth: 1, borderColor: t.separator, marginBottom: 8, flexDirection: 'row', alignItems: 'center', gap: 10 },
  name: { color: t.text, fontWeight: '600', fontSize: 14 },
  sub: { color: t.secondaryText, fontSize: 13, marginTop: 5 },
  orderAmount: { alignItems: 'flex-end' },
  amountValue: { color: t.text, fontSize: 13, fontWeight: '700' },
});
