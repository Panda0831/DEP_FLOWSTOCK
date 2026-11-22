import { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';

import { useAuth } from '@/lib/auth-context';

const GREEN = '#078343';

export default function HomeScreen() {
  const router = useRouter();
  const { isReady, signOut, user } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isReady && !user) router.replace('/');
    if (user?.doit_changer_mot_de_passe) router.replace('/change-password');
  }, [isReady, router, user]);

  const handleSignOut = async () => {
    setIsSigningOut(true);
    setMessage('');
    try {
      await signOut();
    } catch {
      setMessage('Session supprimée sur cet appareil. La révocation côté serveur a échoué.');
    } finally {
      setIsSigningOut(false);
      router.replace('/');
    }
  };

  if (!isReady || !user) {
    return (
      <SafeAreaView style={styles.loading}>
        <ActivityIndicator color={GREEN} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="dark" />
      <View pointerEvents="none" style={styles.glow} />
      <View style={styles.content}>
        <View style={styles.brandRow}>
          <View style={styles.brandMark}><Text style={styles.brandLetter}>S</Text></View>
          <Text style={styles.brandName}>StockFlow</Text>
        </View>
        <View style={styles.card}>
          <Text style={styles.eyebrow}>ESPACE STOCKFLOW</Text>
          <Text style={styles.title}>Bienvenue{user.prenom ? `, ${user.prenom}` : ''}</Text>
          <Text style={styles.email}>{user.email}</Text>
          <Text style={styles.description}>
            Votre session est active. Vous pourrez accéder ici à la gestion de votre activité.
          </Text>
          {!!message && <Text style={styles.error}>{message}</Text>}
          <Pressable
            onPress={handleSignOut}
            disabled={isSigningOut}
            style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
            {isSigningOut ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.buttonText}>Se déconnecter</Text>}
          </Pressable>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#FFFFFF' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFFFF' },
  glow: { position: 'absolute', width: 280, height: 280, borderRadius: 160, backgroundColor: '#E8F8EF', top: -195, left: -145 },
  content: { flex: 1, width: '100%', maxWidth: 480, alignSelf: 'center', justifyContent: 'center', padding: 24 },
  brandRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 34 },
  brandMark: { width: 42, height: 42, borderRadius: 21, backgroundColor: GREEN, alignItems: 'center', justifyContent: 'center' },
  brandLetter: { color: '#FFFFFF', fontSize: 31, lineHeight: 38, fontWeight: '800' },
  brandName: { color: '#142039', fontSize: 28, fontWeight: '800' },
  card: { borderWidth: 1, borderColor: '#E0E7E2', borderRadius: 22, padding: 24, backgroundColor: '#FFFFFF' },
  eyebrow: { color: GREEN, fontSize: 12, letterSpacing: 1.3, fontWeight: '700', marginBottom: 12 },
  title: { color: '#142039', fontSize: 29, fontWeight: '700' },
  email: { color: '#687182', fontSize: 15, marginTop: 5 },
  description: { color: '#384154', fontSize: 15, lineHeight: 22, marginTop: 24 },
  error: { color: '#A33B31', fontSize: 13, lineHeight: 18, marginTop: 16 },
  button: { height: 54, backgroundColor: GREEN, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 28 },
  buttonText: { color: '#FFFFFF', fontSize: 17, fontWeight: '700' },
  pressed: { opacity: 0.85 },
});
