import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';
import { useAuth } from '@/lib/auth-context';
import { api, type Page, type Produit, type Fournisseur, type Purchase } from '@/lib/session-api';

type DraftLine = { product: string; quantity: string; unit_price: string };
const PAYMENT_MODES = [
  { value: 'especes', label: 'Espèces' }, { value: 'mvola', label: 'MVola' },
  { value: 'orange_money', label: 'Orange Money' }, { value: 'airtel_money', label: 'Airtel Money' },
  { value: 'virement', label: 'Virement' }, { value: 'autre', label: 'Autre' },
];

export default function PurchasesScreen() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;
  const [purchases, setPurchases] = useState<Purchase[]>([]);
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
      const [purchasesResult, suppliersResult, productsResult] = await Promise.all([
        api.get<Page<Purchase> | Purchase[]>('/purchases/'),
        api.get<Page<Fournisseur> | Fournisseur[]>('/suppliers/'),
        api.get<Page<Produit> | Produit[]>('/products/', { active: true }),
      ]);
      setPurchases(Array.isArray(purchasesResult) ? purchasesResult : purchasesResult.results);
      setSuppliers(Array.isArray(suppliersResult) ? suppliersResult : suppliersResult.results);
      setProducts(Array.isArray(productsResult) ? productsResult : productsResult.results);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chargement des achats impossible.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

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
      if (editingPurchase) await api.patch(`/purchases/${editingPurchase.public_id}/`, payload);
      else await api.post('/purchases/', payload);
      setSupplier(''); setLines([]); setLocation(''); setEditingPurchase(null); setObtention('commande');
      await load();
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

  if (!isAdmin) return <ScrollView style={ui.page} contentContainerStyle={ui.content}><AppPageHeading title="Achats" subtitle="Cette section est réservée aux administrateurs." /></ScrollView>;

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Achats" subtitle="Commandez auprès de vos fournisseurs et réceptionnez les produits en plusieurs fois." />
    <FadeIn delay={120}><View style={ui.card}>
      <Text style={ui.cardTitle}>{editingPurchase ? `Modifier ${editingPurchase.reference}` : 'Nouvel achat'}</Text>
      <Text style={styles.label}>Fournisseur</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>
        {suppliers.map((item) => <Choice key={item.public_id} label={item.nomFournisseur} selected={supplier === item.public_id} onPress={() => setSupplier(item.public_id)} />)}
      </ScrollView>
      <Text style={styles.label}>Mode d’obtention</Text>
      <View style={styles.choices}><Choice label="Commande" selected={obtention === 'commande'} onPress={() => setObtention('commande')} /><Choice label="Achat direct" selected={obtention === 'achat_direct'} onPress={() => setObtention('achat_direct')} /></View>
      <TextInput style={ui.input} value={location} onChangeText={setLocation} placeholder="Lieu d’achat (facultatif)" />
      <Text style={styles.label}>Ajouter un produit</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>
        {products.map((item) => <Choice key={item.public_id} label={item.nomProduit} selected={selectedProduct === item.public_id} onPress={() => { setSelectedProduct(item.public_id); setUnitPrice(item.prixAchat || '0'); }} />)}
      </ScrollView>
      <View style={styles.inlineInputs}><TextInput style={[ui.input, styles.numberInput]} value={quantity} onChangeText={setQuantity} keyboardType="number-pad" placeholder="Quantité" /><TextInput style={[ui.input, styles.numberInput]} value={unitPrice} onChangeText={setUnitPrice} keyboardType="decimal-pad" placeholder="Prix unitaire (Ar)" /></View>
      <Action label="Ajouter à l’achat" onPress={addLine} />
      {lines.map((line) => <View style={styles.draftLine} key={line.product}><Text style={styles.lineName}>{products.find((p) => p.public_id === line.product)?.nomProduit}</Text><Text style={styles.lineDetail}>{line.quantity} × {line.unit_price} Ar</Text><MotionPressable onPress={() => setLines((current) => current.filter((item) => item.product !== line.product))}><Text style={styles.remove}>Retirer</Text></MotionPressable></View>)}
      <View style={styles.modeRow}><Text style={styles.totalLabel}>Total prévu</Text><Text style={styles.totalValue}>{lines.reduce((sum, line) => sum + Number(line.quantity) * Number(line.unit_price), 0).toLocaleString('fr-FR')} Ar</Text></View>
      <Action label={busy ? 'Enregistrement…' : editingPurchase ? 'Enregistrer les modifications' : 'Créer l’achat'} onPress={() => void savePurchase()} disabled={busy || !lines.length} />
      {editingPurchase && <MotionPressable onPress={() => { setEditingPurchase(null); setSupplier(''); setLines([]); setLocation(''); }} style={styles.cancel}><Text style={styles.cancelText}>Quitter la modification</Text></MotionPressable>}
    </View></FadeIn>
    {!!error && <Text style={ui.error}>{error}</Text>}
    <View style={styles.sectionHeading}><Text style={ui.section}>Historique des achats</Text><MotionPressable onPress={() => void load()}><Text style={ui.refresh}>Actualiser</Text></MotionPressable></View>
    {loading ? <ActivityIndicator color="#078343" style={{ marginVertical: 24 }} /> : purchases.length === 0 ? <Text style={ui.empty}>Aucun achat enregistré.</Text> : purchases.map((purchase, index) => <FadeIn key={purchase.public_id} delay={Math.min(index * 35, 280)}>
      <View style={styles.purchase}>
        <View style={styles.purchaseHeader}><View><Text style={styles.purchaseTitle}>{purchase.reference}</Text><Text style={styles.purchaseSub}>{purchase.nomFournisseur} · {purchase.dateCommande}</Text></View><Text style={styles.badge}>{purchase.statut.replaceAll('_', ' ')}</Text></View>
        {purchase.lignes.map((line) => {
          const restant = line.quantite - line.quantite_recue;
          return <View key={line.product} style={styles.purchaseLine}>
            <View style={{ flex: 1 }}><Text style={styles.lineName}>{line.nomProduit}</Text><Text style={styles.lineDetail}>Reçu {line.quantite_recue} / {line.quantite} · retourné {line.quantite_retournee} · {line.prixUnitaire} Ar</Text></View>
            {restant > 0 && <TextInput style={styles.receiveInput} value={receiveQuantities[purchase.public_id]?.[line.product] || ''} onChangeText={(value) => setReceiveQuantities((current) => ({ ...current, [purchase.public_id]: { ...current[purchase.public_id], [line.product]: value } }))} keyboardType="number-pad" placeholder={`≤ ${restant}`} />}
            {(line.quantite_recue - line.quantite_retournee) > 0 && <TextInput style={styles.receiveInput} value={returnQuantities[purchase.public_id]?.[line.product] || ''} onChangeText={(value) => setReturnQuantities((current) => ({ ...current, [purchase.public_id]: { ...current[purchase.public_id], [line.product]: value } }))} keyboardType="number-pad" placeholder={`retour ≤ ${line.quantite_recue - line.quantite_retournee}`} />}
          </View>;
        })}
        <View style={styles.totals}><Text style={styles.totalLabel}>Total {Number(purchase.montant_total).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalLabel}>Payé {Number(purchase.montant_paye).toLocaleString('fr-FR')} Ar</Text><Text style={styles.totalValue}>Reste {Number(purchase.solde_restant).toLocaleString('fr-FR')} Ar</Text></View>
        <Text style={styles.history}>Paiement : {purchase.statut_paiement.replaceAll('_', ' ')}</Text>
        {!!purchase.receptions.length && <Text style={styles.history}>{purchase.receptions.length} réception(s) · dernière : {purchase.receptions[0].date}</Text>}
        {purchase.paiements.map((payment) => <Text style={styles.history} key={payment.public_id}>{payment.date} · {Number(payment.montant).toLocaleString('fr-FR')} Ar · {payment.mode}</Text>)}
        {!!purchase.historique.length && <Text style={styles.history}>Historique : {purchase.historique.map((event) => `${event.evenement} (${event.utilisateur})`).join(' · ')}</Text>}
        {purchase.statut === 'en_attente' && purchase.montant_paye === '0.00' && <MotionPressable onPress={() => editPurchase(purchase)} disabled={busy} style={styles.cancel}><Text style={styles.editText}>Modifier l’achat</Text></MotionPressable>}
        {purchase.statut !== 'recu' && purchase.statut !== 'annule' && <View style={styles.actions}><Action label={busy ? '…' : 'Enregistrer la réception'} onPress={() => void receive(purchase)} disabled={busy} /></View>}
        {purchase.lignes.some((line) => line.quantite_recue > line.quantite_retournee) && purchase.statut !== 'annule' && <View style={styles.actions}><Action label={busy ? '…' : 'Retourner au fournisseur'} onPress={() => void returnToSupplier(purchase)} disabled={busy} /></View>}
        {Number(purchase.solde_restant) > 0 && purchase.statut !== 'annule' && <View style={styles.paymentBox}><Text style={styles.label}>Enregistrer un paiement fournisseur</Text><ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.choices}>{PAYMENT_MODES.map((mode) => <Choice key={mode.value} label={mode.label} selected={paymentMode === mode.value} onPress={() => setPaymentMode(mode.value)} />)}</ScrollView><View style={styles.paymentRow}><TextInput style={[ui.input, styles.paymentInput]} value={paymentAmounts[purchase.public_id] || ''} onChangeText={(value) => setPaymentAmounts((current) => ({ ...current, [purchase.public_id]: value }))} keyboardType="decimal-pad" placeholder="Montant versé (Ar)" /><Action label="Ajouter paiement" onPress={() => void pay(purchase)} disabled={busy} /></View></View>}
        {purchase.statut === 'en_attente' && purchase.montant_paye === '0.00' && <MotionPressable onPress={() => void cancel(purchase)} disabled={busy} style={styles.cancel}><Text style={styles.cancelText}>Annuler l’achat</Text></MotionPressable>}
      </View>
    </FadeIn>)}
  </ScrollView>;
}

