import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useAuth } from '@/lib/auth-context';
import { api, type Page, type Stock } from '@/lib/api';

type Dashboard = { resume_financier: { chiffre_affaires: string; benefice_net: string; commandes_livrees: number }; alertes_stock: Stock[]; commandes_en_attente: number };
type Pending = { public_id: string; date: string; client: string };
const shortcuts = [
  ['/products', 'Produits', 'Catalogue et tarifs'], ['/stock', 'Stock', 'Quantités et mouvements'], ['/orders', 'Commandes', 'Préparer une vente'], ['/clients', 'Clients', 'Fichier clients'], ['/deliveries', 'Livraisons', 'Suivre les expéditions'], ['/expenses', 'Dépenses', 'Saisir les charges'], ['/reports', 'Rapports', 'Résultats et exports'], ['/profile', 'Mon compte', 'Profil et sécurité'],
] as const;

export default function HomeScreen() {
  const router = useRouter(); const { user, signOut } = useAuth();
  const [summary, setSummary] = useState<Dashboard | null>(null); const [pending, setPending] = useState<Pending[]>([]); const [stock, setStock] = useState<Stock[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;
  const refresh = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [p, s] = await Promise.all([api.get<Pending[] | Page<Pending>>('/dashboard/pending-orders/'), api.get<Stock[]>('/stock/alerts/')]);
      setPending(Array.isArray(p) ? p : p.results); setStock(s);
      if (isAdmin) setSummary(await api.get<Dashboard>('/dashboard/summary/'));
    } catch (e) { setError(e instanceof Error ? e.message : 'Le tableau de bord est indisponible.'); }
    finally { setLoading(false); }
  }, [isAdmin]);
  useEffect(() => { void refresh(); }, [refresh]);
  const disconnect = async () => { try { await signOut(); } finally { router.replace('/'); } };

  return <SafeAreaView style={styles.safe} edges={['top']}><StatusBar style="dark"/><ScrollView contentContainerStyle={styles.content}>
    <View style={styles.header}><View><Text style={styles.brand}>FLOWSTOCK</Text><Text style={styles.greeting}>Bonjour{user?.nom_complet ? `, ${user.nom_complet.split(' ')[0]}` : ''}</Text><Text style={styles.role}>{user?.role === 'ADMIN' ? 'Administrateur' : 'Vendeur'} · {user?.email}</Text></View><Pressable onPress={disconnect} style={styles.logout}><Text style={styles.logoutText}>Quitter</Text></Pressable></View>
    <View style={styles.hello}><Text style={styles.helloTitle}>Votre activité, en un coup d’œil</Text><Text style={styles.helloSub}>Données actualisées depuis l’API FlowStock.</Text></View>
    {!!error && <Text style={styles.error}>{error}</Text>}
    {loading ? <ActivityIndicator color="#078343" size="large" style={{ margin: 30 }} /> : <>
      <View style={styles.stats}>
        <Stat label="Commandes en attente" value={String(pending.length)} hint="À traiter"/>
        <Stat label="Alertes de stock" value={String(stock.length)} hint="Sous le seuil"/>
        {isAdmin && summary && <><Stat label="Chiffre d’affaires" value={`${Number(summary.resume_financier.chiffre_affaires).toLocaleString('fr-FR')} Ar`} hint="Mois en cours"/><Stat label="Bénéfice net" value={`${Number(summary.resume_financier.benefice_net).toLocaleString('fr-FR')} Ar`} hint="Après dépenses"/></>}
      </View>
      {stock.length > 0 && <Pressable onPress={() => router.push('/stock')} style={styles.alert}><Text style={styles.alertTitle}>⚠ Stock à surveiller</Text><Text style={styles.alertText}>{stock.slice(0, 3).map((p) => `${p.nomProduit} (${p.stock}/${p.seuilAlerte})`).join(' · ')}</Text></Pressable>}
      <Text style={styles.section}>Gérer l’activité</Text><View style={styles.grid}>{shortcuts.filter(([route]) => isAdmin || route !== '/expenses' && route !== '/reports').map(([route, title, detail]) => <Pressable key={route} onPress={() => router.push(route)} style={({ pressed }) => [styles.tile, pressed && { opacity: .85 }]}><View style={styles.tileIcon}><Text style={styles.tileInitial}>{title[0]}</Text></View><Text style={styles.tileTitle}>{title}</Text><Text style={styles.tileDetail}>{detail}</Text><Text style={styles.chevron}>›</Text></Pressable>)}</View>
    </>}
    <Pressable onPress={() => void refresh()} style={styles.refresh}><Text style={styles.refreshText}>Actualiser les données</Text></Pressable>
  </ScrollView></SafeAreaView>;
}
function Stat({ label, value, hint }: { label: string; value: string; hint: string }) { return <View style={styles.stat}><Text style={styles.statLabel}>{label}</Text><Text style={styles.statValue} numberOfLines={1}>{value}</Text><Text style={styles.statHint}>{hint}</Text></View>; }
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: '#F5F7F5' }, content: { width: '100%', maxWidth: 720, alignSelf: 'center', padding: 20, paddingBottom: 48 }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }, brand: { color: '#078343', fontSize: 11, fontWeight: '800', letterSpacing: 2 }, greeting: { color: '#142039', fontSize: 27, fontWeight: '800', marginTop: 6 }, role: { color: '#778078', fontSize: 12, marginTop: 3 }, logout: { borderColor: '#DDE5DE', borderWidth: 1, borderRadius: 11, paddingVertical: 9, paddingHorizontal: 13 }, logoutText: { color: '#525D55', fontWeight: '700' }, hello: { backgroundColor: '#078343', borderRadius: 19, padding: 20, marginTop: 23, marginBottom: 16 }, helloTitle: { color: '#fff', fontWeight: '800', fontSize: 18 }, helloSub: { color: '#D8F1E1', fontSize: 13, marginTop: 5 }, stats: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 }, stat: { flexGrow: 1, flexBasis: '45%', backgroundColor: '#fff', borderRadius: 16, padding: 15, borderWidth: 1, borderColor: '#E6EBE6' }, statLabel: { color: '#66716A', fontSize: 12 }, statValue: { color: '#142039', fontWeight: '800', fontSize: 21, marginTop: 7 }, statHint: { color: '#89938C', fontSize: 11, marginTop: 3 }, alert: { backgroundColor: '#FFF7E7', borderColor: '#F1DFAF', borderWidth: 1, borderRadius: 14, padding: 14, marginTop: 12 }, alertTitle: { color: '#7A5811', fontWeight: '800' }, alertText: { color: '#806925', fontSize: 12, marginTop: 5 }, section: { color: '#142039', fontWeight: '800', fontSize: 19, marginTop: 24, marginBottom: 12 }, grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 }, tile: { width: '48%', flexGrow: 1, minHeight: 130, borderRadius: 16, padding: 15, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E6EBE6' }, tileIcon: { width: 31, height: 31, borderRadius: 10, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' }, tileInitial: { color: '#078343', fontWeight: '800' }, tileTitle: { color: '#142039', fontWeight: '800', marginTop: 10 }, tileDetail: { color: '#758079', fontSize: 11, marginTop: 4 }, chevron: { position: 'absolute', right: 13, top: 17, color: '#078343', fontSize: 20 }, error: { color: '#A33B31', marginVertical: 10 }, refresh: { alignSelf: 'center', padding: 15, marginTop: 10 }, refreshText: { color: '#078343', fontWeight: '700' } });
