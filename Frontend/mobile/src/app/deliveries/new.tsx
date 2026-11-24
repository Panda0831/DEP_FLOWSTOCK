import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { api, fetchAll, type Client, type Commande, type Delivery, type Produit } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { MotionPressable } from '@/components/motion';
import { OptionSelect, toOptions } from '@/components/option-select';
import { orderDisplayName } from '@/lib/order-display';

export default function NewDeliveryScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ order?: string }>();
  const [orders, setOrders] = useState<Commande[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [selected, setSelected] = useState('');
  const [address, setAddress] = useState('');
  const [cost, setCost] = useState('0');
  const [charged, setCharged] = useState('0');
  const [feesOpen, setFeesOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [deliveryList, orderList, clientList, productList] = await Promise.all([
        fetchAll<Delivery>('/deliveries/'),
        fetchAll<Commande>('/orders/'),
        fetchAll<Client>('/clients/'),
        fetchAll<Produit>('/products/'),
      ]);
      setDeliveries(deliveryList);
      setOrders(orderList);
      setClients(clientList);
      setProducts(productList);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const availableOrders = useMemo(
    () => orders.filter((order) => order.statut === 'confirmee' && !deliveries.some((delivery) => delivery.commande === order.public_id)),
    [deliveries, orders],
  );
  const order = orders.find((item) => item.public_id === selected);
  const client = clients.find((item) => item.public_id === order?.client);

  useEffect(() => {
    const nextOrder = typeof params.order === 'string'
      ? orders.find((item) => item.public_id === params.order)
      : availableOrders.length === 1 ? availableOrders[0] : undefined;
    if (!nextOrder) return;
    setSelected(nextOrder.public_id);
    setAddress(clients.find((item) => item.public_id === nextOrder.client)?.adresse || '');
  }, [availableOrders, clients, orders, params.order]);

  const create = async () => {
    if (!selected) { setError('Sélectionnez une commande confirmée.'); return; }
    setBusy(true); setError('');
    try {
      const created = await api.post<Delivery>('/deliveries/', { commande: selected, adresse: address, cout: Number(cost), fraisFacture: Number(charged) });
      router.replace({ pathname: '/deliveries', params: { focus: created.public_id } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Création impossible.');
      setBusy(false);
    }
  };

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Nouvelle livraison" subtitle="Choisissez une commande confirmée, vérifiez le client puis créez le suivi." />
    {loading ? <ActivityIndicator color="#11645D" style={styles.loader} /> : <View style={ui.card}>
      {availableOrders.length
        ? <OptionSelect
            label="Commande à livrer"
            options={toOptions(availableOrders, (item) => orderDisplayName(item, clients, products), (item) => `Réf. ${item.reference}`)}
            value={selected}
            onChange={(value) => {
              setSelected(value);
              const nextOrder = orders.find((item) => item.public_id === value);
              const nextClient = clients.find((item) => item.public_id === nextOrder?.client);
              setAddress(nextClient?.adresse || '');
            }}
            placeholder="Choisir une commande"
          />
        : <View><Text style={styles.helper}>{orders.length ? 'Aucune commande confirmée en attente de livraison.' : 'Créez une commande, puis confirmez-la avant de planifier la livraison.'}</Text><Action label={orders.length ? 'Voir les commandes' : 'Créer une commande'} variant="secondary" onPress={() => router.push(orders.length ? '/orders' : '/orders/new')} /></View>}
      {!!client && <View style={styles.clientBox}>
        <Text style={styles.clientName}>{client.nomClient}</Text>
        <Text style={styles.clientDetail}>Contact : {client.contact || '—'}</Text>
        <Text style={styles.clientDetail}>Adresse : {address.trim() || client.adresse || '—'}</Text>
      </View>}
      <Text style={styles.fieldLabel}>Adresse de livraison</Text>
      <TextInput style={ui.input} value={address} onChangeText={setAddress} placeholder="Adresse du client" placeholderTextColor="#526864" accessibilityLabel="Adresse de livraison" />
      <MotionPressable onPress={() => setFeesOpen((open) => !open)} style={styles.feesToggle} accessibilityRole="button" accessibilityState={{ expanded: feesOpen }}>
        <Text style={styles.feesToggleText}>{feesOpen ? 'Masquer les frais' : 'Renseigner les frais (facultatif)'}</Text>
      </MotionPressable>
      {feesOpen && <View style={styles.feeFields}>
        <Text style={styles.fieldLabel}>Coût réel (Ar)</Text>
        <TextInput style={ui.input} value={cost} onChangeText={setCost} keyboardType="decimal-pad" placeholder="0" placeholderTextColor="#526864" accessibilityLabel="Coût réel de la livraison en ariary" />
        <Text style={styles.fieldLabel}>Frais facturés au client (Ar)</Text>
        <TextInput style={ui.input} value={charged} onChangeText={setCharged} keyboardType="decimal-pad" placeholder="0" placeholderTextColor="#526864" accessibilityLabel="Frais facturés au client en ariary" />
      </View>}
      {!!error && <Text accessibilityRole="alert" style={ui.error}>{error}</Text>}
      <Action label={busy ? 'Création…' : 'Créer le suivi de livraison'} onPress={() => void create()} disabled={busy || !selected} />
    </View>}
  </ScrollView>;
}

const styles = StyleSheet.create({
  loader: { marginVertical: 32 },
  helper: { color: '#526864', fontSize: 14, lineHeight: 20, marginBottom: 14 },
  clientBox: { backgroundColor: '#E5F2EF', borderRadius: 12, padding: 14, marginBottom: 14 },
  clientName: { color: '#18332F', fontSize: 15, fontWeight: '600' },
  clientDetail: { color: '#526864', fontSize: 14, marginTop: 5 },
  fieldLabel: { color: '#18332F', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  feesToggle: { minHeight: 48, justifyContent: 'center', marginTop: 2, marginBottom: 8 },
  feesToggleText: { color: '#11645D', fontSize: 14, fontWeight: '600' },
  feeFields: { borderLeftWidth: 2, borderLeftColor: '#DCE7E2', paddingLeft: 12, marginBottom: 8 },
});