function Choice({ label, selected, onPress }: { label: string; selected: boolean; onPress: () => void }) {
  return <MotionPressable onPress={onPress} style={[styles.choice, selected && styles.choiceSelected]}><Text style={[styles.choiceText, selected && styles.choiceTextSelected]}>{label}</Text></MotionPressable>;
}

const styles = StyleSheet.create({
  label: { color: '#68736B', fontSize: 12, marginTop: 7, marginBottom: 8 },
  choices: { flexDirection: 'row', gap: 8, paddingBottom: 8 },
  choice: { paddingVertical: 9, paddingHorizontal: 12, borderRadius: 11, backgroundColor: '#F0F4F1' },
  choiceSelected: { backgroundColor: '#078343' },
  choiceText: { color: '#465149', fontSize: 12, fontWeight: '600' },
  choiceTextSelected: { color: '#FFFFFF' },
  inlineInputs: { flexDirection: 'row', gap: 9 },
  numberInput: { flex: 1, minWidth: 0 },
  draftLine: { flexDirection: 'row', alignItems: 'center', gap: 10, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingVertical: 10 },
  lineName: { color: '#173D2B', fontSize: 13, fontWeight: '700' },
  lineDetail: { color: '#77827A', fontSize: 11, marginTop: 3 },
  remove: { color: '#B63838', fontSize: 11, fontWeight: '700' },
  modeRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12 },
  totalLabel: { color: '#69756D', fontSize: 11, fontWeight: '600' },
  totalValue: { color: '#173D2B', fontSize: 13, fontWeight: '800' },
  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  purchase: { backgroundColor: '#FFFFFF', padding: 16, borderColor: '#DDE9DF', borderWidth: 1, borderRadius: 16, marginBottom: 11 },
  purchaseHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 10 },
  purchaseTitle: { color: '#173D2B', fontWeight: '800', fontSize: 14 },
  purchaseSub: { color: '#77827A', fontSize: 11, marginTop: 4 },
  badge: { color: '#078343', backgroundColor: '#E7F5EC', overflow: 'hidden', paddingHorizontal: 9, paddingVertical: 5, borderRadius: 10, fontSize: 10, fontWeight: '800', textTransform: 'capitalize' },
  purchaseLine: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingVertical: 10 },
  receiveInput: { width: 78, height: 42, borderWidth: 1, borderColor: '#D9E0DA', borderRadius: 10, paddingHorizontal: 9, textAlign: 'center', color: '#142039' },
  totals: { gap: 5, borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 10 },
  history: { color: '#77827A', fontSize: 10, marginTop: 7 },
  actions: { marginTop: 12 },
  paymentRow: { flexDirection: 'row', alignItems: 'center', gap: 9, marginTop: 9 },
  paymentBox: { borderTopWidth: 1, borderTopColor: '#EEF2EE', paddingTop: 7, marginTop: 10 },
  paymentInput: { flex: 1, minWidth: 0, marginBottom: 0 },
  cancel: { alignSelf: 'flex-start', marginTop: 12 },
  cancelText: { color: '#B63838', fontSize: 11, fontWeight: '700' },
  editText: { color: '#078343', fontSize: 11, fontWeight: '700' },
});
