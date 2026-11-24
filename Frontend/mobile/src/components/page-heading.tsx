import { StyleSheet, Text, View } from 'react-native';
import { usePathname, useRouter } from 'expo-router';

import { PRIMARY_HREFS, siblingLinks } from '@/constants/navigation';
import { HitSize, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';
import { useAuth } from '@/lib/auth-context';
import { MotionPressable } from '@/components/motion';

/** Plain title, one line of context, and the few sibling screens of this section. */
export function AppPageHeading({ title, subtitle }: { title: string; subtitle?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const t = useAppTheme();
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || !!user?.is_staff;
  const canGoBack = !PRIMARY_HREFS.includes(pathname as (typeof PRIMARY_HREFS)[number]);
  const links = siblingLinks(pathname).filter((link) => !('admin' in link && link.admin && !isAdmin));

  return (
    <View style={styles.header}>
      <Text style={[styles.title, { color: t.text }]}>{title}</Text>
      {!!subtitle && <Text style={[styles.subtitle, { color: t.secondaryText }]}>{subtitle}</Text>}
      {(canGoBack || links.length > 0) && (
        <View style={styles.links}>
          {canGoBack && (
            <MotionPressable onPress={() => router.back()} style={styles.link} accessibilityRole="button" accessibilityLabel="Retour">
              <Text style={[styles.linkText, { color: t.tint }]}>‹ Retour</Text>
            </MotionPressable>
          )}
          {links.map((link) => (
            <MotionPressable key={link.href} onPress={() => router.push(link.href)} style={styles.link} accessibilityRole="link" accessibilityLabel={link.label}>
              <Text style={[styles.linkText, { color: t.tint }]}>{link.label}</Text>
            </MotionPressable>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  header: { marginBottom: 20 },
  title: { ...Type.title },
  subtitle: { ...Type.footnote, marginTop: 4 },
  links: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 14 },
  link: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 10 },
  linkText: { fontSize: 14, fontWeight: '600' },
});
