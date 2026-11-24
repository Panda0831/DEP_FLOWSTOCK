import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api, fetchAll, type Movement, type Produit, type Stock } from '@/lib/session-api';
import { useAuth } from '@/lib/auth-context';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn } from '@/components/motion';
import { LIST_PAGE_SIZE, ShowMore } from '@/components/show-more';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

const MOVEMENTS_PER_PAGE = 15;
type MovementFilter = 'all' | 'entries' | 'losses';

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
}

export default function StockScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ product?: string; success?: string }>();
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  const [items, setItems] = useState<Stock[]>([]);
  const [stockLimit, setStockLimit] = useState(LIST_PAGE_SIZE);
  const [moves, setMoves] = useState<Movement[]>([]);
  const [movePage, setMovePage] = useState(1);
  const [movementQuery, setMovementQuery] = useState('');
  const [movementFilter, setMovementFilter] = useState<MovementFilter>('all');
  const [products, setProducts] = useState<Produit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [stock, movementList, productList] = await Promise.all([
        api.get<Stock[]>('/stock/'),
        fetchAll<Movement>('/movements/'),
        fetchAll<Produit>('/products/'),
      ]);
      setItems(stock);
      setMoves(movementList);
      setProducts(productList);
      setStockLimit(LIST_PAGE_SIZE);
      setMovePage(1);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const lowStockItems = useMemo(() => items.filter((item) => item.stock <= item.seuilAlerte), [items]);
  const totalUnits = useMemo(() => items.reduce((sum, item) => sum + item.stock, 0), [items]);
  const orderedItems = useMemo(() => {
    if (typeof params.product !== 'string') return items;
    return [...items].sort((a, b) => Number(b.public_id === params.product) - Number(a.public_id === params.product));
  }, [items, params.product]);
  const focusedProduct = items.find((item) => item.public_id === params.product);
  const filteredMoves = useMemo(() => {
    const needle = movementQuery.trim().toLocaleLowerCase('fr-FR');
    return moves.filter((move) => {
      const isEntry = move.typeMouvement === 'entree';
      if (movementFilter === 'entries' && !isEntry) return false;
      if (movementFilter === 'losses' && isEntry) return false;
      if (!needle) return true;
      const productName = products.find((item) => item.public_id === move.produit)?.nomProduit || '';
      const haystack = [productName, move.motif, move.referenceOperation, formatDate(move.date), String(move.quantite), isEntry ? 'entrée entree' : 'perte sortie'].join(' ').toLocaleLowerCase('fr-FR');
      return haystack.includes(needle);
    });
  }, [moves, movementFilter, movementQuery, products]);
  const movePageCount = Math.max(1, Math.ceil(filteredMoves.length / MOVEMENTS_PER_PAGE));
  const currentMovePage = Math.min(movePage, movePageCount);
  const visibleMoves = filteredMoves.slice((currentMovePage - 1) * MOVEMENTS_PER_PAGE, currentMovePage * MOVEMENTS_PER_PAGE);
  return <ScrollView style={[ui.page, { backgroundColor: t.background }]} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Stock" subtitle="Niveaux disponibles, alertes et journal des mouvements" />
    {params.success && <View style={[styles.notice, params.success === 'loss' && styles.lossNotice]} accessibilityRole="summary">
      <Text style={styles.noticeText}>{params.success === 'loss' ? 'Perte enregistrée.' : 'Entrée de stock enregistrée.'}{focusedProduct ? ` ${focusedProduct.nomProduit} : ${focusedProduct.stock} unité(s) disponible(s).` : ''}</Text>
    </View>}

    <FadeIn delay={100}>
      <View style={styles.summaryGrid}>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Références suivies</Text>
          <Text style={styles.summaryValue}>{loading ? '—' : items.length}</Text>
          <Text style={styles.summaryHint}>Produits en stock</Text>
        </View>
        <View style={styles.summaryCard}>
          <Text style={styles.summaryLabel}>Unités disponibles</Text>
          <Text style={styles.summaryValue}>{loading ? '—' : totalUnits.toLocaleString('fr-FR')}</Text>
          <Text style={styles.summaryHint}>Toutes références confondues</Text>
        </View>
        <View style={[styles.summaryCard, lowStockItems.length > 0 && styles.alertSummaryCard]}>
          <Text style={styles.summaryLabel}>À réapprovisionner</Text>
          <Text style={[styles.summaryValue, lowStockItems.length > 0 && styles.alertValue]}>{loading ? '—' : lowStockItems.length}</Text>
          <Text style={styles.summaryHint}>Au seuil d’alerte ou en dessous</Text>
        </View>
      </View>
    </FadeIn>

    {admin && <View style={styles.createRow}><Action label="Nouveau mouvement" onPress={() => router.push('/stock/new')} /></View>}

    {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}

    <View style={styles.sectionHeading}>
      <View><Text style={styles.sectionTitle}>État du stock</Text><Text style={styles.sectionHint}>Les références sous le seuil sont signalées avec une alerte.</Text></View>
      <Pressable onPress={() => void load()} accessibilityRole="button" accessibilityLabel="Actualiser le stock"><Text style={styles.refresh}>Actualiser</Text></Pressable>
    </View>
    {loading ? <ActivityIndicator color={t.tint} style={styles.loader} /> : items.length === 0 ? <Text style={styles.empty}>Aucun niveau de stock à afficher.</Text> : orderedItems.slice(0, stockLimit).map((item, index) => {
      const isLow = item.stock <= item.seuilAlerte;
      return <FadeIn key={item.public_id} delay={Math.min(index * 35, 280)}>
        <View style={styles.stockRow}>
          <View style={styles.stockInfo}>
            <Text style={styles.productName}>{item.nomProduit}</Text>
            <Text style={styles.threshold}>Seuil d’alerte : {item.seuilAlerte}</Text>
          </View>
          <View style={styles.stockValueWrap}>
            <Text style={[styles.stockValue, isLow && styles.lowValue]}>{item.stock}</Text>
            <Text style={[styles.stockStatus, isLow && styles.lowStatus]}>{isLow ? 'À réapprovisionner' : 'Disponible'}</Text>
          </View>
        </View>
      </FadeIn>;
    })}
    {!loading && <ShowMore remaining={items.length - stockLimit} onPress={() => setStockLimit((current) => current + LIST_PAGE_SIZE)} />}

    <View style={[styles.sectionHeading, styles.historyHeading]}>
      <View><Text style={styles.sectionTitle}>Historique récent</Text><Text style={styles.sectionHint}>Les derniers mouvements de stock enregistrés.</Text></View>
      <Pressable onPress={() => void load()} accessibilityRole="button" accessibilityLabel="Actualiser l’historique"><Text style={styles.refresh}>Actualiser</Text></Pressable>
    </View>
    <TextInput
      value={movementQuery}
      onChangeText={(value) => { setMovementQuery(value); setMovePage(1); }}
      placeholder="Rechercher un produit, une date…"
      placeholderTextColor={t.secondaryText}
      style={styles.searchInput}
      accessibilityLabel="Rechercher dans l’historique des mouvements"
      returnKeyType="search"
      clearButtonMode="while-editing"
    />
    <View style={styles.filterRow}>
      {([
        ['all', 'Tous'], ['entries', 'Entrées'], ['losses', 'Pertes'],
      ] as const).map(([value, label]) => <Pressable
        key={value}
        onPress={() => { setMovementFilter(value); setMovePage(1); }}
        style={[styles.filterButton, movementFilter === value && styles.filterButtonActive]}
        accessibilityRole="tab"
        accessibilityState={{ selected: movementFilter === value }}>
        <Text style={[styles.filterText, movementFilter === value && styles.filterTextActive]}>{label}</Text>
      </Pressable>)}
    </View>
    {loading ? <ActivityIndicator color={t.tint} style={styles.loader} /> : moves.length === 0 ? <Text style={styles.empty}>Aucun mouvement enregistré.</Text> : filteredMoves.length === 0 ? <Text style={styles.empty}>Aucun mouvement ne correspond à ces critères.</Text> : visibleMoves.map((move) => {
      const isEntry = move.typeMouvement === 'entree';
      const productName = products.find((item) => item.public_id === move.produit)?.nomProduit || `Produit ${move.produit.slice(0, 8)}`;
      return <View key={move.public_id} style={styles.movementRow}>
        <View style={[styles.movementIcon, isEntry ? styles.entryIcon : styles.lossIcon]}><Text style={[styles.movementSign, isEntry ? styles.entrySign : styles.lossSign]}>{isEntry ? '+' : '−'}</Text></View>
        <View style={styles.movementInfo}>
          <Text style={styles.movementName}>{productName}</Text>
          <Text style={styles.movementDate}>{formatDate(move.date)}</Text>
        </View>
        <View style={styles.movementAmountWrap}>
          <Text style={[styles.movementAmount, !isEntry && styles.lowValue]}>{isEntry ? '+' : '−'}{move.quantite}</Text>
          <Text style={styles.movementKind}>{isEntry ? 'Entrée' : 'Perte'}</Text>
        </View>
      </View>;
    })}
    {!loading && filteredMoves.length > 0 && <View style={styles.pagination}>
      <Pressable onPress={() => setMovePage((page) => Math.max(1, page - 1))} disabled={currentMovePage <= 1} style={[styles.pageButton, currentMovePage <= 1 && styles.pageButtonDisabled]} accessibilityRole="button" accessibilityLabel="Page précédente">
        <Text style={styles.pageButtonText}>‹ Précédent</Text>
      </Pressable>
      <Text style={styles.pageIndicator}>Page {currentMovePage} sur {movePageCount}</Text>
      <Pressable onPress={() => setMovePage((page) => Math.min(movePageCount, page + 1))} disabled={currentMovePage >= movePageCount} style={[styles.pageButton, currentMovePage >= movePageCount && styles.pageButtonDisabled]} accessibilityRole="button" accessibilityLabel="Page suivante">
        <Text style={styles.pageButtonText}>Suivant ›</Text>
      </Pressable>
    </View>}
  </ScrollView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 22 },
  summaryCard: { flexGrow: 1, flexBasis: 145, minHeight: 108, backgroundColor: t.surface, borderWidth: 1, borderColor: t.separator, borderRadius: 16, padding: 15 },
  alertSummaryCard: { borderColor: t.warningSurface, backgroundColor: t.warningSurface },
  summaryLabel: { color: t.secondaryText, fontSize: 12, fontWeight: '600' },
  summaryValue: { color: t.text, fontSize: 24, fontWeight: '700', marginTop: 8 },
  alertValue: { color: t.warning },
  summaryHint: { color: t.secondaryText, fontSize: 13, marginTop: 3 },
  createRow: { marginBottom: 18 },
  notice: { padding: 14, borderRadius: 12, backgroundColor: t.tintSurface, marginBottom: 16 },
  lossNotice: { backgroundColor: t.dangerSurface },
  noticeText: { color: t.text, fontSize: 14, lineHeight: 20, fontWeight: '600' },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 12 },
  sectionTitle: { color: t.text, fontSize: 17, lineHeight: 22, fontWeight: '600' },
  sectionHint: { color: t.secondaryText, fontSize: 13, marginTop: 3 },
  empty: { color: t.secondaryText, fontSize: 15, textAlign: 'center', marginVertical: 32 },
  error: { color: t.danger, fontSize: 14, lineHeight: 20, marginBottom: 12 },
  refresh: { color: t.tint, fontSize: 14, fontWeight: '600', minHeight: 44, textAlignVertical: 'center' },
  loader: { marginVertical: 24 },
  stockRow: { backgroundColor: t.surface, borderRadius: 14, padding: 15, marginBottom: 8, flexDirection: 'row', alignItems: 'center', borderColor: t.separator, borderWidth: 1, gap: 10 },
  stockInfo: { flex: 1 },
  productName: { color: t.text, fontWeight: '600', fontSize: 15 },
  threshold: { color: t.secondaryText, fontSize: 13, marginTop: 4 },
  stockValueWrap: { alignItems: 'flex-end', minWidth: 94 },
  stockValue: { color: t.tint, fontWeight: '700', fontSize: 22 },
  lowValue: { color: t.danger },
  stockStatus: { color: t.tint, fontWeight: '600', fontSize: 13, marginTop: 1 },
  lowStatus: { color: t.danger },
  historyHeading: { marginTop: 20 },
  searchInput: { minHeight: 48, borderWidth: 1, borderColor: t.separator, borderRadius: 12, paddingHorizontal: 14, fontSize: 15, color: t.text, backgroundColor: t.surface, marginBottom: 8 },
  filterRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  filterButton: { minHeight: 40, minWidth: 74, justifyContent: 'center', alignItems: 'center', paddingHorizontal: 13, borderWidth: 1, borderColor: t.separator, borderRadius: 20, backgroundColor: t.surface },
  filterButtonActive: { borderColor: t.tint, backgroundColor: t.tintSurface },
  filterText: { color: t.secondaryText, fontSize: 13, fontWeight: '600' },
  filterTextActive: { color: t.tint },
  pagination: { minHeight: 52, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 4, marginBottom: 16 },
  pageButton: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 12, borderWidth: 1, borderColor: t.separator, borderRadius: 11, backgroundColor: t.surface },
  pageButtonDisabled: { opacity: 0.45 },
  pageButtonText: { color: t.tint, fontSize: 13, fontWeight: '600' },
  pageIndicator: { color: t.secondaryText, fontSize: 13, fontWeight: '600' },
  movementRow: { backgroundColor: t.surface, borderRadius: 14, padding: 13, marginBottom: 8, flexDirection: 'row', alignItems: 'center', gap: 11, borderColor: t.separator, borderWidth: 1 },
  movementIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  entryIcon: { backgroundColor: t.tintSurface },
  lossIcon: { backgroundColor: t.dangerSurface },
  movementSign: { fontSize: 20, fontWeight: '700' },
  entrySign: { color: t.tint },
  lossSign: { color: t.danger },
  movementInfo: { flex: 1 },
  movementName: { color: t.text, fontSize: 15, fontWeight: '600' },
  movementDate: { color: t.secondaryText, fontSize: 13, marginTop: 4 },
  movementAmountWrap: { alignItems: 'flex-end' },
  movementAmount: { color: t.tint, fontWeight: '700', fontSize: 15 },
  movementKind: { color: t.secondaryText, fontSize: 13, marginTop: 2 },
});
