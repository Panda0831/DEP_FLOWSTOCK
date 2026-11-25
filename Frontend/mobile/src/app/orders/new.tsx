import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { api, fetchAll, type Client, type Commande, type Produit } from '@/lib/session-api';
import { useAuth } from '@/lib/auth-context';
import { Action, useUiStyles } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { MotionPressable } from '@/components/motion';
import { OptionSelect, toOptions } from '@/components/option-select';
import { QuantityField } from '@/components/quantity-field';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

type DraftLine = { product: string; quantity: string };

export default function NewOrderScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const ui = useUiStyles();
  const router = useRouter();
  const params = useLocalSearchParams<{ client?: string; product?: string }>();
  const { user } = useAuth();
  const canManageProducts = user?.role === 'ADMIN' || !!user?.is_staff;
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [client, setClient] = useState('');
  const [product, setProduct] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [discount, setDiscount] = useState('0');
  const [deliveryFee, setDeliveryFee] = useState('0');
  const [extraOpen, setExtraOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [clientList, productList] = await Promise.all([
        fetchAll<Client>('/clients/'),
        fetchAll<Produit>('/products/', { active: true }),
      ]);
      setClients(clientList);
      setProducts(productList);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    if (typeof params.client === 'string') setClient(params.client);
    else if (clients.length === 1) setClient(clients[0].public_id);
    if (typeof params.product === 'string') setProduct(params.product);
    else if (products.length === 1) setProduct(products[0].public_id);
  }, [clients, params.client, params.product, products]);

  const addLine = () => {
    if (!product || Number(quantity) < 1) { setError('Choisissez un produit et une quantité valide.'); return; }
    if (lines.some((line) => line.product === product)) { setError('Ce produit est déjà dans la commande.'); return; }
    setLines((current) => [...current, { product, quantity }]);
    setProduct(''); setQuantity('1'); setError('');
  };

  const create = async () => {
    if (!client || !lines.length) { setError('Choisissez un client et ajoutez au moins un produit.'); return; }
    setBusy(true); setError('');
    try {
      const created = await api.post<Commande>('/orders/', {
        client,
        items: lines.map((line) => ({ product: line.product, quantity: Number(line.quantity) })),
        remise: Number(discount),
        fraisLivraison: Number(deliveryFee),
      });
      router.replace({ pathname: '/orders', params: { focus: created.public_id, step: 'confirm' } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Création impossible.');
      setBusy(false);
    }
  };

  const subtotal = lines.reduce((sum, line) => sum + Number(line.quantity) * Number(products.find((item) => item.public_id === line.product)?.prixVente || 0), 0);
  const total = Math.max(0, subtotal - Number(discount || 0)) + Number(deliveryFee || 0);

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
    <AppPageHeading title="Nouvelle commande" subtitle="Choisissez un client, puis ajoutez les articles à vendre." />
    {loading ? <ActivityIndicator color={t.tint} style={styles.loader} /> : <View style={ui.card}>
      <Text style={styles.sectionTitle}>1. Client</Text>
      <OptionSelect label="Client" options={toOptions(clients, (item) => item.nomClient, (item) => item.contact)} value={client} onChange={setClient} placeholder="Choisir un client" />
      {!clients.length && <MotionPressable onPress={() => router.push({ pathname: '/clients', params: { flow: 'order' } })} accessibilityRole="link"><Text style={styles.helper}>Ajouter un client ›</Text></MotionPressable>}
      <Text style={styles.sectionTitle}>2. Articles</Text>
      {!products.length && canManageProducts && <MotionPressable onPress={() => router.push({ pathname: '/products', params: { add: '1', flow: 'order', client } })} accessibilityRole="link"><Text style={styles.helper}>Ajouter un produit et son stock ›</Text></MotionPressable>}
      {!products.length && !canManageProducts && <Text style={styles.helper}>Aucun produit actif. Demandez à un administrateur d’en ajouter au catalogue.</Text>}
      <OptionSelect label="Produit" options={toOptions(products, (item) => item.nomProduit, (item) => `${item.prixVente} Ar`)} value={product} onChange={setProduct} placeholder="Choisir un produit" />
      <QuantityField value={quantity} onChange={setQuantity} />
      <Action label="Ajouter cet article" variant="secondary" onPress={addLine} disabled={!product || !(Number(quantity) >= 1)} />
      {!!lines.length && <View style={styles.lines}>
        {lines.map((line) => <View style={styles.draftLine} key={line.product}>
          <View style={styles.lineCopy}><Text style={styles.lineName}>{products.find((item) => item.public_id === line.product)?.nomProduit}</Text><Text style={styles.lineDetail}>{line.quantity} × {Number(products.find((item) => item.public_id === line.product)?.prixVente || 0).toLocaleString('fr-FR')} Ar</Text></View>
          <MotionPressable onPress={() => setLines((current) => current.filter((item) => item.product !== line.product))} style={styles.removeButton} accessibilityRole="button" accessibilityLabel={`Retirer ${products.find((item) => item.public_id === line.product)?.nomProduit}`}><Text style={styles.remove}>Retirer</Text></MotionPressable>
        </View>)}
      </View>}
      <MotionPressable onPress={() => setExtraOpen((current) => !current)} style={styles.optionalToggle} accessibilityRole="button" accessibilityState={{ expanded: extraOpen }}>
        <Text style={styles.optionalText}>{extraOpen ? 'Masquer remise et livraison' : 'Ajouter une remise ou des frais'}</Text>
      </MotionPressable>
      {extraOpen && <View style={styles.extraFields}>
        <Text style={styles.fieldLabel}>Remise (Ar)</Text>
        <TextInput style={ui.input} value={discount} onChangeText={setDiscount} keyboardType="decimal-pad" placeholder="0" placeholderTextColor={t.secondaryText} />
        <Text style={styles.fieldLabel}>Frais de livraison (Ar)</Text>
        <TextInput style={ui.input} value={deliveryFee} onChangeText={setDeliveryFee} keyboardType="decimal-pad" placeholder="0" placeholderTextColor={t.secondaryText} />
      </View>}
      <View style={styles.totalRow}><Text style={styles.totalLabel}>Total estimé</Text><Text style={styles.totalValue}>{total.toLocaleString('fr-FR')} Ar</Text></View>
      {!!error && <Text accessibilityRole="alert" style={ui.error}>{error}</Text>}
      <Action label={busy ? 'Création…' : 'Créer la commande'} onPress={() => void create()} disabled={busy || !client || !lines.length} />
    </View>}
  </ScrollView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  loader: { marginVertical: 32 },
  helper: { color: t.tint, fontSize: 14, fontWeight: '600', marginTop: -4, marginBottom: 14 },
  sectionTitle: { color: t.text, fontSize: 16, fontWeight: '600', marginTop: 8, marginBottom: 10 },
  lines: { marginTop: 16, marginBottom: 4, borderTopWidth: 1, borderTopColor: t.separator },
  draftLine: { minHeight: 64, flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: t.separator },
  lineCopy: { flex: 1 },
  lineName: { color: t.text, fontSize: 15, fontWeight: '600' },
  lineDetail: { color: t.secondaryText, fontSize: 14, marginTop: 4 },
  removeButton: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 8 },
  remove: { color: t.danger, fontSize: 14, fontWeight: '600' },
  optionalToggle: { minHeight: 48, justifyContent: 'center', marginTop: 8 },
  optionalText: { color: t.tint, fontSize: 14, fontWeight: '600' },
  extraFields: { borderLeftWidth: 2, borderLeftColor: t.separator, paddingLeft: 12, marginBottom: 8 },
  fieldLabel: { color: t.text, fontSize: 14, fontWeight: '600', marginBottom: 6 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 12, paddingTop: 14, borderTopWidth: 1, borderTopColor: t.separator },
  totalLabel: { color: t.secondaryText, fontSize: 14, fontWeight: '600' },
  totalValue: { color: t.text, fontSize: 18, fontWeight: '700' },
});
