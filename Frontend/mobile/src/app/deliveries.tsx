import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api, fetchAll, type Client, type Commande, type Delivery } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { LIST_PAGE_SIZE, ShowMore } from '@/components/show-more';
import { DeliveryLocationMap, type DeliveryMapPoint } from '@/components/delivery-location-map';

export default function DeliveriesScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ focus?: string }>();
  const [orders, setOrders] = useState<Commande[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [items, setItems] = useState<Delivery[]>([]);
  const [deliveryLimit, setDeliveryLimit] = useState(LIST_PAGE_SIZE);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [deliveryList, orderList, clientList] = await Promise.all([
        fetchAll<Delivery>('/deliveries/'),
        fetchAll<Commande>('/orders/'),
        fetchAll<Client>('/clients/'),
      ]);
      setItems(deliveryList);
      setOrders(orderList);
      setClients(clientList);
      setDeliveryLimit(LIST_PAGE_SIZE);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const mark = async (id: string, action: 'mark-preparing' | 'mark-shipped' | 'mark-delivered' | 'mark-failed' | 'retry' | 'mark-returned') => {
    setBusy(true);
    setError('');
    try {
      await api.post(`/deliveries/${id}/${action}/`);
      await load();
      router.replace({ pathname: '/deliveries', params: { focus: id } });
    }
    catch (e) { setError(e instanceof Error ? e.message : 'Mise à jour impossible.'); }
    finally { setBusy(false); }
  };

  const orderName = (id: string) => orders.find((order) => order.public_id === id)?.public_id.slice(0, 8) || id.slice(0, 8);
  const focusedId = typeof params.focus === 'string' ? params.focus : '';
  const focusedDelivery = items.find((delivery) => delivery.public_id === focusedId);
  const visibleDeliveries = focusedId
    ? [...items].sort((a, b) => Number(b.public_id === focusedId) - Number(a.public_id === focusedId)).slice(0, deliveryLimit)
    : items.slice(0, deliveryLimit);
  const clientFor = (delivery: Delivery) => {
    const linkedOrder = orders.find((order) => order.public_id === delivery.commande);
    return clients.find((client) => client.public_id === linkedOrder?.client);
  };
  const deliveredCountFor = (delivery: Delivery) => {
    const linkedOrder = orders.find((order) => order.public_id === delivery.commande);
    return linkedOrder ? orders.filter((order) => order.client === linkedOrder.client && order.statut === 'livree').length : 0;
  };
  const locationPoints = useMemo<DeliveryMapPoint[]>(() => {
    const points: DeliveryMapPoint[] = [];
    for (const delivery of items) {
      const order = orders.find((item) => item.public_id === delivery.commande);
      const client = clients.find((item) => item.public_id === order?.client);
      const latitude = Number(client?.latitude);
      const longitude = Number(client?.longitude);
      const deliveryAddress = delivery.adresse?.trim() || client?.adresse?.trim() || '';
      if (!deliveryAddress && (!Number.isFinite(latitude) || !Number.isFinite(longitude))) continue;
      points.push({
        id: delivery.public_id,
        title: `Commande ${delivery.commande.slice(0, 8)}`,
        address: deliveryAddress,
        detail: `${delivery.statut.replace('_', ' ')} · ${Number(delivery.fraisFacture).toLocaleString('fr-FR')} Ar facturés`,
        latitude: Number.isFinite(latitude) ? latitude : undefined,
        longitude: Number.isFinite(longitude) ? longitude : undefined,
      });
    }
    return points;
  }, [clients, items, orders]);

  return <ScrollView style={ui.page} contentContainerStyle={ui.content}>
    <AppPageHeading title="Livraisons" subtitle="Suivez les expéditions et mettez leur statut à jour." />
    <View style={styles.createRow}><Action label="Nouvelle livraison" onPress={() => router.push('/deliveries/new')} /></View>
    {!!error && <Text style={ui.error}>{error}</Text>}
    {!loading && focusedDelivery && <View style={styles.workflow}>
      <Text style={styles.workflowTitle}>{focusedDelivery.reference_commande || `Commande ${orderName(focusedDelivery.commande)}`}</Text>
      <Text style={styles.workflowText}>{focusedDelivery.statut === 'en_cours' ? 'Prochaine étape : préparer la commande.'
        : focusedDelivery.statut === 'en_preparation' ? 'Prochaine étape : marquer la commande comme expédiée.'
        : focusedDelivery.statut === 'expediee' ? 'Prochaine étape : confirmer la livraison au client.'
        : focusedDelivery.statut === 'echec' ? 'La livraison a échoué. Vous pouvez la relancer.'
        : focusedDelivery.statut === 'livree' ? 'Livraison terminée.' : `Statut : ${focusedDelivery.statut.replaceAll('_', ' ')}.`}</Text>
    </View>}
    <FadeIn delay={170}><DeliveryLocationMap points={locationPoints} /></FadeIn>
    <View style={styles.sectionHeading}><Text style={ui.section}>Suivi des livraisons</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#11645D" style={{ marginVertical: 24 }} /> : items.length === 0 ? <Text style={ui.empty}>Aucune livraison enregistrée.</Text> : visibleDeliveries.map((delivery, index) => <FadeIn key={delivery.public_id} delay={Math.min(index * 40, 280)}>
      <View style={[styles.row, delivery.public_id === focusedId && styles.rowFocused]}>
        <View style={styles.deliveryTop}><View><Text style={styles.name}>{delivery.reference_commande || `Commande ${orderName(delivery.commande)}`}</Text><Text style={styles.detail}>Client : {clientFor(delivery)?.nomClient || delivery.client}</Text></View><Text style={[styles.status, delivery.statut === 'livree' && styles.statusDone]}>{delivery.statut.replaceAll('_', ' ')}</Text></View>
        {!!clientFor(delivery)?.contact && <Text style={styles.detail}>Contact : {clientFor(delivery)?.contact}</Text>}
        <Text style={styles.detail}>Adresse : {delivery.adresse?.trim() || clientFor(delivery)?.adresse || '—'}</Text>
        <Text style={styles.detail}>Commandes livrées du client : {deliveredCountFor(delivery)}</Text>
        {!!delivery.dateExpedition && <Text style={styles.detail}>Expédiée le : {delivery.dateExpedition}</Text>}
        <Text style={styles.detail}>Date : {delivery.dateLivraison || 'à définir'}</Text>
        <View style={styles.amounts}><Text style={styles.amount}>Coût {delivery.cout} Ar</Text><Text style={styles.amount}>Facturé {delivery.fraisFacture} Ar</Text></View>
        {delivery.statut === 'en_cours' && <View style={styles.actions}><Action label="Préparer" onPress={() => void mark(delivery.public_id, 'mark-preparing')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'en_preparation' && <View style={styles.actions}><Action label="Expédier" onPress={() => void mark(delivery.public_id, 'mark-shipped')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'expediee' && <View style={styles.actions}><Action label="Livrer" onPress={() => void mark(delivery.public_id, 'mark-delivered')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'echec' && <View style={styles.actions}><Action label="Relancer" onPress={() => void mark(delivery.public_id, 'retry')} disabled={busy} /></View>}
        {delivery.statut === 'livree' && <View style={styles.actions}><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-returned')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Retour</Text></MotionPressable></View>}
      </View>
    </FadeIn>)}
    {!loading && <ShowMore remaining={items.length - deliveryLimit} onPress={() => setDeliveryLimit((current) => current + LIST_PAGE_SIZE)} />}
  </ScrollView>;
}

const styles = StyleSheet.create({
  createRow: { marginBottom: 16 },
  workflow: { padding: 15, marginBottom: 18, borderRadius: 16, borderWidth: 1, borderColor: '#B9DCD4', backgroundColor: '#E5F2EF' },
  workflowTitle: { color: '#18332F', fontSize: 16, fontWeight: '700' },
  workflowText: { color: '#526864', fontSize: 14, lineHeight: 20, marginTop: 5 },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  row: { backgroundColor: '#FFFFFF', padding: 17, borderColor: '#DCE7E2', borderWidth: 1, borderRadius: 16, marginBottom: 11 },
  rowFocused: { borderColor: '#11645D', borderWidth: 2 },
  deliveryTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  name: { fontWeight: '800', color: '#18332F', fontSize: 14 },
  status: { color: '#11645D', backgroundColor: '#E5F2EF', paddingVertical: 5, paddingHorizontal: 9, borderRadius: 10, fontSize: 12, fontWeight: '800', textTransform: 'capitalize' },
  statusDone: { color: '#11645D' },
  detail: { color: '#748078', fontSize: 12, marginTop: 10 },
  amounts: { flexDirection: 'row', gap: 15, marginTop: 9 },
  amount: { color: '#66716A', fontSize: 11, fontWeight: '600' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 14 },
  failButton: { borderWidth: 1, borderColor: '#DFAAAA', paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12 },
  failText: { color: '#A43D32', fontWeight: '700', fontSize: 12 },
});
