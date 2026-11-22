import { SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { BrandLockup } from '@/components/brand-lockup';
import { FadeIn, MotionPressable } from '@/components/motion';

export default function SignupScreen() {
  const router = useRouter();
  return <SafeAreaView style={styles.safe}>
    <StatusBar style="dark" />
    <FadeIn style={styles.card}>
      <BrandLockup variant="hero" />
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

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F5F8F5', justifyContent: 'center', padding: 22 },
  card: { width: '100%', maxWidth: 460, alignSelf: 'center', backgroundColor: '#FFFFFF', borderRadius: 24, padding: 28, borderWidth: 1, borderColor: '#DDE9DF', shadowColor: '#38704A', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.06, shadowRadius: 20, elevation: 3 },
  copyBlock: { marginTop: 30 },
  eyebrow: { color: '#078343', fontSize: 10, fontWeight: '800', letterSpacing: 1.2, textAlign: 'center' },
  title: { color: '#173D2B', fontSize: 27, fontWeight: '800', marginTop: 9, textAlign: 'center' },
  copy: { color: '#65736A', fontSize: 14, lineHeight: 22, marginTop: 11, textAlign: 'center' },
  button: { minHeight: 52, borderRadius: 14, backgroundColor: '#078343', justifyContent: 'center', alignItems: 'center', marginTop: 24 },
  buttonText: { color: '#FFFFFF', fontSize: 14, fontWeight: '700' },
});
