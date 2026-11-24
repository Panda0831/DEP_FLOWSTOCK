import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Linking, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { File, Paths } from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { Action, useUiStyles } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
import { api, getApiBaseUrl, getSessionCookieHeaders } from '@/lib/session-api';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';
import { LIST_PAGE_SIZE, PageNavigation } from '@/components/list-pagination';

type Summary = {
  chiffre_affaires: string;
  ventes_produits: string;
  remises: string;
  frais_livraison_factures: string;
  cout_produits: string;
  cout_livraisons: string;
  benefice_brut: string;
  depenses: string;
  benefice_net: string;
  commandes_livrees: number;
};
type ProductReport = { idProduit__public_id: string; idProduit__nomProduit: string; quantite_vendue: number; chiffre_affaires: string; benefice_brut: string };
type OrderReport = { public_id: string; client: string; date_livraison: string; chiffre_affaires: string; benefice: string };
const EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

function localDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export default function ReportsScreen() {
  const ui = useUiStyles();
  const router = useRouter();
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
  const [productPage, setProductPage] = useState(1);
  const [orderPage, setOrderPage] = useState(1);
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
      setProductPage(1); setOrderPage(1);
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

  const net = Number(summary?.benefice_net ?? 0);
  const ventesAvantLivraison = summary
    ? Number(summary.ventes_produits) - Number(summary.remises) - Number(summary.cout_produits)
      + Number(summary.frais_livraison_factures)
    : 0;
  const livraisonExpliqueLaPerte = !!summary && net < 0
    && Number(summary.cout_livraisons) > ventesAvantLivraison;
  const details = summary ? [
    ['Ventes de produits', Number(summary.ventes_produits)],
    ['Remises accordées', -Number(summary.remises)],
    ['Livraison facturée au client', Number(summary.frais_livraison_factures)],
    ['Coût des produits vendus', -Number(summary.cout_produits)],
    ['Coût des livraisons', -Number(summary.cout_livraisons)],
    ['Autres dépenses', -Number(summary.depenses)],
  ] as const : [];
  const sortedProducts = [...products].sort((a, b) => Number(b.chiffre_affaires) - Number(a.chiffre_affaires));
  const maxProductSales = Math.max(...products.map((row) => Number(row.chiffre_affaires)), 1);

  return <ScrollView style={[ui.page, { backgroundColor: t.background }]} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Rapports" subtitle="Voyez ce que les ventes rapportent et ce qui réduit le résultat." />
    {!admin ? <Text style={styles.error}>Les rapports financiers sont réservés aux administrateurs.</Text> : <>
      <FadeIn delay={130}><View style={styles.periodCard}>
        <View style={styles.periodHeading}><View style={styles.periodIcon}><Text style={styles.periodIconText}>⌁</Text></View><View><Text style={styles.periodTitle}>Période du rapport</Text><Text style={styles.periodCaption}>Choisissez les dates à analyser.</Text></View></View>
        <Text style={styles.fieldLabel}>Du</Text>
        <TextInput style={styles.input} value={start} onChangeText={setStart} placeholder="AAAA-MM-JJ" placeholderTextColor={t.secondaryText} />
        <Text style={styles.fieldLabel}>Au</Text>
        <TextInput style={styles.input} value={end} onChangeText={setEnd} placeholder="AAAA-MM-JJ" placeholderTextColor={t.secondaryText} />
        <Action label={loading ? 'Chargement…' : 'Mettre à jour le rapport'} onPress={() => void load()} disabled={loading} />
      </View></FadeIn>
      {!!error && <Text style={styles.error}>{error}</Text>}
      {loading && !summary ? <ActivityIndicator color={t.tint} style={{ margin: 20 }} /> : null}
      {summary && <>
        <FadeIn delay={180}><View style={styles.grid}>{[
          ['Ventes', summary.chiffre_affaires], ['Reste après produits et livraison', summary.benefice_brut],
          ['Dépenses', summary.depenses], [net < 0 ? 'Résultat négatif' : 'Résultat', summary.benefice_net],
          ['Livraisons faites', String(summary.commandes_livrees)],
        ].map(([label, value], index) => <View key={label} style={[styles.metric, index === 3 && styles.netMetric, index === 3 && net < 0 && styles.negativeMetric]}>
          <Text style={styles.metricLabel}>{label}</Text>
          <Text style={[styles.metricValue, index === 3 && net < 0 && styles.negativeValue]}>{index === 4 ? value : `${Number(value).toLocaleString('fr-FR')} Ar`}</Text>
        </View>)}</View></FadeIn>
        <View style={styles.breakdownCard}>
          <Text style={styles.sectionTitle}>D’où vient ce résultat ?</Text>
          <Text style={styles.breakdownCaption}>Les montants qui augmentent ou réduisent vos ventes.</Text>
          {details.map(([label, value]) => <View key={label} style={styles.breakdownRow}>
            <Text style={styles.breakdownLabel}>{label}</Text>
            <Text style={[styles.breakdownValue, value < 0 && styles.deductionValue]}>{value < 0 ? '−' : ''}{Math.abs(value).toLocaleString('fr-FR')} Ar</Text>
          </View>)}
          <View style={styles.breakdownTotal}>
            <Text style={styles.breakdownTotalLabel}>{net < 0 ? 'Il manque' : 'Il reste'}</Text>
            <Text style={[styles.breakdownTotalValue, net < 0 && styles.negativeValue]}>{Math.abs(net).toLocaleString('fr-FR')} Ar</Text>
          </View>
        </View>
        {net < 0 && <View style={styles.lossMessage} accessibilityRole="summary">
          <Text style={styles.lossTitle}>Les coûts dépassent les ventes de {Math.abs(net).toLocaleString('fr-FR')} Ar.</Text>
          <Text style={styles.lossCopy}>{livraisonExpliqueLaPerte
            ? `Les livraisons coûtent ${Number(summary.cout_livraisons).toLocaleString('fr-FR')} Ar. Les ventes laissent ${ventesAvantLivraison.toLocaleString('fr-FR')} Ar avant ces frais. Vérifiez les coûts de livraison saisis.`
            : 'Vérifiez les coûts des produits et les dépenses affichés ci-dessus.'}</Text>
        </View>}
        <View style={styles.exportCard}>
          <View style={styles.exportCopy}><Text style={styles.exportTitle}>Enregistrer ou envoyer le rapport</Text><Text style={styles.exportCaption}>Télécharger le fichier Excel pour le partager.</Text></View>
          <Action label={exporting ? 'Préparation…' : 'Télécharger le fichier Excel'} onPress={() => void exportExcel()} disabled={exporting} />
        </View>
        <View style={styles.chartCard}>
          <View style={styles.chartHeading}><View><Text style={styles.sectionTitle}>Ventes par produit</Text><Text style={styles.chartCaption}>Montant des produits vendus</Text></View><Text style={styles.chartUnit}>AR</Text></View>
          {products.length === 0 ? <Text style={styles.empty}>Aucune vente sur cette période.</Text> : sortedProducts.slice((productPage - 1) * LIST_PAGE_SIZE, productPage * LIST_PAGE_SIZE).map((item) => {
            const share = Math.max(5, Number(item.chiffre_affaires) / maxProductSales * 100);
            return <MotionPressable key={item.idProduit__public_id} style={styles.chartRow} onPress={() => router.push({ pathname: '/products', params: { focus: item.idProduit__public_id, open: '1' } })} accessibilityRole="link" accessibilityLabel={`Gérer le produit ${item.idProduit__nomProduit}`}>
              <View style={styles.chartMeta}><Text style={styles.chartName} numberOfLines={1}>{item.idProduit__nomProduit}</Text><Text style={styles.chartAmount}>{Number(item.chiffre_affaires).toLocaleString('fr-FR')} Ar</Text></View>
              <View style={styles.track}><View style={[styles.fill, { width: `${share}%` }]} /></View>
              <Text style={styles.chartDetail}>{item.quantite_vendue} vendu(s) · reste après achat : {Number(item.benefice_brut).toLocaleString('fr-FR')} Ar</Text>
            </MotionPressable>;
          })}
          <PageNavigation page={productPage} totalItems={products.length} onPageChange={setProductPage} />
        </View>
        <View style={styles.chartCard}>
          <View style={styles.chartHeading}><View><Text style={styles.sectionTitle}>Commandes livrées</Text><Text style={styles.chartCaption}>Ventes terminées sur la période</Text></View><Text style={styles.chartUnit}>{orders.length}</Text></View>
          {orders.length === 0 ? <Text style={styles.empty}>Aucune commande livrée sur cette période.</Text> : orders.slice((orderPage - 1) * LIST_PAGE_SIZE, orderPage * LIST_PAGE_SIZE).map((item) => <MotionPressable key={item.public_id} style={styles.row} onPress={() => router.push({ pathname: '/orders/[id]', params: { id: item.public_id } })} accessibilityRole="link" accessibilityLabel={`Gérer la commande de ${item.client}`}>
            <View style={{ flex: 1 }}><Text style={styles.name}>{item.client}</Text><Text style={styles.sub}>{item.date_livraison}</Text></View>
            <View style={styles.orderAmount}><Text style={styles.amountValue}>{Number(item.chiffre_affaires).toLocaleString('fr-FR')} Ar</Text><Text style={styles.sub}>Reste sur la commande : {Number(item.benefice).toLocaleString('fr-FR')} Ar</Text></View>
          </MotionPressable>)}
          <PageNavigation page={orderPage} totalItems={orders.length} onPageChange={setOrderPage} />
        </View>
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
  negativeMetric: { backgroundColor: t.dangerSurface, borderColor: t.dangerSurface },
  negativeValue: { color: t.danger },
  breakdownCard: { backgroundColor: t.surface, padding: 20, borderRadius: 18, borderColor: t.separator, borderWidth: 1, marginBottom: 14 },
  breakdownCaption: { color: t.secondaryText, fontSize: 14, marginTop: 4, marginBottom: 12 },
  breakdownRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, paddingVertical: 9, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: t.separator },
  breakdownLabel: { color: t.text, fontSize: 14, flex: 1 },
  breakdownValue: { color: t.text, fontSize: 14, fontWeight: '600' },
  deductionValue: { color: t.secondaryText },
  breakdownTotal: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 14, marginTop: 4 },
  breakdownTotalLabel: { color: t.text, fontSize: 16, fontWeight: '700' },
  breakdownTotalValue: { color: t.tint, fontSize: 18, fontWeight: '700' },
  lossMessage: { backgroundColor: t.dangerSurface, borderRadius: 16, padding: 16, marginBottom: 16 },
  lossTitle: { color: t.danger, fontSize: 16, lineHeight: 22, fontWeight: '700' },
  lossCopy: { color: t.text, fontSize: 14, lineHeight: 20, marginTop: 6 },
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
