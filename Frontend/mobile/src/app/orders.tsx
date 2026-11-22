import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { api, type Client, type Commande, type Page, type Produit } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';

type DraftLine = { product: string; quantity: string };
const PAYMENT_MODES = [
  { value: 'especes', label: 'Espèces' }, { value: 'mvola', label: 'MVola' },
  { value: 'orange_money', label: 'Orange Money' }, { value: 'airtel_money', label: 'Airtel Money' },
  { value: 'virement', label: 'Virement' }, { value: 'autre', label: 'Autre' },
];

export default function OrdersScreen() {
  const router = useRouter();
  const [orders, setOrders] = useState<Commande[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [client, setClient] = useState('');
  const [product, setProduct] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [discount, setDiscount] = useState('0');
  const [deliveryFee, setDeliveryFee] = useState('0');
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({});
  const [paymentMode, setPaymentMode] = useState('especes');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [orderResult, clientResult, productResult] = await Promise.all([
        api.get<Page<Commande> | Commande[]>('/orders/'),
        api.get<Page<Client> | Client[]>('/clients/'),
        api.get<Page<Produit> | Produit[]>('/products/', { active: true }),
      ]);
      setOrders(Array.isArray(orderResult) ? orderResult : orderResult.results);
      setClients(Array.isArray(clientResult) ? clientResult : clientResult.results);
      setProducts(Array.isArray(productResult) ? productResult : productResult.results);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

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
      await api.post('/orders/', {
        client,
        items: lines.map((line) => ({ product: line.product, quantity: Number(line.quantity) })),
        remise: Number(discount),
        fraisLivraison: Number(deliveryFee),
      });
      setClient(''); setLines([]); setDiscount('0'); setDeliveryFee('0');
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Création impossible.'); }
    finally { setBusy(false); }
  };

  const act = async (id: string, action: 'confirm' | 'cancel') => {
    setBusy(true); setError('');
    try { await api.post(`/orders/${id}/${action}/`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Action refusée.'); }
    finally { setBusy(false); }
  };

  const pay = async (order: Commande, typePaiement: 'versement' | 'remboursement' = 'versement') => {
    const montant = Number(paymentAmounts[order.public_id]);
    if (!Number.isFinite(montant) || montant <= 0) { setError('Indiquez un montant de paiement valide.'); return; }
    setBusy(true); setError('');
    try {
      await api.post('/payments/', { operation: 'order', public_id: order.public_id, montant, mode: paymentMode, typePaiement });
      setPaymentAmounts((current) => ({ ...current, [order.public_id]: '' }));
      await load();
    } catch (e) { setError(e instanceof Error ? e.message : 'Paiement impossible.'); }
    finally { setBusy(false); }
  };

  const subtotal = lines.reduce((sum, line) => sum + Number(line.quantity) * Number(products.find((item) => item.public_id === line.product)?.prixVente || 0), 0);
  const total = Math.max(0, subtotal - Number(discount || 0)) + Number(deliveryFee || 0);

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Commandes" subtitle="Enregistrez les ventes, leurs paiements et suivez leur préparation et livraison." />
    <FadeIn delay={130}><View style={ui.card}>
      <Text style={ui.cardTitle}>Nouvelle commande</Text>
      <MotionPressable onPress={() => router.push('/clients')}><Text style={styles.helper}>Besoin d’un client ? Ouvrir le fichier clients ›</Text></MotionPressable>
      <Text style={styles.label}>Client</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>
        {clients.map((item) => <Choice key={item.public_id} label={item.nomClient} selected={client === item.public_id} onPress={() => setClient(item.public_id)} />)}
      </ScrollView>
      <Text style={styles.label}>Ajouter un produit</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>
        {products.map((item) => <Choice key={item.public_id} label={item.nomProduit} selected={product === item.public_id} onPress={() => setProduct(item.public_id)} />)}
      </ScrollView>
      <View style={styles.inline}><TextInput style={[ui.input, styles.quantity]} value={quantity} onChangeText={setQuantity} keyboardType="number-pad" placeholder="Quantité" /><Action label="Ajouter" onPress={addLine} /></View>
      {lines.map((line) => <View style={styles.draftLine} key={line.product}><Text style={styles.lineName}>{products.find((item) => item.public_id === line.product)?.nomProduit}</Text><Text style={styles.lineDetail}>{line.quantity} × {products.find((item) => item.public_id === line.product)?.prixVente} Ar</Text><MotionPressable onPress={() => setLines((current) => current.filter((item) => item.product !== line.product))}><Text style={styles.remove}>Retirer</Text></MotionPressable></View>)}
      <View style={styles.inline}><TextInput style={[ui.input, styles.money]} value={discount} onChangeText={setDiscount} keyboardType="decimal-pad" placeholder="Remise (Ar)" /><TextInput style={[ui.input, styles.money]} value={deliveryFee} onChangeText={setDeliveryFee} keyboardType="decimal-pad" placeholder="Frais livraison (Ar)" /></View>
      <View style={styles.totalRow}><Text style={styles.totalLabel}>Total estimé</Text><Text style={styles.totalValue}>{total.toLocaleString('fr-FR')} Ar</Text></View>
      <Action label={busy ? 'Création…' : 'Créer la commande'} onPress={() => void create()} disabled={busy || !lines.length} />
    </View></FadeIn>
    {!!error && <Text style={ui.error}>{error}</Text>}
    <View style={styles.sectionHeading}><Text style={ui.section}>Historique des commandes</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#078343" style={{ marginVertical: 24 }} /> : orders.length === 0 ? <Text style={ui.empty}>Aucune commande.</Text> : orders.map((order, index) => {
      const canCancel = ['en_attente', 'confirmee', 'en_preparation'].includes(order.statut);
      const canPay = Number(order.solde_restant) > 0 && !['annulee', 'retournee'].includes(order.statut);
      const canRefund = order.statut === 'retournee' && Number(order.montant_paye) > 0;
      return <FadeIn key={order.public_id} delay={Math.min(index * 35, 280)}><View style={styles.order}>
        <View style={styles.orderTop}><View><Text style={styles.orderName}>{order.reference}</Text><Text style={styles.detail}>{clients.find((item) => item.public_id === order.client)?.nomClient || order.client.slice(0, 8)}</Text></View><Text style={[styles.status, order.statut === 'livree' && styles.confirmed]}>{order.statut.replaceAll('_', ' ')}</Text></View>
        <Text style={styles.detail}>{new Date(order.date).toLocaleDateString('fr-FR')} · {order.lignes.length} ligne(s)</Text>
        {order.lignes.map((line, i) => <Text style={styles.lineDetail} key={`${line.product}-${i}`}>{products.find((item) => item.public_id === line.product)?.nomProduit || line.product.slice(0, 8)} · {line.quantite} × {line.prixUnitaire} Ar</Text>)}
        <View style={styles.totalRow}><Text style={styles.totalLabel}>Total {Number(order.montant_total).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalValue}>Reste {Number(order.solde_restant).toLocaleString('fr-FR')} Ar</Text></View>
        {order.paiements.map((payment) => <Text style={styles.paymentHistory} key={payment.public_id}>{payment.date} · {payment.typePaiement === 'remboursement' ? 'Remboursement' : 'Paiement'} {Number(payment.montant).toLocaleString('fr-FR')} Ar · {payment.mode}</Text>)}
        {canPay && <View style={styles.paymentBox}><Text style={styles.label}>Enregistrer un paiement</Text><ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>{PAYMENT_MODES.map((mode) => <Choice key={mode.value} label={mode.label} selected={paymentMode === mode.value} onPress={() => setPaymentMode(mode.value)} />)}</ScrollView><View style={styles.inline}><TextInput style={[ui.input, styles.money]} value={paymentAmounts[order.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [order.public_id]: value }))} keyboardType="decimal-pad" placeholder="Montant versé (Ar)" /><Action label="Ajouter paiement" onPress={() => void pay(order)} disabled={busy} /></View></View>}
        {canRefund && <View style={styles.paymentBox}><Text style={styles.label}>Rembourser un paiement reçu</Text><View style={styles.inline}><TextInput style={[ui.input, styles.money]} value={paymentAmounts[order.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [order.public_id]: value }))} keyboardType="decimal-pad" placeholder="Montant remboursé (Ar)" /><Action label="Enregistrer le remboursement" onPress={() => void pay(order, 'remboursement')} disabled={busy} /></View></View>}
        {order.statut === 'en_attente' && <View style={styles.actions}><Action label={busy ? '…' : 'Confirmer'} onPress={() => void act(order.public_id, 'confirm')} disabled={busy} /><MotionPressable onPress={() => void act(order.public_id, 'cancel')} disabled={busy} style={styles.cancelButton}><Text style={styles.cancelText}>Annuler</Text></MotionPressable></View>}
        {canCancel && order.statut !== 'en_attente' && <MotionPressable onPress={() => void act(order.public_id, 'cancel')} disabled={busy} style={styles.cancel}><Text style={styles.cancelText}>Annuler la commande</Text></MotionPressable>}
      </View></FadeIn>;
    })}
  </ScrollView>;
}

