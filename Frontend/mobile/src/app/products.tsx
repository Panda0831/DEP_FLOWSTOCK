import { useEffect, useMemo, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { ResourceScreen, type ResourceItem } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
import { api, fetchAll, type Categorie, type Fournisseur, type Stock } from '@/lib/session-api';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

export default function ProductsScreen() {
  const router = useRouter();
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const params = useLocalSearchParams<{ flow?: string; client?: string; supplier?: string }>();
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  const [categories, setCategories] = useState<Categorie[]>([]);
  const [suppliers, setSuppliers] = useState<Fournisseur[]>([]);
  const [stock, setStock] = useState<Stock[]>([]);

  useEffect(() => {
    let active = true;
    Promise.all([
      admin ? fetchAll<Categorie>('/categories/') : Promise.resolve([] as Categorie[]),
      admin ? fetchAll<Fournisseur>('/suppliers/') : Promise.resolve([] as Fournisseur[]),
      api.get<Stock[]>('/stock/'),
    ])
      .then(([categoryList, supplierList, stockList]) => {
        if (!active) return;
        setCategories(categoryList);
        setSuppliers(supplierList);
        setStock(stockList);
      })
      .catch(() => { if (active) { setCategories([]); setSuppliers([]); setStock([]); } });
    return () => { active = false; };
  }, [admin]);

  const totalUnits = stock.reduce((sum, item) => sum + item.stock, 0);
  const lowCount = stock.filter((item) => item.stock <= item.seuilAlerte).length;
  const summary = <View style={styles.summary}>
    <View style={styles.summaryCard}><Text style={styles.summaryLabel}>Références</Text><Text style={styles.summaryValue}>{stock.length}</Text></View>
    <View style={styles.summaryCard}><Text style={styles.summaryLabel}>Unités en stock</Text><Text style={styles.summaryValue}>{totalUnits.toLocaleString('fr-FR')}</Text></View>
    <View style={[styles.summaryCard, lowCount > 0 && styles.alertCard]}><Text style={styles.summaryLabel}>À réapprovisionner</Text><Text style={[styles.summaryValue, lowCount > 0 && styles.alertValue]}>{lowCount}</Text></View>
  </View>;

  const productMetric = (item: ResourceItem) => {
    const inventory = stock.find((entry) => entry.public_id === item.public_id);
    const amount = inventory?.stock ?? 0;
    const warning = !inventory || amount <= (inventory?.seuilAlerte ?? Number(item.seuilAlerte || 0));
    return { value: String(amount), label: warning ? 'À réapprovisionner' : 'en stock', warning };
  };

  return <ResourceScreen
    title="Produits"
    subtitle="Gérez les articles, leurs prix et leurs niveaux d’alerte."
    endpoint="/products/"
    titleKey="nomProduit"
    subtitleKeys={['prixVente', 'seuilAlerte']}
    listTitle="Produits du catalogue"
    emptyText="Aucun produit dans le catalogue pour le moment."
    itemMarker="PRD"
    canEdit={!!admin}
    searchable
    summary={summary}
    itemMetric={productMetric}
    onCreated={(item) => {
      if (params.flow === 'purchase') {
        router.replace({
          pathname: '/purchases',
          params: { add: '1', product: item.public_id, ...(typeof params.supplier === 'string' ? { supplier: params.supplier } : {}) },
        });
      } else {
        router.replace({
          pathname: '/stock/new',
          params: {
            product: item.public_id,
            ...(params.flow === 'order' ? {
              returnTo: 'order',
              ...(typeof params.client === 'string' ? { client: params.client } : {}),
            } : {}),
          },
        });
      }
    }}
    fields={[
      { key: 'nomProduit', label: 'Nom du produit', placeholder: 'Ex. Café moulu' },
      { key: 'prixVente', label: 'Prix de vente (Ar)', placeholder: '0', keyboardType: 'decimal-pad', hint: 'Montant en ariary.' },
      ...(admin ? [{ key: 'prixAchat', label: 'Prix d’achat (Ar)', placeholder: '0', keyboardType: 'decimal-pad' as const, hint: 'Montant en ariary.' }] : []),
      { key: 'seuilAlerte', label: 'Seuil de réapprovisionnement', placeholder: 'Ex. 5', keyboardType: 'number-pad', hint: 'Une alerte apparaît quand le stock atteint cette quantité.' },
      { key: 'idCategorie', label: 'Catégorie', optional: true, clearToNull: true, options: categories.map((item) => ({ value: item.public_id, label: item.nomCategorie || 'Catégorie' })) },
      { key: 'idFournisseur', label: 'Fournisseur', optional: true, clearToNull: true, options: suppliers.map((item) => ({ value: item.public_id, label: item.nomFournisseur || 'Fournisseur' })) },
    ]} />;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  summary: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: -6, marginBottom: 18 },
  summaryCard: { flexGrow: 1, flexBasis: 100, minHeight: 78, justifyContent: 'center', backgroundColor: t.surface, borderWidth: 1, borderColor: t.separator, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 10 },
  alertCard: { backgroundColor: t.warningSurface, borderColor: t.warningSurface },
  summaryLabel: { color: t.secondaryText, fontSize: 11, fontWeight: '600' },
  summaryValue: { color: t.text, fontSize: 20, fontWeight: '700', marginTop: 4 },
  alertValue: { color: t.warning },
});
