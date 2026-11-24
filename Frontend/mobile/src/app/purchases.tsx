import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { FormDisclosure, useAutoOpenForm } from '@/components/form-disclosure';
import { OptionSelect, toOptions } from '@/components/option-select';
import { QuantityField } from '@/components/quantity-field';
import { LIST_PAGE_SIZE, ShowMore } from '@/components/show-more';
import { useAuth } from '@/lib/auth-context';
import { api, fetchAll, type Produit, type Fournisseur, type Purchase } from '@/lib/session-api';

type DraftLine = { product: string; quantity: string; unit_price: string };
const PAYMENT_MODES = [
  { value: 'especes', label: 'Espèces' }, { value: 'mvola', label: 'MVola' },
  { value: 'orange_money', label: 'Orange Money' }, { value: 'airtel_money', label: 'Airtel Money' },
  { value: 'virement', label: 'Virement' }, { value: 'autre', label: 'Autre' },
];
const OBTENTION_OPTIONS = [
  { value: 'commande', label: 'Commande' }, { value: 'achat_direct', label: 'Achat direct' },
];

export default function PurchasesScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ focus?: string; step?: string; supplier?: string; product?: string }>();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;
  const autoOpen = useAutoOpenForm();
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [purchaseLimit, setPurchaseLimit] = useState(LIST_PAGE_SIZE);
  const [suppliers, setSuppliers] = useState<Fournisseur[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [supplier, setSupplier] = useState('');
  const [selectedProduct, setSelectedProduct] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [unitPrice, setUnitPrice] = useState('');
  const [lines, setLines] = useState<DraftLine[]>([]);
  const [editingPurchase, setEditingPurchase] = useState<Purchase | null>(null);
  const [location, setLocation] = useState('');
  const [obtention, setObtention] = useState<'commande' | 'achat_direct'>('commande');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [receiveQuantities, setReceiveQuantities] = useState<Record<string, Record<string, string>>>({});
  const [returnQuantities, setReturnQuantities] = useState<Record<string, Record<string, string>>>({});
  const [paymentAmounts, setPaymentAmounts] = useState<Record<string, string>>({});
  const [paymentMode, setPaymentMode] = useState('especes');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [purchaseList, supplierList, productList] = await Promise.all([
        fetchAll<Purchase>('/purchases/'),
        fetchAll<Fournisseur>('/suppliers/'),
        fetchAll<Produit>('/products/', { active: true }),
      ]);
      setPurchases(purchaseList);
      setSuppliers(supplierList);
      setProducts(productList);
      setPurchaseLimit(LIST_PAGE_SIZE);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement des achats impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const selectedSupplier = typeof params.supplier === 'string'
      ? suppliers.find((item) => item.public_id === params.supplier)
      : suppliers.length === 1 ? suppliers[0] : undefined;
    if (selectedSupplier) setSupplier(selectedSupplier.public_id);
    const selected = typeof params.product === 'string'
      ? products.find((item) => item.public_id === params.product)
      : products.length === 1 ? products[0] : undefined;
    if (selected) {
      setSelectedProduct(selected.public_id);
      setUnitPrice(selected.prixAchat || '0');
    }
  }, [params.product, params.supplier, products, suppliers]);

  const addLine = () => {
    if (!selectedProduct || Number(quantity) < 1 || Number(unitPrice) < 0 || !unitPrice) {
      setError('Choisissez un produit et renseignez une quantité et un prix valides.');
      return;
    }
    if (lines.some((line) => line.product === selectedProduct)) {
      setError('Ce produit est déjà dans l’achat.');
      return;
    }
    setLines((current) => [...current, { product: selectedProduct, quantity, unit_price: unitPrice }]);
    setSelectedProduct('');
    setQuantity('1');
    setUnitPrice('');
    setError('');
  };

  const savePurchase = async () => {
    if (!supplier || !lines.length) {
      setError('Choisissez un fournisseur et ajoutez au moins un produit.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      const payload = {
        supplier,
        lieuAchat: location,
        modeObtention: obtention,
        items: lines.map((line) => ({ product: line.product, quantity: Number(line.quantity), unit_price: line.unit_price })),
      };
      const wasEditing = !!editingPurchase;
      const saved = editingPurchase
        ? await api.patch<Purchase>(`/purchases/${editingPurchase.public_id}/`, payload)
        : await api.post<Purchase>('/purchases/', payload);
      setSupplier(''); setLines([]); setLocation(''); setEditingPurchase(null); setObtention('commande'); setDetailsOpen(false);
      await load();
      if (!wasEditing) router.replace({ pathname: '/purchases', params: { focus: saved.public_id, step: 'receive' } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Création de l’achat impossible.');
    } finally {
      setBusy(false);
    }
  };

  const editPurchase = (purchase: Purchase) => {
    setEditingPurchase(purchase);
    setSupplier(purchase.supplier);
    setLocation(purchase.lieuAchat);
    setObtention(purchase.modeObtention);
    setDetailsOpen(true);
    setLines(purchase.lignes.map((line) => ({ product: line.product, quantity: String(line.quantite), unit_price: String(line.prixUnitaire) })));
    setError('');
  };

  const receive = async (purchase: Purchase) => {
    const items = purchase.lignes
      .map((line) => ({ product: line.product, quantity: Number(receiveQuantities[purchase.public_id]?.[line.product] || 0) }))
      .filter((line) => line.quantity > 0);
    if (!items.length) { setError('Indiquez au moins une quantité à réceptionner.'); return; }
    setBusy(true); setError('');
    try {
      await api.post(`/purchases/${purchase.public_id}/receive/`, { items });
      setReceiveQuantities((current) => ({ ...current, [purchase.public_id]: {} }));
      await load();
      const pendingAfterReceive = purchase.lignes.some((line) => line.quantite_recue + (items.find((item) => item.product === line.product)?.quantity || 0) < line.quantite);
      router.replace({ pathname: '/purchases', params: { focus: purchase.public_id, step: pendingAfterReceive ? 'receive' : 'payment' } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Réception impossible.');
    } finally { setBusy(false); }
  };

  const returnToSupplier = async (purchase: Purchase) => {
    const items = purchase.lignes
      .map((line) => ({ product: line.product, quantity: Number(returnQuantities[purchase.public_id]?.[line.product] || 0) }))
      .filter((line) => line.quantity > 0);
    if (!items.length) { setError('Indiquez au moins une quantité à retourner.'); return; }
    setBusy(true); setError('');
    try {
      await api.post(`/purchases/${purchase.public_id}/return-to-supplier/`, { items, motif: 'Retour fournisseur' });
      setReturnQuantities((current) => ({ ...current, [purchase.public_id]: {} }));
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Retour fournisseur impossible.');
    } finally { setBusy(false); }
  };

  const pay = async (purchase: Purchase) => {
    const montant = Number(paymentAmounts[purchase.public_id]);
    if (!Number.isFinite(montant) || montant <= 0) { setError('Indiquez un montant de paiement valide.'); return; }
    setBusy(true); setError('');
    try {
      await api.post('/payments/', { operation: 'purchase', public_id: purchase.public_id, montant, mode: paymentMode });
      setPaymentAmounts((current) => ({ ...current, [purchase.public_id]: '' }));
      await load();
      router.replace({ pathname: '/purchases', params: { focus: purchase.public_id, step: montant >= Number(purchase.solde_restant) ? 'done' : 'payment' } });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Paiement impossible.');
    } finally { setBusy(false); }
  };

  const cancel = async (purchase: Purchase) => {
    setBusy(true); setError('');
    try { await api.post(`/purchases/${purchase.public_id}/cancel/`); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Annulation impossible.'); }
    finally { setBusy(false); }
  };

  const focusedId = typeof params.focus === 'string' ? params.focus : '';
  const focusedPurchase = purchases.find((purchase) => purchase.public_id === focusedId);
  const visiblePurchases = focusedId
    ? [...purchases].sort((a, b) => Number(b.public_id === focusedId) - Number(a.public_id === focusedId)).slice(0, purchaseLimit)
    : purchases.slice(0, purchaseLimit);

  if (!isAdmin) return <ScrollView style={ui.page} contentContainerStyle={ui.content}><AppPageHeading title="Achats" subtitle="Cette section est réservée aux administrateurs." /></ScrollView>;

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Achats" subtitle="Commandez auprès de vos fournisseurs et réceptionnez les produits en plusieurs fois." />
    <FormDisclosure label={editingPurchase ? `Modifier ${editingPurchase.reference}` : 'Nouvel achat'} openWhen={autoOpen ? '1' : (editingPurchase?.public_id ?? null)}>
      <View style={ui.card}>
      {!suppliers.length && <MotionPressable onPress={() => router.push({ pathname: '/suppliers', params: { add: '1', flow: 'purchase' } })} accessibilityRole="link"><Text style={styles.helper}>Ajouter un fournisseur ›</Text></MotionPressable>}
      <OptionSelect label="Fournisseur" options={toOptions(suppliers, (item) => item.nomFournisseur)} value={supplier} onChange={setSupplier} placeholder="Choisir un fournisseur" />
      {!products.length && !!supplier && <MotionPressable onPress={() => router.push({ pathname: '/products', params: { add: '1', flow: 'purchase', supplier } })} accessibilityRole="link"><Text style={styles.helper}>Ajouter un produit ›</Text></MotionPressable>}
      <OptionSelect
        label="Ajouter un produit"
        options={toOptions(products, (item) => item.nomProduit, (item) => `${item.prixAchat || '0'} Ar`)}
        value={selectedProduct}
        onChange={(value) => { setSelectedProduct(value); setUnitPrice(products.find((item) => item.public_id === value)?.prixAchat || '0'); }}
        placeholder="Choisir un produit"
      />
      <QuantityField value={quantity} onChange={setQuantity} />
      <Text style={styles.fieldLabel}>Prix d’achat unitaire (Ar)</Text>
      <TextInput style={ui.input} value={unitPrice} onChangeText={setUnitPrice} keyboardType="decimal-pad" placeholder="0" placeholderTextColor="#526864" accessibilityLabel="Prix d’achat unitaire en ariary" />
      <Action label="Ajouter cet article" variant="secondary" onPress={addLine} disabled={!selectedProduct || !(Number(quantity) >= 1) || !(Number(unitPrice) >= 0) || !unitPrice} />
      {lines.map((line) => <View style={styles.draftLine} key={line.product}><Text style={styles.lineName}>{products.find((p) => p.public_id === line.product)?.nomProduit}</Text><Text style={styles.lineDetail}>{line.quantity} × {line.unit_price} Ar</Text><MotionPressable onPress={() => setLines((current) => current.filter((item) => item.product !== line.product))}><Text style={styles.remove}>Retirer</Text></MotionPressable></View>)}
      <View style={styles.modeRow}><Text style={styles.totalLabel}>Total prévu</Text><Text style={styles.totalValue}>{lines.reduce((sum, line) => sum + Number(line.quantity) * Number(line.unit_price), 0).toLocaleString('fr-FR')} Ar</Text></View>
      <MotionPressable onPress={() => setDetailsOpen((open) => !open)} style={styles.detailsToggle} accessibilityRole="button" accessibilityState={{ expanded: detailsOpen }}>
        <Text style={styles.detailsToggleText}>{detailsOpen ? 'Masquer les options' : 'Options d’achat (facultatif)'}</Text>
      </MotionPressable>
      {detailsOpen && <View style={styles.detailsBox}>
        <OptionSelect label="Mode d’obtention" options={OBTENTION_OPTIONS} value={obtention} onChange={(value) => setObtention(value as 'commande' | 'achat_direct')} />
        <Text style={styles.fieldLabel}>Lieu d’achat</Text>
        <TextInput style={ui.input} value={location} onChangeText={setLocation} placeholder="Ex. Marché central" placeholderTextColor="#526864" accessibilityLabel="Lieu d’achat, facultatif" />
      </View>}
      <Action label={busy ? 'Enregistrement…' : 'Enregistrer'} onPress={() => void savePurchase()} disabled={busy || !supplier || !lines.length} />
        {editingPurchase && <MotionPressable onPress={() => { setEditingPurchase(null); setSupplier(''); setLines([]); setLocation(''); setDetailsOpen(false); }} style={styles.cancel}><Text style={styles.cancelText}>Annuler la modification</Text></MotionPressable>}
      </View>
    </FormDisclosure>
    {!!error && <Text style={ui.error}>{error}</Text>}
    {!loading && focusedPurchase && <View style={styles.workflow}>
      <Text style={styles.workflowEyebrow}>{params.step === 'done' ? 'ACHAT TERMINÉ' : 'ÉTAPE SUIVANTE'}</Text>
      <Text style={styles.workflowTitle}>{focusedPurchase.reference}</Text>
      <Text style={styles.workflowText}>{focusedPurchase.statut_paiement === 'paye' && focusedPurchase.lignes.every((line) => line.quantite_recue >= line.quantite)
        ? 'Toutes les quantités sont reçues et le paiement est soldé.'
        : focusedPurchase.lignes.some((line) => line.quantite_recue < line.quantite)
          ? 'Saisissez les quantités réellement reçues dans cet achat. Le stock sera mis à jour à la réception.'
          : `Réception terminée. Solde restant : ${Number(focusedPurchase.solde_restant).toLocaleString('fr-FR')} Ar.`}</Text>
    </View>}
    <View style={styles.sectionHeading}><Text style={ui.section}>Historique des achats</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#11645D" style={{ marginVertical: 24 }} /> : purchases.length === 0 ? <Text style={ui.empty}>Aucun achat enregistré.</Text> : visiblePurchases.map((purchase, index) => <FadeIn key={purchase.public_id} delay={Math.min(index * 35, 280)}>
      <View style={[styles.purchase, purchase.public_id === focusedId && styles.purchaseFocused]}>
        <View style={styles.purchaseHeader}><View><Text style={styles.purchaseTitle}>{purchase.reference}</Text><Text style={styles.purchaseSub}>{purchase.nomFournisseur} · {purchase.dateCommande}</Text></View><Text style={styles.badge}>{purchase.statut.replaceAll('_', ' ')}</Text></View>
        {purchase.lignes.map((line) => {
          const restant = line.quantite - line.quantite_recue;
          return <View key={line.product} style={styles.purchaseLine}>
            <View style={{ flex: 1 }}><Text style={styles.lineName}>{line.nomProduit}</Text><Text style={styles.lineDetail}>Reçu {line.quantite_recue} sur {line.quantite} · retourné {line.quantite_retournee}</Text></View>
            {(restant > 0 || (line.quantite_recue - line.quantite_retournee) > 0) && <View style={styles.quantityActions}>
              {restant > 0 && <View style={styles.quantityAction}><Text style={styles.inputLabel}>À recevoir</Text><TextInput style={styles.receiveInput} value={receiveQuantities[purchase.public_id]?.[line.product] || ''} onChangeText={(value) => setReceiveQuantities((current) => ({ ...current, [purchase.public_id]: { ...current[purchase.public_id], [line.product]: value } }))} keyboardType="number-pad" placeholder={`Max. ${restant}`} placeholderTextColor="#526864" accessibilityLabel={`Quantité à recevoir pour ${line.nomProduit}, maximum ${restant}`} />}</View>}
              {(line.quantite_recue - line.quantite_retournee) > 0 && <View style={styles.quantityAction}><Text style={styles.inputLabel}>À retourner</Text><TextInput style={styles.receiveInput} value={returnQuantities[purchase.public_id]?.[line.product] || ''} onChangeText={(value) => setReturnQuantities((current) => ({ ...current, [purchase.public_id]: { ...current[purchase.public_id], [line.product]: value } }))} keyboardType="number-pad" placeholder={`Max. ${line.quantite_recue - line.quantite_retournee}`} placeholderTextColor="#526864" accessibilityLabel={`Quantité à retourner pour ${line.nomProduit}, maximum ${line.quantite_recue - line.quantite_retournee}`} />}</View>}
            </View>}
          </View>;
        })}
        <View style={styles.totals}><Text style={styles.totalLabel}>Total {Number(purchase.montant_total).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalLabel}>Payé {Number(purchase.montant_paye).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalValue}>Reste {Number(purchase.solde_restant).toLocaleString('fr-FR')} Ar</Text></View>
        <Text style={styles.history}>Paiement : {purchase.statut_paiement.replaceAll('_', ' ')}</Text>
        {!!purchase.receptions.length && <Text style={styles.history}>{purchase.receptions.length} réception(s) · dernière : {purchase.receptions[0].date}</Text>}
        {purchase.paiements.map((payment) => <Text style={styles.history} key={payment.public_id}>{payment.date} · {Number(payment.montant).toLocaleString('fr-FR')} Ar · {payment.mode}</Text>)}
        {!!purchase.historique.length && <Text style={styles.history}>Historique : {purchase.historique.map((event) => `${event.evenement} (${event.utilisateur})`).join(' · ')}</Text>}
        {purchase.statut === 'en_attente' && purchase.montant_paye === '0.00' && <MotionPressable onPress={() => editPurchase(purchase)} disabled={busy} style={styles.cancel}><Text style={styles.editText}>Modifier</Text></MotionPressable>}
        {purchase.statut !== 'recu' && purchase.statut !== 'annule' && <View style={styles.actions}><Action label={busy ? '…' : 'Réceptionner'} onPress={() => void receive(purchase)} disabled={busy || !purchase.lignes.some((line) => Number(receiveQuantities[purchase.public_id]?.[line.product]) > 0)} /></View>}
        {purchase.lignes.some((line) => line.quantite_recue > line.quantite_retournee) && purchase.statut !== 'annule' && <View style={styles.actions}><Action label={busy ? '…' : 'Retourner'} onPress={() => void returnToSupplier(purchase)} disabled={busy || !purchase.lignes.some((line) => Number(returnQuantities[purchase.public_id]?.[line.product]) > 0)} /></View>}
        {Number(purchase.solde_restant) > 0 && purchase.statut !== 'annule' && <View style={styles.paymentBox}><OptionSelect label="Mode de paiement" options={PAYMENT_MODES} value={paymentMode} onChange={setPaymentMode} pageSize={PAYMENT_MODES.length} /><Text style={styles.inputLabel}>Montant versé (Ar)</Text><View style={styles.paymentRow}><TextInput style={[ui.input, styles.paymentInput]} value={paymentAmounts[purchase.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [purchase.public_id]: value }))} keyboardType="decimal-pad" placeholder="0" placeholderTextColor="#526864" accessibilityLabel={`Montant à payer pour l’achat ${purchase.reference}, solde ${purchase.solde_restant} ariary`} /><Action label="Enregistrer le paiement" onPress={() => void pay(purchase)} disabled={busy || !(Number(paymentAmounts[purchase.public_id]) > 0)} /></View></View>}
        {purchase.statut === 'en_attente' && purchase.montant_paye === '0.00' && <MotionPressable onPress={() => void cancel(purchase)} disabled={busy} style={styles.cancel}><Text style={styles.cancelText}>Annuler</Text></MotionPressable>}
      </View>
    </FadeIn>)}
    {!loading && <ShowMore remaining={purchases.length - purchaseLimit} onPress={() => setPurchaseLimit((current) => current + LIST_PAGE_SIZE)} />}
  </ScrollView>;
}

