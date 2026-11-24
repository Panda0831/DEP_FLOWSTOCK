import { useMemo } from 'react';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { BrandLockup } from '@/components/brand-lockup';
import { BrandDivider, FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

export default function SignupScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const router = useRouter();
  return <SafeAreaView style={styles.safe}>
    <StatusBar style="auto" />
    <FadeIn style={styles.card}>
      <BrandLockup variant="hero" />
      <BrandDivider style={styles.divider} />
      <View style={styles.copyBlock}>
        <Text style={styles.eyebrow}>ACCÈS À L’ESPACE</Text>
        <Text style={styles.title}>Demander un accès</Text>
        <Text style={styles.copy}>Les comptes sont créés par un administrateur FlowStock. Contactez l’administrateur de votre espace pour recevoir vos identifiants.</Text>
      </View>
      <MotionPressable onPress={() => router.replace('/')} style={styles.button} accessibilityRole="button">
        <Text style={styles.buttonText}>Retour à la connexion</Text>
      </MotionPressable>
    </FadeIn>
  </SafeAreaView>;
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  safe: { flex: 1, backgroundColor: t.background, justifyContent: 'center', padding: 22 },
  card: { width: '100%', maxWidth: 460, alignSelf: 'center', backgroundColor: t.surface, borderRadius: 24, padding: 28, borderWidth: 1, borderColor: t.separator, shadowColor: '#38704A', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.06, shadowRadius: 20, elevation: 3 },
  copyBlock: { marginTop: 12 },
  divider: { marginTop: 20 },
  eyebrow: { color: t.tint, fontSize: 10, fontWeight: '800', letterSpacing: 1.2, textAlign: 'center' },
  title: { color: t.text, fontSize: 27, fontWeight: '800', marginTop: 9, textAlign: 'center' },
  copy: { color: t.secondaryText, fontSize: 14, lineHeight: 22, marginTop: 11, textAlign: 'center' },
  button: { minHeight: 52, borderRadius: 14, backgroundColor: t.tint, justifyContent: 'center', alignItems: 'center', marginTop: 24 },
  buttonText: { color: t.onTint, fontSize: 14, fontWeight: '700' },
});
