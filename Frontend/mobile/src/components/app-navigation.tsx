import { usePathname, useRouter } from 'expo-router';
import { SymbolView } from 'expo-symbols';
import { Platform, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { PRIMARY_LINKS } from '@/constants/navigation';
import { HitSize, Radius } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';
import { useAuth } from '@/lib/auth-context';
import { MotionPressable } from '@/components/motion';

/** One bottom tab bar. Sub-screens are reached from links inside each page. */
export function AppNavigation() {
  const router = useRouter();
  const pathname = usePathname();
  const insets = useSafeAreaInsets();
  const t = useAppTheme();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || !!user?.is_staff;

  if (!user || pathname === '/' || pathname === '/signup' || pathname === '/reset-password') return null;

  const links = PRIMARY_LINKS.filter((link) => !('admin' in link && link.admin && !isAdmin));

  return (
    <View style={[styles.bar, { borderTopColor: t.separator, paddingBottom: Math.max(insets.bottom, Platform.OS === 'ios' ? 6 : 8) }, { backgroundColor: t.surface }]}>
      <View style={styles.row} accessibilityRole="tablist">
        {links.map((link) => {
          const active = pathname === link.href || pathname.startsWith(`${link.href}/`) ||
            (link.href === '/products' && ['/categories', '/suppliers'].some((route) => pathname.startsWith(route))) ||
            (link.href === '/home' && ['/orders', '/deliveries', '/clients', '/purchases', '/expenses', '/profile'].some((route) => pathname.startsWith(route)));
          const color = active ? t.tint : t.secondaryText;
          return (
            <MotionPressable
              key={link.href}
              onPress={() => router.replace(link.href)}
              style={[styles.item, { minHeight: Math.max(HitSize, 48) }, active && { backgroundColor: t.tintSurface }]}
              accessibilityRole="tab"
              accessibilityLabel={link.label}
              accessibilityState={{ selected: active }}>
              <SymbolView name={link.icon} size={22} tintColor={color} />
              <Text style={[styles.label, { color }]}>{link.label}</Text>
            </MotionPressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: { borderTopWidth: StyleSheet.hairlineWidth, paddingTop: 6, paddingHorizontal: 12 },
  row: { flexDirection: 'row', width: '100%', maxWidth: 760, alignSelf: 'center', gap: 6 },
  item: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 2, borderRadius: Radius.control },
  label: { fontSize: 12, lineHeight: 16, fontWeight: '600' },
});
