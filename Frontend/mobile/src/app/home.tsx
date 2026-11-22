import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useAuth } from '@/lib/auth-context';
import { api, type Page, type Stock } from '@/lib/session-api';

type Dashboard = { resume_financier: { chiffre_affaires: string; benefice_net: string; commandes_livrees: number }; alertes_stock: Stock[]; commandes_en_attente: number };
type Pending = { public_id: string; date: string; client: string };
const shortcuts = [
  ['/products', 'Produits', 'Catalogue et tarifs'], ['/categories', 'Catégories', 'Classer les produits'], ['/suppliers', 'Fournisseurs', 'Gérer les approvisionneurs'], ['/stock', 'Stock', 'Quantités et mouvements'], ['/orders', 'Commandes', 'Préparer une vente'], ['/clients', 'Clients', 'Fichier clients'], ['/deliveries', 'Livraisons', 'Suivre les expéditions'], ['/expenses', 'Dépenses', 'Saisir les charges'], ['/reports', 'Rapports', 'Résultats et exports'], ['/profile', 'Mon compte', 'Profil et sécurité'],
] as const;

export default function HomeScreen() {
  const router = useRouter(); const { user, isReady, signOut } = useAuth();
  const [summary, setSummary] = useState<Dashboard | null>(null); const [pending, setPending] = useState<Pending[]>([]); const [stock, setStock] = useState<Stock[]>([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('');
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;
  useEffect(() => {
    if (isReady && !user) router.replace('/');
  }, [isReady, router, user]);
  const refresh = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [p, s] = await Promise.all([api.get<Pending[] | Page<Pending>>('/dashboard/pending-orders/'), api.get<Stock[]>('/stock/alerts/')]);
      setPending(Array.isArray(p) ? p : p.results); setStock(s);
      if (isAdmin) setSummary(await api.get<Dashboard>('/dashboard/summary/'));
    } catch (e) { setError(e instanceof Error ? e.message : 'Le tableau de bord est indisponible.'); }
    finally { setLoading(false); }
  }, [isAdmin]);
  useEffect(() => { if (isReady && user) void refresh(); }, [isReady, refresh, user]);
  const disconnect = async () => { try { await signOut(); } finally { router.replace('/'); } };

  if (!isReady || !user) return <SafeAreaView style={styles.safe}><ActivityIndicator color="#078343" size="large" style={{ flex: 1 }} /></SafeAreaView>;
  return <SafeAreaView style={styles.safe} edges={['top']}><StatusBar style="dark"/><ScrollView contentContainerStyle={styles.content}>
    <View style={styles.header}><View><Text style={styles.greeting}>Bonjour{user?.nom_complet ? `, ${user.nom_complet.split(' ')[0]}` : ''}</Text><Text style={styles.role}>{user?.role === 'ADMIN' ? 'Administrateur' : 'Vendeur'} · {user?.email}</Text></View><Pressable onPress={disconnect} style={styles.logout}><Text style={styles.logoutText}>Quitter</Text></Pressable></View>
    <View style={styles.hello}><View style={styles.helloTop}><View style={styles.live}><View style={styles.liveDot}/><Text style={styles.liveText}>ESPACE DE GESTION</Text></View><Text style={styles.helloMark}>FS</Text></View><Text style={styles.helloTitle}>Votre activité, en un coup d’œil</Text><Text style={styles.helloSub}>Un aperçu à jour de votre stock et de vos ventes.</Text></View>
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
function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  const mark = label === 'Chiffre d’affaires' ? 'CA' : label === 'Bénéfice net' ? 'BN' : label === 'Alertes de stock' ? 'ST' : 'CO';
  return <View style={styles.stat}><View style={styles.statTop}><Text style={styles.statLabel}>{label}</Text><View style={styles.statMark}><Text style={styles.statMarkText}>{mark}</Text></View></View><Text style={styles.statValue} numberOfLines={1}>{value}</Text><Text style={styles.statHint}>{hint}</Text></View>;
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: '#F5F7F5' }, content: { width: '100%', maxWidth: 1080, alignSelf: 'center', paddingHorizontal: 24, paddingTop: 27, paddingBottom: 64 }, header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }, greeting: { color: '#142039', fontSize: 27, fontWeight: '800' }, role: { color: '#778078', fontSize: 12, marginTop: 4 }, logout: { borderColor: '#DDE5DE', borderWidth: 1, borderRadius: 11, paddingVertical: 9, paddingHorizontal: 13, backgroundColor: '#FFFFFF' }, logoutText: { color: '#525D55', fontWeight: '700' }, hello: { backgroundColor: '#078343', borderRadius: 20, paddingHorizontal: 23, paddingVertical: 21, marginTop: 22, marginBottom: 17, minHeight: 152, overflow: 'hidden' }, helloTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 17 }, live: { flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: '#FFFFFF22', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20 }, liveDot: { width: 6, height: 6, borderRadius: 4, backgroundColor: '#D8F1E1' }, liveText: { color: '#D8F1E1', fontSize: 9, fontWeight: '800', letterSpacing: 1 }, helloMark: { color: '#D8F1E1', fontSize: 16, fontWeight: '900', opacity: .8 }, helloTitle: { color: '#fff', fontWeight: '800', fontSize: 22 }, helloSub: { color: '#D8F1E1', fontSize: 13, marginTop: 6 }, stats: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, stat: { flexGrow: 1, flexBasis: 205, backgroundColor: '#fff', borderRadius: 17, padding: 17, borderWidth: 1, borderColor: '#E6EBE6', minHeight: 126 }, statTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 }, statMark: { width: 30, height: 30, borderRadius: 10, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' }, statMarkText: { color: '#078343', fontSize: 9, fontWeight: '900' }, statLabel: { color: '#66716A', fontSize: 12, fontWeight: '600' }, statValue: { color: '#142039', fontWeight: '800', fontSize: 21, marginTop: 10 }, statHint: { color: '#89938C', fontSize: 11, marginTop: 4 }, alert: { backgroundColor: '#FFF7E7', borderColor: '#F1DFAF', borderWidth: 1, borderRadius: 15, padding: 16, marginTop: 13 }, alertTitle: { color: '#7A5811', fontWeight: '800' }, alertText: { color: '#806925', fontSize: 12, marginTop: 6 }, section: { color: '#142039', fontWeight: '800', fontSize: 19, marginTop: 27, marginBottom: 13 }, grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 }, tile: { width: '31%', flexGrow: 1, minWidth: 205, minHeight: 134, borderRadius: 17, padding: 17, backgroundColor: '#fff', borderWidth: 1, borderColor: '#E6EBE6' }, tileIcon: { width: 34, height: 34, borderRadius: 11, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' }, tileInitial: { color: '#078343', fontWeight: '800' }, tileTitle: { color: '#142039', fontWeight: '800', marginTop: 11, fontSize: 14 }, tileDetail: { color: '#758079', fontSize: 11, marginTop: 5 }, chevron: { position: 'absolute', right: 15, top: 17, color: '#078343', fontSize: 20 }, error: { color: '#A33B31', marginVertical: 10, padding: 12, backgroundColor: '#FCEBE9', borderRadius: 10 }, refresh: { alignSelf: 'center', padding: 15, marginTop: 10 }, refreshText: { color: '#078343', fontWeight: '700' } });
