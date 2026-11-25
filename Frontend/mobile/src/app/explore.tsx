import { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';

import { AppPageHeading } from '@/components/page-heading';
import { MotionPressable } from '@/components/motion';
import { PRIMARY_LINKS, SECTION_LINKS } from '@/constants/navigation';
import { MaxContentWidth, Radius, Spacing, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';
import { useAuth } from '@/lib/auth-context';

export default function ExploreScreen() {
  const router = useRouter();
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN' || !!user?.is_staff;
  const groups = [...new Set(SECTION_LINKS
    .filter((link) => !('admin' in link && link.admin && !isAdmin))
    .map((link) => link.group))];
  const primaryHrefs = new Set<string>(PRIMARY_LINKS.map((link) => link.href));

  return (
    <ScrollView style={styles.page} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <AppPageHeading
        title="Parcourir FlowStock"
        subtitle="Accédez aux outils de gestion de votre activité."
      />
      {groups.map((group) => (
        <View key={group} style={styles.group}>
          <Text style={styles.groupTitle}>{group}</Text>
          <View style={styles.list}>
            {SECTION_LINKS
              .filter((link) => link.group === group && !('admin' in link && link.admin && !isAdmin))
              .map((link) => (
                <MotionPressable
                  key={link.href}
                  onPress={() => router.push(link.href)}
                  style={styles.link}
                  accessibilityRole="link"
                  accessibilityLabel={`Ouvrir ${link.label}`}>
                  <Text style={[styles.linkText, primaryHrefs.has(link.href) && styles.primaryLinkText]}>
                    {link.label}
                  </Text>
                  <Text style={styles.chevron} accessibilityElementsHidden>›</Text>
                </MotionPressable>
              ))}
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

const makeStyles = (t: ReturnType<typeof useAppTheme>) => StyleSheet.create({
  page: { flex: 1, backgroundColor: t.background },
  content: {
    width: '100%',
    maxWidth: MaxContentWidth,
    alignSelf: 'center',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.xxl,
  },
  group: { marginBottom: Spacing.xl },
  groupTitle: { ...Type.headline, color: t.text, marginBottom: Spacing.sm },
  list: {
    overflow: 'hidden',
    backgroundColor: t.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: t.separator,
    borderRadius: Radius.card,
  },
  link: {
    minHeight: 52,
    paddingHorizontal: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: t.separator,
  },
  linkText: { ...Type.body, color: t.text },
  primaryLinkText: { fontWeight: '600' },
  chevron: { color: t.secondaryText, fontSize: 22, lineHeight: 26 },
});
