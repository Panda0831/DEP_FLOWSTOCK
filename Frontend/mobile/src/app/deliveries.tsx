import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { api, type Client, type Commande, type Delivery, type Page } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { DeliveryLocationMap, type DeliveryMapPoint } from '@/components/delivery-location-map';

export default function DeliveriesScreen() {
  const [orders, setOrders] = useState<Commande[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [items, setItems] = useState<Delivery[]>([]);
  const [selected, setSelected] = useState('');
  const [address, setAddress] = useState('');
  const [cost, setCost] = useState('0');
  const [charged, setCharged] = useState('0');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [deliveries, orderList, clientList] = await Promise.all([
        api.get<Page<Delivery> | Delivery[]>('/deliveries/'),
        api.get<Page<Commande> | Commande[]>('/orders/'),
        api.get<Page<Client> | Client[]>('/clients/'),
      ]);
      setItems(Array.isArray(deliveries) ? deliveries : deliveries.results);
      setOrders(Array.isArray(orderList) ? orderList : orderList.results);
      setClients(Array.isArray(clientList) ? clientList : clientList.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const create = async () => {
    if (!selected) { setError('Sélectionnez une commande confirmée.'); return; }
    setBusy(true);
    setError('');
    try {
      await api.post('/deliveries/', { commande: selected, adresse: address, cout: Number(cost), fraisFacture: Number(charged) });
      setSelected(''); setAddress(''); setCost('0'); setCharged('0');
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Création impossible.');
    } finally {
      setBusy(false);
    }
  };

  const mark = async (id: string, action: 'mark-preparing' | 'mark-shipped' | 'mark-delivered' | 'mark-failed' | 'retry' | 'mark-returned') => {
    setBusy(true);
    setError('');
    try { await api.post(`/deliveries/${id}/${action}/`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Mise à jour impossible.'); }
    finally { setBusy(false); }
  };

  const orderName = (id: string) => orders.find((order) => order.public_id === id)?.public_id.slice(0, 8) || id.slice(0, 8);
  const availableOrders = orders.filter((order) => order.statut === 'confirmee' && !items.some((delivery) => delivery.commande === order.public_id));
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
    <FadeIn delay={130}>
      <View style={ui.card}>
        <Text style={ui.cardTitle}>Nouvelle livraison</Text>
        {availableOrders.length ? <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>
          {availableOrders.map((order) => <MotionPressable key={order.public_id} onPress={() => setSelected(order.public_id)} style={[styles.choice, selected === order.public_id && styles.selected]}>
            <Text style={[styles.choiceText, selected === order.public_id && styles.choiceTextSelected]}>Commande {order.public_id.slice(0, 8)}</Text>
          </MotionPressable>)}
        </ScrollView> : <Text style={styles.helper}>Aucune commande confirmée en attente de livraison.</Text>}
        <TextInput style={ui.input} value={address} onChangeText={setAddress} placeholder="Adresse de livraison (facultatif)" />
        <View style={styles.amountInputs}><TextInput style={[ui.input, styles.amountInput]} value={cost} onChangeText={setCost} keyboardType="decimal-pad" placeholder="Coût réel (Ar)" /><TextInput style={[ui.input, styles.amountInput]} value={charged} onChangeText={setCharged} keyboardType="decimal-pad" placeholder="Frais facturés (Ar)" /></View>
        <Action label={busy ? 'Création…' : 'Créer le suivi'} onPress={() => void create()} disabled={busy || !availableOrders.length} />
      </View>
    </FadeIn>
    {!!error && <Text style={ui.error}>{error}</Text>}
    <FadeIn delay={170}><DeliveryLocationMap points={locationPoints} /></FadeIn>
    <View style={styles.sectionHeading}><Text style={ui.section}>Suivi des livraisons</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#078343" style={{ marginVertical: 24 }} /> : items.length === 0 ? <Text style={ui.empty}>Aucune livraison enregistrée.</Text> : items.map((delivery, index) => <FadeIn key={delivery.public_id} delay={Math.min(index * 40, 280)}>
      <View style={styles.row}>
        <View style={styles.deliveryTop}><View><Text style={styles.name}>{delivery.reference_commande || `Commande ${orderName(delivery.commande)}`}</Text><Text style={styles.detail}>{delivery.client}</Text></View><Text style={[styles.status, delivery.statut === 'livree' && styles.statusDone]}>{delivery.statut.replaceAll('_', ' ')}</Text></View>
        {!!delivery.adresse && <Text style={styles.detail}>Adresse : {delivery.adresse}</Text>}
        {!!delivery.dateExpedition && <Text style={styles.detail}>Expédiée le : {delivery.dateExpedition}</Text>}
        <Text style={styles.detail}>Date : {delivery.dateLivraison || 'à définir'}</Text>
        <View style={styles.amounts}><Text style={styles.amount}>Coût {delivery.cout} Ar</Text><Text style={styles.amount}>Facturé {delivery.fraisFacture} Ar</Text></View>
        {delivery.statut === 'en_cours' && <View style={styles.actions}><Action label="Préparer" onPress={() => void mark(delivery.public_id, 'mark-preparing')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'en_preparation' && <View style={styles.actions}><Action label="Marquer expédiée" onPress={() => void mark(delivery.public_id, 'mark-shipped')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'expediee' && <View style={styles.actions}><Action label="Marquer livrée" onPress={() => void mark(delivery.public_id, 'mark-delivered')} disabled={busy} /><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-failed')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Échec</Text></MotionPressable></View>}
        {delivery.statut === 'echec' && <View style={styles.actions}><Action label="Relancer la livraison" onPress={() => void mark(delivery.public_id, 'retry')} disabled={busy} /></View>}
        {delivery.statut === 'livree' && <View style={styles.actions}><MotionPressable onPress={() => void mark(delivery.public_id, 'mark-returned')} disabled={busy} style={styles.failButton}><Text style={styles.failText}>Enregistrer un retour</Text></MotionPressable></View>}
      </View>
    </FadeIn>)}
  </ScrollView>;
}

const styles = StyleSheet.create({
  choices: { gap: 8, paddingBottom: 12 },
  amountInputs: { flexDirection: 'row', gap: 9 },
  amountInput: { flex: 1, minWidth: 0 },
  choice: { paddingVertical: 10, paddingHorizontal: 13, borderRadius: 11, backgroundColor: '#F0F4F1' },
  selected: { backgroundColor: '#078343' },
  choiceText: { color: '#36443A', fontSize: 12, fontWeight: '700' },
  choiceTextSelected: { color: '#FFFFFF' },
  helper: { color: '#758079', fontSize: 12, marginBottom: 14 },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  row: { backgroundColor: '#FFFFFF', padding: 17, borderColor: '#DDE9DF', borderWidth: 1, borderRadius: 16, marginBottom: 11, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 7, elevation: 1 },
  deliveryTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  name: { fontWeight: '800', color: '#173D2B', fontSize: 14 },
  status: { color: '#078343', backgroundColor: '#E7F5EC', paddingVertical: 5, paddingHorizontal: 9, borderRadius: 10, fontSize: 10, fontWeight: '800', textTransform: 'capitalize' },
  statusDone: { color: '#078343' },
  detail: { color: '#748078', fontSize: 12, marginTop: 10 },
  amounts: { flexDirection: 'row', gap: 15, marginTop: 9 },
  amount: { color: '#66716A', fontSize: 11, fontWeight: '600' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 14 },
  failButton: { borderWidth: 1, borderColor: '#DFAAAA', paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12 },
  failText: { color: '#AD3C3C', fontWeight: '700', fontSize: 12 },
});
