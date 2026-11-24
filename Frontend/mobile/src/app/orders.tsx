import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api, fetchAll, type Client, type Commande, type Delivery, type Produit } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { OptionSelect } from '@/components/option-select';
import { LIST_PAGE_SIZE, ShowMore } from '@/components/show-more';

const PAYMENT_MODES = [
  { value: 'especes', label: 'Espèces' }, { value: 'mvola', label: 'MVola' },
  { value: 'orange_money', label: 'Orange Money' }, { value: 'airtel_money', label: 'Airtel Money' },
  { value: 'virement', label: 'Virement' }, { value: 'autre', label: 'Autre' },
];

export default function OrdersScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ focus?: string; step?: string }>();
  const [orders, setOrders] = useState<Commande[]>([]);
  const [orderLimit, setOrderLimit] = useState(LIST_PAGE_SIZE);
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({});
  const [paymentMode, setPaymentMode] = useState('especes');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [orderList, clientList, productList, deliveryList] = await Promise.all([
        fetchAll<Commande>('/orders/'),
        fetchAll<Client>('/clients/'),
        fetchAll<Produit>('/products/', { active: true }),
        fetchAll<Delivery>('/deliveries/'),
      ]);
      setOrders(orderList);
      setClients(clientList);
      setProducts(productList);
      setDeliveries(deliveryList);
      setOrderLimit(LIST_PAGE_SIZE);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const act = async (id: string, action: 'confirm' | 'cancel') => {
    setBusy(true); setError('');
    try {
      await api.post<Commande>(`/orders/${id}/${action}/`);
      await load();
      if (action === 'confirm') router.replace({ pathname: '/orders', params: { focus: id, step: 'delivery' } });
    }
    catch (e) { setError(e instanceof Error ? e.message : 'Action refusée.'); }
    finally { setBusy(false); }
  };

  const focusedId = typeof params.focus === 'string' ? params.focus : '';
  const focusedOrder = orders.find((order) => order.public_id === focusedId);
  const focusedDelivery = deliveries.find((delivery) => delivery.commande === focusedId);
  const visibleOrders = focusedId
    ? [...orders].sort((a, b) => Number(b.public_id === focusedId) - Number(a.public_id === focusedId)).slice(0, orderLimit)
    : orders.slice(0, orderLimit);

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

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Commandes" subtitle="Enregistrez les ventes, leurs paiements et suivez leur préparation et livraison." />
    <View style={styles.createRow}><Action label="Nouvelle commande" onPress={() => router.push('/orders/new')} /></View>
    {!!error && <Text style={ui.error}>{error}</Text>}
    {!loading && focusedOrder && <View style={styles.workflow}>
      <Text style={styles.workflowEyebrow}>{params.step === 'delivery' ? 'PROCHAINE ÉTAPE' : 'COMMANDE CRÉÉE'}</Text>
      <Text style={styles.workflowTitle}>{focusedOrder.reference}</Text>
      <Text style={styles.workflowText}>{params.step === 'delivery' && focusedOrder.statut === 'confirmee'
        ? focusedDelivery ? 'Une livraison est déjà associée à cette commande.' : 'La commande est confirmée. Créez son suivi de livraison si elle doit être expédiée.'
        : focusedOrder.statut === 'en_attente' ? 'Vérifiez la commande puis confirmez-la pour réserver le stock.' : `Statut : ${focusedOrder.statut.replaceAll('_', ' ')}.`}</Text>
      {focusedOrder.statut === 'en_attente' && <Action label="Confirmer la commande" onPress={() => void act(focusedId, 'confirm')} disabled={busy} />}
      {focusedOrder.statut === 'confirmee' && !focusedDelivery && <View style={styles.workflowAction}><Action label="Créer le suivi de livraison" variant="secondary" onPress={() => router.push({ pathname: '/deliveries/new', params: { order: focusedId } })} /></View>}
      {focusedDelivery && <View style={styles.workflowAction}><Action label="Ouvrir le suivi de livraison" variant="secondary" onPress={() => router.push({ pathname: '/deliveries', params: { focus: focusedDelivery.public_id } })} /></View>}
    </View>}
    <View style={styles.sectionHeading}><Text style={ui.section}>Historique des commandes</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#11645D" style={{ marginVertical: 24 }} /> : orders.length === 0 ? <Text style={ui.empty}>Aucune commande.</Text> : visibleOrders.map((order, index) => {
      const canCancel = ['en_attente', 'confirmee', 'en_preparation'].includes(order.statut);
      const canPay = Number(order.solde_restant) > 0 && !['annulee', 'retournee'].includes(order.statut);
      const canRefund = order.statut === 'retournee' && Number(order.montant_paye) > 0;
      return <FadeIn key={order.public_id} delay={Math.min(index * 35, 280)}><View style={[styles.order, order.public_id === focusedId && styles.orderFocused]}>
        <View style={styles.orderTop}><View><Text style={styles.orderName}>{order.reference}</Text><Text style={styles.detail}>{clients.find((item) => item.public_id === order.client)?.nomClient || order.client.slice(0, 8)}</Text></View><Text style={[styles.status, order.statut === 'livree' && styles.confirmed]}>{order.statut.replaceAll('_', ' ')}</Text></View>
        <Text style={styles.detail}>{new Date(order.date).toLocaleDateString('fr-FR')} · {order.lignes.length} ligne(s)</Text>
        {order.lignes.map((line, i) => <Text style={styles.lineDetail} key={`${line.product}-${i}`}>{products.find((item) => item.public_id === line.product)?.nomProduit || line.product.slice(0, 8)} · {line.quantite} × {line.prixUnitaire} Ar</Text>)}
        <View style={styles.totalRow}><Text style={styles.totalLabel}>Total {Number(order.montant_total).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalValue}>Reste {Number(order.solde_restant).toLocaleString('fr-FR')} Ar</Text></View>
        {order.paiements.map((payment) => <Text style={styles.paymentHistory} key={payment.public_id}>{payment.date} · {payment.typePaiement === 'remboursement' ? 'Remboursement' : 'Paiement'} {Number(payment.montant).toLocaleString('fr-FR')} Ar · {payment.mode}</Text>)}
        {canPay && <View style={styles.paymentBox}><OptionSelect label="Mode de paiement" options={PAYMENT_MODES} value={paymentMode} onChange={setPaymentMode} pageSize={4} /><View style={styles.inline}><TextInput style={[ui.input, styles.money]} value={paymentAmounts[order.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [order.public_id]: value }))} keyboardType="decimal-pad" placeholder="Montant versé (Ar)" /><Action label="Payer" onPress={() => void pay(order)} disabled={busy || !(Number(paymentAmounts[order.public_id]) > 0)} /></View></View>}
        {canRefund && <View style={styles.paymentBox}><Text style={styles.label}>Rembourser un paiement reçu</Text><View style={styles.inline}><TextInput style={[ui.input, styles.money]} value={paymentAmounts[order.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [order.public_id]: value }))} keyboardType="decimal-pad" placeholder="Montant remboursé (Ar)" /><Action label="Rembourser" onPress={() => void pay(order, 'remboursement')} disabled={busy || !(Number(paymentAmounts[order.public_id]) > 0)} /></View></View>}
        {order.statut === 'en_attente' && <View style={styles.actions}><Action label={busy ? '…' : 'Confirmer'} onPress={() => void act(order.public_id, 'confirm')} disabled={busy} /><MotionPressable onPress={() => void act(order.public_id, 'cancel')} disabled={busy} style={styles.cancelButton}><Text style={styles.cancelText}>Annuler</Text></MotionPressable></View>}
        {canCancel && order.statut !== 'en_attente' && <MotionPressable onPress={() => void act(order.public_id, 'cancel')} disabled={busy} style={styles.cancel}><Text style={styles.cancelText}>Annuler</Text></MotionPressable>}
      </View></FadeIn>;
    })}
    {!loading && <ShowMore remaining={orders.length - orderLimit} onPress={() => setOrderLimit((current) => current + LIST_PAGE_SIZE)} />}
  </ScrollView>;
}

