import { usePathname, useRouter } from 'expo-router';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useAuth } from '@/lib/auth-context';

const primaryLinks = [
  { label: 'Vue générale', href: '/home', matches: ['/home'] },
  { label: 'Catalogue', href: '/products', matches: ['/products', '/categories', '/suppliers'] },
  { label: 'Opérations', href: '/orders', matches: ['/orders', '/clients', '/deliveries', '/stock'] },
  { label: 'Finances', href: '/reports', matches: ['/reports', '/expenses'], admin: true },
  { label: 'Compte', href: '/profile', matches: ['/profile', '/change-password'], admin: false },
] as const;

const sectionLinks = [
  { label: 'Tableau de bord', href: '/home', admin: false },
  { label: 'Produits', href: '/products', admin: false },
  { label: 'Catégories', href: '/categories', admin: false },
  { label: 'Fournisseurs', href: '/suppliers', admin: false },
  { label: 'Stock', href: '/stock', admin: false },
  { label: 'Commandes', href: '/orders', admin: false },
  { label: 'Clients', href: '/clients', admin: false },
  { label: 'Livraisons', href: '/deliveries', admin: false },
  { label: 'Dépenses', href: '/expenses', admin: true },
  { label: 'Rapports', href: '/reports', admin: true },
  { label: 'Mon compte', href: '/profile', admin: false },
] as const;

export function AppNavigation() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;

  if (!user || pathname === '/' || pathname === '/signup' || pathname === '/reset-password') return null;

  const visiblePrimary = primaryLinks.filter((link) => !('admin' in link && link.admin && !isAdmin));
  const visibleSections = sectionLinks.filter((link) => !link.admin || isAdmin);
  const activePrimary = visiblePrimary.find((link) => link.matches.some((path) => pathname === path || pathname.startsWith(`${path}/`)));

  return (
    <View style={styles.shell}>
      <View style={styles.inner}>
        <View style={styles.brandRow}>
          <View style={styles.brandMark}><Text style={styles.brandLetter}>F</Text></View>
          <View style={styles.brandCopy}>
            <Text style={styles.brand}>FLOWSTOCK</Text>
            <Text style={styles.caption}>Gestion de votre activité</Text>
          </View>
          <Text style={styles.userName} numberOfLines={1}>{user.nom_complet || user.email}</Text>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.primaryRow}>
          {visiblePrimary.map((link) => {
            const active = activePrimary?.label === link.label;
            return <Pressable key={link.label} onPress={() => router.push(link.href)} style={[styles.primaryItem, active && styles.primaryActive]}>
              <Text style={[styles.primaryText, active && styles.primaryTextActive]}>{link.label}</Text>
            </Pressable>;
          })}
        </ScrollView>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.sectionRow}>
          {visibleSections.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return <Pressable key={link.href} onPress={() => router.push(link.href)} style={styles.sectionItem}>
              <Text style={[styles.sectionText, active && styles.sectionTextActive]}>{link.label}</Text>
              {active && <View style={styles.activeMark} />}
            </Pressable>;
          })}
        </ScrollView>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { zIndex: 10, width: '100%', backgroundColor: '#FFFFFF', borderBottomWidth: 1, borderBottomColor: '#E3E9E4' },
  inner: { width: '100%', maxWidth: 1200, alignSelf: 'center', paddingHorizontal: 20 },
  brandRow: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 11 },
  brandMark: { width: 34, height: 34, borderRadius: 11, alignItems: 'center', justifyContent: 'center', backgroundColor: '#078343' },
  brandLetter: { color: '#FFFFFF', fontSize: 18, fontWeight: '900' },
  brandCopy: { gap: 1 },
  brand: { color: '#142039', fontSize: 12, fontWeight: '900', letterSpacing: 1.3 },
  caption: { color: '#758079', fontSize: 10 },
  userName: { marginLeft: 'auto', color: '#657064', fontSize: 12, fontWeight: '600', maxWidth: 190 },
  primaryRow: { gap: 7, alignItems: 'center', paddingBottom: 8 },
  primaryItem: { paddingHorizontal: 15, paddingVertical: 9, borderRadius: 10, backgroundColor: '#F4F7F4' },
  primaryActive: { backgroundColor: '#078343' },
  primaryText: { color: '#526057', fontWeight: '700', fontSize: 12 },
  primaryTextActive: { color: '#FFFFFF' },
  sectionRow: { gap: 22, alignItems: 'center', minHeight: 39, paddingHorizontal: 2 },
  sectionItem: { height: 39, justifyContent: 'center', position: 'relative' },
  sectionText: { color: '#78827B', fontSize: 12, fontWeight: '600' },
  sectionTextActive: { color: '#078343', fontWeight: '800' },
  activeMark: { position: 'absolute', left: 0, right: 0, bottom: 0, height: 2, borderRadius: 2, backgroundColor: '#078343' },
});
