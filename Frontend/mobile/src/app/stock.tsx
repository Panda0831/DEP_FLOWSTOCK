import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { api, type Movement, type Page, type Produit, type Stock } from '@/lib/session-api';
import { useAuth } from '@/lib/auth-context';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
}

export default function StockScreen() {
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  const [items, setItems] = useState<Stock[]>([]);
  const [moves, setMoves] = useState<Movement[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [product, setProduct] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [stock, movementResult, productResult] = await Promise.all([
        api.get<Stock[]>('/stock/'),
        api.get<Page<Movement> | Movement[]>('/movements/'),
        api.get<Page<Produit> | Produit[]>('/products/'),
      ]);
      setItems(stock);
      setMoves(Array.isArray(movementResult) ? movementResult : movementResult.results);
      setProducts(Array.isArray(productResult) ? productResult : productResult.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const lowStockItems = useMemo(() => items.filter((item) => item.stock <= item.seuilAlerte), [items]);
  const totalUnits = useMemo(() => items.reduce((sum, item) => sum + item.stock, 0), [items]);

  const adjust = async (kind: 'entries' | 'losses') => {
    const amount = Number(quantity);
    if (!product || !Number.isInteger(amount) || amount < 1) {
      setError('Sélectionnez un produit et saisissez une quantité entière supérieure à zéro.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await api.post(`/movements/${kind}/`, { product, quantity: amount });
      setQuantity('1');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mouvement refusé.');
    } finally {
      setBusy(false);
    }
  };

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Stock" subtitle="Niveaux disponibles, alertes et journal des mouvements" />

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

    {admin && <FadeIn delay={130}>
      <View style={ui.card}>
        <Text style={ui.cardTitle}>Enregistrer un mouvement</Text>
        <Text style={styles.label}>Choisir un produit</Text>
        {products.length === 0 ? <Text style={styles.helper}>Aucun produit disponible.</Text> : <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.productChoices}>
          {products.map((item) => <MotionPressable key={item.public_id} onPress={() => setProduct(item.public_id)} style={[styles.productChoice, product === item.public_id && styles.productSelected]}>
            <Text style={[styles.productText, product === item.public_id && styles.productTextSelected]}>{item.nomProduit}</Text>
          </MotionPressable>)}
        </ScrollView>}
        <TextInput value={quantity} onChangeText={setQuantity} keyboardType="number-pad" placeholder="Quantité" placeholderTextColor="#89919E" style={ui.input} />
        <View style={styles.actions}>
          <Action label={busy ? 'Enregistrement…' : 'Entrée de stock'} onPress={() => void adjust('entries')} disabled={busy || !products.length} />
          <MotionPressable style={[styles.lossButton, busy && styles.disabled]} onPress={() => void adjust('losses')} disabled={busy || !products.length}>
            <Text style={styles.lossText}>Enregistrer une perte</Text>
          </MotionPressable>
        </View>
      </View>
    </FadeIn>}

    {!!error && <Text accessibilityRole="alert" style={ui.error}>{error}</Text>}

    <View style={styles.sectionHeading}>
      <View><Text style={ui.section}>État du stock</Text><Text style={styles.sectionHint}>Les références sous le seuil sont signalées en rouge.</Text></View>
      <Pressable onPress={() => void load()} accessibilityRole="button" accessibilityLabel="Actualiser le stock"><Text style={ui.refresh}>Actualiser</Text></Pressable>
    </View>
    {loading ? <ActivityIndicator color="#078343" style={styles.loader} /> : items.length === 0 ? <Text style={ui.empty}>Aucun niveau de stock à afficher.</Text> : items.map((item, index) => {
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

    <View style={[styles.sectionHeading, styles.historyHeading]}>
      <View><Text style={ui.section}>Historique récent</Text><Text style={styles.sectionHint}>Les derniers mouvements de stock enregistrés.</Text></View>
      <Pressable onPress={() => void load()} accessibilityRole="button" accessibilityLabel="Actualiser l’historique"><Text style={ui.refresh}>Actualiser</Text></Pressable>
    </View>
    {loading ? <ActivityIndicator color="#078343" style={styles.loader} /> : moves.length === 0 ? <Text style={ui.empty}>Aucun mouvement enregistré.</Text> : moves.slice(0, 30).map((move) => {
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
  </ScrollView>;
}

const styles = StyleSheet.create({
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 22 },
  summaryCard: { flexGrow: 1, flexBasis: 145, minHeight: 108, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E5EBE6', borderRadius: 16, padding: 15 },
  alertSummaryCard: { borderColor: '#F0CACA', backgroundColor: '#FFFAFA' },
  summaryLabel: { color: '#718077', fontSize: 11, fontWeight: '700' },
  summaryValue: { color: '#173D2B', fontSize: 24, fontWeight: '800', marginTop: 8 },
  alertValue: { color: '#B63838' },
  summaryHint: { color: '#89928C', fontSize: 10, marginTop: 3 },
  label: { fontSize: 13, color: '#68736B', marginBottom: 8 },
  productChoices: { gap: 7, paddingBottom: 10 },
  productChoice: { backgroundColor: '#F0F4F1', paddingVertical: 10, paddingHorizontal: 12, borderRadius: 10 },
  productSelected: { backgroundColor: '#078343' },
  productText: { color: '#38443B', fontSize: 12, fontWeight: '700' },
  productTextSelected: { color: '#FFFFFF' },
  helper: { color: '#818A83', fontSize: 12, marginBottom: 12 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 9 },
  lossButton: { borderColor: '#DDAAAA', borderWidth: 1, borderRadius: 12, justifyContent: 'center', paddingHorizontal: 13, minHeight: 44 },
  lossText: { color: '#A63838', fontWeight: '700', fontSize: 12 },
  disabled: { opacity: 0.55 },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 12 },
  sectionHint: { color: '#818A83', fontSize: 11, marginTop: 3 },
  loader: { marginVertical: 24 },
  stockRow: { backgroundColor: '#FFFFFF', borderRadius: 14, padding: 15, marginBottom: 8, flexDirection: 'row', alignItems: 'center', borderColor: '#DDE9DF', borderWidth: 1, gap: 10, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 6, elevation: 1 },
  stockInfo: { flex: 1 },
  productName: { color: '#173D2B', fontWeight: '700', fontSize: 14 },
  threshold: { color: '#818A83', fontSize: 11, marginTop: 4 },
  stockValueWrap: { alignItems: 'flex-end', minWidth: 94 },
  stockValue: { color: '#078343', fontWeight: '800', fontSize: 22 },
  lowValue: { color: '#B63838' },
  stockStatus: { color: '#078343', fontWeight: '700', fontSize: 9, marginTop: 1 },
  lowStatus: { color: '#B63838' },
  historyHeading: { marginTop: 20 },
  movementRow: { backgroundColor: '#FFFFFF', borderRadius: 14, padding: 13, marginBottom: 8, flexDirection: 'row', alignItems: 'center', gap: 11, borderColor: '#DDE9DF', borderWidth: 1, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 6, elevation: 1 },
  movementIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  entryIcon: { backgroundColor: '#E7F5EC' },
  lossIcon: { backgroundColor: '#FCEEEE' },
  movementSign: { fontSize: 20, fontWeight: '700' },
  entrySign: { color: '#078343' },
  lossSign: { color: '#B63838' },
  movementInfo: { flex: 1 },
  movementName: { color: '#173D2B', fontSize: 13, fontWeight: '700' },
  movementDate: { color: '#818A83', fontSize: 10, marginTop: 4 },
  movementAmountWrap: { alignItems: 'flex-end' },
  movementAmount: { color: '#078343', fontWeight: '800', fontSize: 15 },
  movementKind: { color: '#818A83', fontSize: 10, marginTop: 2 },
});