const styles = StyleSheet.create({
  createRow: { marginBottom: 16 }, label: { color: '#526864', fontSize: 12, marginTop: 6, marginBottom: 8 },
  workflow: { padding: 16, marginBottom: 18, borderRadius: 16, borderWidth: 1, borderColor: '#B9DCD4', backgroundColor: '#E5F2EF' },
  workflowEyebrow: { color: '#11645D', fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  workflowTitle: { color: '#18332F', fontSize: 18, fontWeight: '700', marginTop: 5 },
  workflowText: { color: '#526864', fontSize: 14, lineHeight: 20, marginTop: 5, marginBottom: 12 },
  workflowAction: { marginTop: 8 },
  inline: { flexDirection: 'row', alignItems: 'center', gap: 9 }, money: { flex: 1, minWidth: 0 }, lineDetail: { color: '#526864', fontSize: 11, marginTop: 5 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 10, paddingTop: 9, borderTopWidth: 1, borderTopColor: '#EEF2EE' }, totalLabel: { color: '#526864', fontSize: 11, fontWeight: '600' }, totalValue: { color: '#18332F', fontSize: 13, fontWeight: '800' }, sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  order: { backgroundColor: '#fff', borderColor: '#DCE7E2', borderWidth: 1, borderRadius: 15, padding: 15, marginBottom: 10 }, orderFocused: { borderColor: '#11645D', borderWidth: 2 }, orderTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 }, orderName: { color: '#18332F', fontWeight: '800', fontSize: 14 }, status: { color: '#80520B', backgroundColor: '#FFF3D9', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 9, fontSize: 12, fontWeight: '700', textTransform: 'capitalize' }, confirmed: { color: '#11645D', backgroundColor: '#E5F2EF' }, detail: { color: '#526864', fontSize: 11, marginTop: 5 }, paymentHistory: { color: '#526864', fontSize: 12, marginTop: 5 }, paymentBox: { borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 7, marginTop: 10 }, actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 12 }, cancelButton: { borderColor: '#DFAAAA', borderWidth: 1, paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12 }, cancel: { alignSelf: 'flex-start', marginTop: 12 }, cancelText: { color: '#A43D32', fontWeight: '700', fontSize: 12 },
});
