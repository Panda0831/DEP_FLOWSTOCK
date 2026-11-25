import { useCallback, useEffect, useMemo, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { api, fetchAll, type Produit, type Stock } from '@/lib/session-api';
import { useAuth } from '@/lib/auth-context';
import { Action, useUiStyles } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { OptionSelect, toOptions } from '@/components/option-select';
import { QuantityField } from '@/components/quantity-field';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';
import { ScreenState } from '@/components/screen-state';

export default function NewStockMovementScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const ui = useUiStyles();
  const router = useRouter();
  const params = useLocalSearchParams<{ product?: string; returnTo?: string; client?: string }>();
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || !!user?.is_staff;
  const [products, setProducts] = useState<Produit[]>([]);
  const [currentStock, setCurrentStock] = useState<Record<string, number>>({});
  const [product, setProduct] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [productList, stockList] = await Promise.all([
        fetchAll<Produit>('/products/'),
        api.get<Stock[]>('/stock/'),
      ]);
      setProducts(productList);
      setCurrentStock(Object.fromEntries(stockList.map((item) => [item.public_id, item.stock])));
    }
    catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { if (admin) void load(); }, [admin, load]);
  useEffect(() => {
    if (typeof params.product === 'string') setProduct(params.product);
    else if (products.length === 1) setProduct(products[0].public_id);
  }, [params.product, products]);

  const adjust = async (kind: 'entries' | 'losses') => {
    const amount = Number(quantity);
    if (!product || !Number.isInteger(amount) || amount < 1) {
      setError('Sélectionnez un produit et saisissez une quantité entière supérieure à zéro.');
      return;
    }
    setBusy(true); setError('');
    try {
      await api.post(`/movements/${kind}/`, { product, quantity: amount });
      if (params.returnTo === 'order') {
        router.replace({ pathname: '/orders/new', params: { product, ...(typeof params.client === 'string' ? { client: params.client } : {}) } });
      } else {
        router.replace({ pathname: '/stock', params: { success: kind === 'entries' ? 'entry' : 'loss', product } });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Mouvement refusé.');
      setBusy(false);
    }
  };

  if (!admin) return <ScrollView style={ui.page} contentContainerStyle={ui.content} showsVerticalScrollIndicator={false}><AppPageHeading title="Mouvement de stock" subtitle="Cette section est réservée aux administrateurs." /></ScrollView>;

  const valid = !!product && Number.isInteger(Number(quantity)) && Number(quantity) > 0;

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
    <AppPageHeading title="Mouvement de stock" subtitle="Choisissez un produit, puis enregistrez une entrée ou une perte." />
    {loading ? <ScreenState type="loading" title="Chargement du catalogue…" compact /> : !!error && !products.length ? <ScreenState
      type="error"
      title="Le catalogue n’a pas pu être chargé."
      description={error}
      actionLabel="Réessayer"
      onAction={() => void load()}
    /> : !products.length ? <View style={ui.card}>
      <Text style={styles.formTitle}>Ajoutez d’abord un produit</Text>
      <Text style={styles.formHint}>Un mouvement de stock doit être associé à un produit du catalogue.</Text>
      <Action label="Ajouter un produit" onPress={() => router.push({ pathname: '/products', params: { add: '1' } })} />
    </View> : <View style={ui.card}>
      <Text style={styles.formTitle}>Quel produit voulez-vous ajuster ?</Text>
      <Text style={styles.formHint}>Choisissez un article, puis indiquez le nombre d’unités.</Text>
      <OptionSelect label="Produit" options={toOptions(products, (item) => item.nomProduit, (item) => `En stock : ${currentStock[item.public_id] ?? 0}`)} value={product} onChange={setProduct} placeholder="Choisir un produit" />
      <QuantityField value={quantity} onChange={setQuantity} hint="Nombre entier, au minimum 1." />
      <View style={styles.actions}>
        <View style={styles.actionSlot}><Action label={busy ? 'Enregistrement…' : 'Enregistrer une entrée'} onPress={() => void adjust('entries')} disabled={busy || !valid} /></View>
        <View style={styles.actionSlot}><Action label={busy ? 'Enregistrement…' : 'Enregistrer une perte'} variant="danger" onPress={() => void adjust('losses')} disabled={busy || !valid} /></View>
      </View>
      {!!error && <Text accessibilityRole="alert" style={[ui.error, styles.error]}>{error}</Text>}
    </View>}
  </ScrollView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  loader: { marginVertical: 32 },
  formTitle: { color: t.text, fontSize: 17, fontWeight: '600', marginBottom: 5 },
  formHint: { color: t.secondaryText, fontSize: 14, lineHeight: 20, marginBottom: 18 },
  actions: { gap: 10, marginTop: 4 },
  actionSlot: { width: '100%' },
  error: { marginTop: 12 },
});