const styles = StyleSheet.create({
  fieldLabel: { color: '#18332F', fontSize: 14, fontWeight: '600', marginBottom: 6 },
  helper: { color: '#11645D', fontSize: 14, fontWeight: '600', marginBottom: 12 },
  workflow: { padding: 15, marginBottom: 18, borderRadius: 16, borderWidth: 1, borderColor: '#B9DCD4', backgroundColor: '#E5F2EF' },
  workflowEyebrow: { color: '#11645D', fontSize: 11, fontWeight: '700', letterSpacing: 0.5 },
  workflowTitle: { color: '#18332F', fontSize: 17, fontWeight: '700', marginTop: 5 },
  workflowText: { color: '#526864', fontSize: 14, lineHeight: 20, marginTop: 5 },
  detailsToggle: { minHeight: 48, justifyContent: 'center' },
  detailsToggleText: { color: '#11645D', fontSize: 14, fontWeight: '600' },
  detailsBox: { borderLeftWidth: 2, borderLeftColor: '#DCE7E2', paddingLeft: 12, marginBottom: 8 },
  draftLine: { flexDirection: 'row', alignItems: 'center', gap: 10, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingVertical: 10 },
  lineName: { color: '#18332F', fontSize: 13, fontWeight: '700' },
  lineDetail: { color: '#526864', fontSize: 11, marginTop: 3 },
  remove: { color: '#A43D32', fontSize: 11, fontWeight: '700' },
  modeRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12 },
  totalLabel: { color: '#526864', fontSize: 11, fontWeight: '600' },
  totalValue: { color: '#18332F', fontSize: 13, fontWeight: '800' },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  purchase: { backgroundColor: '#FFFFFF', padding: 16, borderColor: '#DCE7E2', borderWidth: 1, borderRadius: 16, marginBottom: 11 },
  purchaseFocused: { borderColor: '#11645D', borderWidth: 2 },
  purchaseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 10 },
  purchaseTitle: { color: '#18332F', fontWeight: '800', fontSize: 14 },
  purchaseSub: { color: '#526864', fontSize: 11, marginTop: 4 },
  badge: { color: '#11645D', backgroundColor: '#E5F2EF', overflow: 'hidden', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 10, fontSize: 12, fontWeight: '800', textTransform: 'capitalize' },
  purchaseLine: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingVertical: 10 },
  quantityActions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  quantityAction: { flex: 1, minWidth: 115 },
  inputLabel: { color: '#526864', fontSize: 13, fontWeight: '600', marginBottom: 4 },
  receiveInput: { minHeight: 44, borderWidth: 1, borderColor: '#D9E0DA', borderRadius: 10, paddingHorizontal: 10, color: '#18332F', fontSize: 15 },
  totals: { gap: 5, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 10 },
  history: { color: '#526864', fontSize: 12, marginTop: 7 },
  actions: { marginTop: 12 },
  paymentRow: { gap: 8, marginTop: 5 },
  paymentBox: { borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 7, marginTop: 10 },
  paymentInput: { width: '100%', marginBottom: 0 },
  cancel: { alignSelf: 'flex-start', marginTop: 12 },
  cancelText: { color: '#A43D32', fontSize: 11, fontWeight: '700' },
  editText: { color: '#11645D', fontSize: 11, fontWeight: '700' },
});
