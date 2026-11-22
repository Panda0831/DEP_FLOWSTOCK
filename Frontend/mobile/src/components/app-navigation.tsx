import { usePathname, useRouter } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useAuth } from '@/lib/auth-context';

const primaryLinks = [
  { label: 'Accueil', shortLabel: 'Accueil', href: '/home', matches: ['/home'], icon: { ios: 'house.fill', android: 'home', web: 'home' } },
  { label: 'Catalogue', shortLabel: 'Catalogue', href: '/products', matches: ['/products', '/categories', '/suppliers'], icon: { ios: 'square.grid.2x2.fill', android: 'grid_view', web: 'grid_view' } },
  { label: 'Activité', shortLabel: 'Activité', href: '/orders', matches: ['/orders', '/clients', '/deliveries', '/stock'], icon: { ios: 'arrow.left.arrow.right', android: 'swap_horiz', web: 'swap_horiz' } },
  { label: 'Finances', shortLabel: 'Finances', href: '/reports', matches: ['/reports', '/expenses'], admin: true, icon: { ios: 'chart.bar.fill', android: 'bar_chart', web: 'bar_chart' } },
  { label: 'Compte', shortLabel: 'Compte', href: '/profile', matches: ['/profile', '/change-password'], icon: { ios: 'person.crop.circle.fill', android: 'account_circle', web: 'account_circle' } },
] as const;

const sectionLinks = [
  { label: 'Vue générale', href: '/home', admin: false },
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
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;

  if (!user || pathname === '/' || pathname === '/signup' || pathname === '/reset-password') return null;

  const visiblePrimary = primaryLinks.filter((link) => !('admin' in link && link.admin && !isAdmin));
  const visibleSections = sectionLinks.filter((link) => !link.admin || isAdmin);
  const activePrimary = visiblePrimary.find((link) => link.matches.some((path) => pathname === path || pathname.startsWith(`${path}/`)));

  return (
    <View style={[styles.shell, { paddingBottom: Math.max(insets.bottom, 10) }]}>
      <View style={styles.inner}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.sectionRow}>
          {visibleSections.map((link) => {
            const active = pathname === link.href || pathname.startsWith(`${link.href}/`);
            return <Pressable key={link.href} onPress={() => router.push(link.href)} style={[styles.sectionItem, active && styles.sectionItemActive]}>
              <Text style={[styles.sectionText, active && styles.sectionTextActive]}>{link.label}</Text>
            </Pressable>;
          })}
        </ScrollView>

        <View style={styles.dock}>
          {visiblePrimary.map((link) => {
            const active = activePrimary?.label === link.label;
            return <Pressable key={link.label} onPress={() => router.push(link.href)} style={styles.primaryItem} accessibilityRole="button" accessibilityLabel={link.label}>
              <View style={[styles.iconWrap, active && styles.iconWrapActive]}>
                <SymbolView name={link.icon} size={19} tintColor={active ? '#078343' : '#778078'} />
              </View>
              <Text style={[styles.primaryText, active && styles.primaryTextActive]} numberOfLines={1}>{link.shortLabel}</Text>
            </Pressable>;
          })}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  shell: { zIndex: 10, width: '100%', backgroundColor: 'transparent', paddingTop: 4, paddingHorizontal: 14 },
  inner: { width: '100%', maxWidth: 680, alignSelf: 'center', gap: 8 },
  sectionRow: { minHeight: 43, alignItems: 'center', gap: 5, paddingHorizontal: 8, paddingVertical: 5, borderRadius: 16, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E3E9E4' },
  sectionItem: { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 11 },
  sectionItemActive: { backgroundColor: '#E7F5EC' },
  sectionText: { color: '#69756D', fontSize: 11, fontWeight: '600' },
  sectionTextActive: { color: '#078343', fontWeight: '800' },
  dock: { minHeight: 66, flexDirection: 'row', justifyContent: 'space-around', alignItems: 'center', paddingHorizontal: 7, paddingVertical: 6, borderRadius: 24, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E3E9E4', shadowColor: '#142039', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.08, shadowRadius: 10, elevation: 4 },
  primaryItem: { flex: 1, minWidth: 52, alignItems: 'center', justifyContent: 'center', gap: 2 },
  iconWrap: { width: 35, height: 32, alignItems: 'center', justifyContent: 'center', borderRadius: 13 },
  iconWrapActive: { backgroundColor: '#E7F5EC' },
  primaryText: { color: '#778078', fontSize: 9, fontWeight: '600' },
  primaryTextActive: { color: '#078343', fontWeight: '800' },
});