function Choice({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return <MotionPressable onPress={onPress} style={[styles.choice, selected && styles.choiceSelected]}><Text style={[styles.choiceText, selected && styles.choiceTextSelected]}>{label}</Text></MotionPressable>;
}

const styles = StyleSheet.create({
  helper: { color: '#078343', fontSize: 12, fontWeight: '700', marginBottom: 13 }, label: { color: '#68736B', fontSize: 12, marginTop: 6, marginBottom: 8 },
  choices: { flexDirection: 'row', gap: 8, paddingBottom: 8 }, choice: { paddingVertical: 9, paddingHorizontal: 12, borderRadius: 11, backgroundColor: '#F0F4F1' }, choiceSelected: { backgroundColor: '#078343' }, choiceText: { color: '#465149', fontSize: 12, fontWeight: '600' }, choiceTextSelected: { color: '#fff' },
  inline: { flexDirection: 'row', alignItems: 'center', gap: 9 }, quantity: { flex: 1, minWidth: 0 }, money: { flex: 1, minWidth: 0 }, draftLine: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 9, borderTopWidth: 1, borderTopColor: '#EEF2EE' }, lineName: { flex: 1, color: '#173D2B', fontSize: 12, fontWeight: '700' }, lineDetail: { color: '#77827A', fontSize: 11, marginTop: 5 }, remove: { color: '#B63838', fontSize: 11, fontWeight: '700' },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 10, paddingTop: 9, borderTopWidth: 1, borderTopColor: '#EEF2EE' }, totalLabel: { color: '#69756D', fontSize: 11, fontWeight: '600' }, totalValue: { color: '#173D2B', fontSize: 13, fontWeight: '800' }, sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  order: { backgroundColor: '#fff', borderColor: '#DDE9DF', borderWidth: 1, borderRadius: 15, padding: 15, marginBottom: 10 }, orderTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 }, orderName: { color: '#173D2B', fontWeight: '800', fontSize: 14 }, status: { color: '#8C6511', backgroundColor: '#FFF4D9', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 9, fontSize: 10, fontWeight: '700', textTransform: 'capitalize' }, confirmed: { color: '#078343', backgroundColor: '#E7F5EC' }, detail: { color: '#7B857D', fontSize: 11, marginTop: 5 }, paymentHistory: { color: '#68736B', fontSize: 10, marginTop: 5 }, paymentBox: { borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 7, marginTop: 10 }, actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12 }, cancelButton: { borderColor: '#DFAAAA', borderWidth: 1, paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12 }, cancel: { alignSelf: 'flex-start', marginTop: 12 }, cancelText: { color: '#AD3C3C', fontWeight: '700', fontSize: 12 },
});
