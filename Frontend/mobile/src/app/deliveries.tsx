import { useCallback, useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { api, fetchAll, type Client, type Commande, type Delivery, type Produit } from '@/lib/session-api';
import { Action, useUiStyles } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { LIST_PAGE_SIZE, PageNavigation } from '@/components/list-pagination';
import { DeliveryLocationMap, type DeliveryMapPoint } from '@/components/delivery-location-map';
import { orderDisplayName } from '@/lib/order-display';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';
import { OptionSelect, toOptions } from '@/components/option-select';
import { FormDisclosure } from '@/components/form-disclosure';

const DELIVERY_STATUSES = [
  { value: 'en_cours', label: 'En cours' },
  { value: 'en_preparation', label: 'En préparation' },
  { value: 'expediee', label: 'Expédiée' },
  { value: 'livree', label: 'Livrée' },
  { value: 'echec', label: 'Échec' },
  { value: 'retournee', label: 'Retournée' },
  { value: 'annulee', label: 'Annulée' },
];

function normalizeSearch(value: string) {
  return value.trim().normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr-FR');
}

export default function DeliveriesScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const ui = useUiStyles();
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string; focus?: string; detail?: string }>();
  const [orders, setOrders] = useState<Commande[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [items, setItems] = useState<Delivery[]>([]);
  const [deliveryPage, setDeliveryPage] = useState(1);
  const [deliverySearch, setDeliverySearch] = useState('');
  const [clientFilter, setClientFilter] = useState('');
  const [productFilter, setProductFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [deliveryList, orderList, clientList, productList] = await Promise.all([
        fetchAll<Delivery>('/deliveries/'),
        fetchAll<Commande>('/orders/'),
        fetchAll<Client>('/clients/'),
        fetchAll<Produit>('/products/'),
      ]);
      setItems(deliveryList);
      setOrders(orderList);
      setClients(clientList);
      setProducts(productList);
      setDeliveryPage(1);
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

  const orderFor = (id: string) => orders.find((order) => order.public_id === id);
  const orderName = (id: string) => {
    const order = orderFor(id);
    return order ? orderDisplayName(order, clients, products) : 'Commande';
  };
  const focusedId = typeof params.id === 'string' ? params.id : typeof params.focus === 'string' ? params.focus : '';
  const focusedDelivery = items.find((delivery) => delivery.public_id === focusedId);
  const detailMode = (!!params.id || params.detail === '1') && !!focusedDelivery;
  const productOptions = useMemo(() => {
    const names = new Map(products.map((product) => [product.public_id, product.nomProduit]));
    const ids = new Set(orders.flatMap((order) => order.lignes.map((line) => line.product)));
    return [...ids].map((id) => ({ value: id, label: names.get(id) || `Article ${id.slice(0, 8)}` }));
  }, [orders, products]);
  const filteredDeliveries = useMemo(() => {
    const needle = normalizeSearch(deliverySearch);
    return items.filter((delivery) => {
      const order = orders.find((item) => item.public_id === delivery.commande);
      const client = clients.find((item) => item.public_id === order?.client || item.public_id === delivery.client);
      if (clientFilter && client?.public_id !== clientFilter) return false;
      if (productFilter && !order?.lignes.some((line) => line.product === productFilter)) return false;
      if (statusFilter && delivery.statut !== statusFilter) return false;
      if (!needle) return true;
      const productNames = order?.lignes.map((line) =>
        products.find((product) => product.public_id === line.product)?.nomProduit || line.product,
      ).join(' ') || '';
      return normalizeSearch([
        client?.nomClient || '',
        delivery.reference_commande || '',
        delivery.adresse || '',
        productNames,
        delivery.statut.replaceAll('_', ' '),
      ].join(' ')).includes(needle);
    });
  }, [clientFilter, clients, deliverySearch, items, orders, productFilter, products, statusFilter]);
  const visibleDeliveries = detailMode && focusedDelivery
    ? [focusedDelivery]
    : (focusedId
      ? [...filteredDeliveries].sort((a, b) => Number(b.public_id === focusedId) - Number(a.public_id === focusedId))
      : filteredDeliveries).slice((deliveryPage - 1) * LIST_PAGE_SIZE, deliveryPage * LIST_PAGE_SIZE);
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
        title: order ? orderDisplayName(order, clients, products) : 'Livraison',
        address: deliveryAddress,
        detail: `${delivery.statut.replace('_', ' ')} · ${Number(delivery.fraisFacture).toLocaleString('fr-FR')} Ar facturés`,
        latitude: Number.isFinite(latitude) ? latitude : undefined,
        longitude: Number.isFinite(longitude) ? longitude : undefined,
      });
    }
    return points;
  }, [clients, items, orders, products]);

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} showsVerticalScrollIndicator={false}>
    <AppPageHeading title="Livraisons" subtitle="Suivez les expéditions et mettez leur statut à jour." />
    {!detailMode && <View style={styles.createRow}><Action label="Nouvelle livraison" onPress={() => router.push('/deliveries/new')} /></View>}
    {!!error && <Text style={ui.error}>{error}</Text>}
    {!loading && focusedDelivery && <View style={styles.workflow}>
      <Text style={styles.workflowTitle}>{orderName(focusedDelivery.commande)}</Text>
      <Text style={styles.workflowReference}>Référence : {focusedDelivery.reference_commande || focusedDelivery.commande.slice(0, 8)}</Text>
      <Text style={styles.workflowText}>{focusedDelivery.statut === 'en_cours' ? 'Prochaine étape : préparer la commande.'
        : focusedDelivery.statut === 'en_preparation' ? 'Prochaine étape : marquer la commande comme expédiée.'
        : focusedDelivery.statut === 'expediee' ? 'Prochaine étape : confirmer la livraison au client.'
        : focusedDelivery.statut === 'echec' ? 'La livraison a échoué. Vous pouvez la relancer.'
        : focusedDelivery.statut === 'livree' ? 'Livraison terminée.' : `Statut : ${focusedDelivery.statut.replaceAll('_', ' ')}.`}</Text>
    </View>}
    {!detailMode && <FadeIn delay={170}><DeliveryLocationMap points={locationPoints} /></FadeIn>}
    {detailMode && <MotionPressable onPress={() => router.back()} style={styles.backLink} accessibilityRole="button"><Text style={styles.backText}>‹ Retour aux livraisons</Text></MotionPressable>}
    {!detailMode && <>
      <TextInput
        style={ui.input}
        value={deliverySearch}
        onChangeText={(value) => { setDeliverySearch(value); setDeliveryPage(1); }}
        placeholder="Rechercher un client, un article…"
        placeholderTextColor={t.secondaryText}
        accessibilityLabel="Rechercher dans les livraisons"
      />
      <FormDisclosure label="Filtres">
        <OptionSelect label="Client" options={toOptions(clients, (client) => client.nomClient, (client) => client.contact)} value={clientFilter} onChange={(value) => { setClientFilter(value); setDeliveryPage(1); }} optional pageSize={5} />
        <OptionSelect label="Article" options={productOptions} value={productFilter} onChange={(value) => { setProductFilter(value); setDeliveryPage(1); }} optional pageSize={5} />
        <OptionSelect label="Statut" options={DELIVERY_STATUSES} value={statusFilter} onChange={(value) => { setStatusFilter(value); setDeliveryPage(1); }} optional pageSize={7} />
      </FormDisclosure>
    </>}
    <View style={styles.sectionHeading}><Text style={ui.section}>{detailMode ? 'Gérer la livraison' : 'Suivi des livraisons'}</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color={t.tint} style={{ marginVertical: 24 }} /> : items.length === 0 ? <Text style={ui.empty}>Aucune livraison enregistrée.</Text> : visibleDeliveries.length === 0 ? <Text style={ui.empty}>Aucune livraison ne correspond à ces filtres.</Text> : visibleDeliveries.map((delivery, index) => <FadeIn key={delivery.public_id} delay={Math.min(index * 40, 280)}>
      <View style={[styles.row, delivery.public_id === focusedId && styles.rowFocused]}>
        <View style={styles.deliveryTop}><View style={{ flex: 1 }}><MotionPressable onPress={() => router.push({ pathname: '/orders/[id]', params: { id: delivery.commande } })} accessibilityRole="link" accessibilityLabel={`Ouvrir la commande de ${orderName(delivery.commande)}`}><Text style={styles.name}>{orderName(delivery.commande)} ›</Text></MotionPressable><Text style={styles.detail}>Référence : {delivery.reference_commande || delivery.commande.slice(0, 8)}</Text></View><View style={styles.deliveryActions}><Text style={[styles.status, delivery.statut === 'livree' && styles.statusDone]}>{delivery.statut.replaceAll('_', ' ')}</Text>{!detailMode && <MotionPressable onPress={() => router.push({ pathname: '/deliveries/[id]', params: { id: delivery.public_id } })} accessibilityRole="link" accessibilityLabel={`Gérer la livraison de ${orderName(delivery.commande)}`}><Text style={styles.manageLink}>Gérer ›</Text></MotionPressable>}</View></View>
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
    {!loading && !detailMode && <PageNavigation page={deliveryPage} totalItems={filteredDeliveries.length} onPageChange={setDeliveryPage} />}
  </ScrollView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  backLink: { minHeight: 44, justifyContent: 'center', alignSelf: 'flex-start', paddingRight: 12 },
  backText: { color: t.tint, fontSize: 14, fontWeight: '600' },
  deliveryActions: { alignItems: 'flex-end', gap: 4 },
  manageLink: { color: t.tint, fontSize: 13, fontWeight: '700', minHeight: 36, textAlignVertical: 'center' },
  createRow: { marginBottom: 16 },
  workflow: { padding: 15, marginBottom: 18, borderRadius: 16, borderWidth: 1, borderColor: t.separator, backgroundColor: t.tintSurface },
  workflowTitle: { color: t.text, fontSize: 16, fontWeight: '700' },
  workflowReference: { color: t.secondaryText, fontSize: 12, marginTop: 3 },
  workflowText: { color: t.secondaryText, fontSize: 14, lineHeight: 20, marginTop: 5 },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  row: { backgroundColor: t.surface, padding: 17, borderColor: t.separator, borderWidth: 1, borderRadius: 16, marginBottom: 11 },
  rowFocused: { borderColor: t.tint, borderWidth: 2 },
  deliveryTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  name: { fontWeight: '800', color: t.text, fontSize: 14 },
  status: { color: t.tint, backgroundColor: t.tintSurface, paddingVertical: 5, paddingHorizontal: 9, borderRadius: 10, fontSize: 12, fontWeight: '800', textTransform: 'capitalize' },
  statusDone: { color: t.tint },
  detail: { color: t.secondaryText, fontSize: 12, marginTop: 10 },
  amounts: { flexDirection: 'row', gap: 15, marginTop: 9 },
  amount: { color: t.secondaryText, fontSize: 11, fontWeight: '600' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 14 },
  failButton: { borderWidth: 1, borderColor: t.danger, paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12 },
  failText: { color: t.danger, fontWeight: '700', fontSize: 12 },
});
