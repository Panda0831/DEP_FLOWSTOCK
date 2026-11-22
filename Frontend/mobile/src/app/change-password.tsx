import { useEffect, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';

import { useAuth } from '@/lib/auth-context';
import { ApiError, changeMyPassword } from '@/lib/api';
import { readTokens } from '@/lib/auth-storage';

const GREEN = '#078343';

export default function ChangePasswordScreen() {
  const router = useRouter();
  const { clearLocalSession, isReady, user } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    if (isReady && !user && !isComplete) router.replace('/');
  }, [isComplete, isReady, router, user]);

  const handleSubmit = async () => {
    if (!currentPassword || !newPassword || !confirmation) {
      setMessage('Renseignez les trois champs.');
      return;
    }
    if (newPassword !== confirmation) {
      setMessage('La confirmation ne correspond pas au nouveau mot de passe.');
      return;
    }

    setIsLoading(true);
    setMessage('');
    try {
      const tokens = await readTokens();
      if (!tokens) throw new ApiError('Votre session a expiré. Reconnectez-vous.', 401);
      await changeMyPassword(tokens.access, currentPassword, newPassword, confirmation);
      await clearLocalSession();
      setIsComplete(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Modification impossible. Réessayez.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isReady || (!user && !isComplete)) {
    return (
      <SafeAreaView style={styles.loading}>
        <ActivityIndicator color={GREEN} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.content}>
            <Text style={styles.brand}>StockFlow</Text>
            <Text style={styles.title}>{isComplete ? 'Mot de passe modifié' : 'Sécurisez votre compte'}</Text>
            <Text style={styles.subtitle}>
              {isComplete
                ? 'Reconnectez-vous avec votre nouveau mot de passe.'
                : 'Choisissez un nouveau mot de passe pour continuer.'}
            </Text>
            {!isComplete && (
              <View style={styles.form}>
                <TextInput
                  style={styles.input}
                  placeholder="Mot de passe temporaire"
                  placeholderTextColor="#7B8190"
                  value={currentPassword}
                  onChangeText={setCurrentPassword}
                  secureTextEntry
                  autoComplete="current-password"
                  textContentType="password"
                />
                <TextInput
                  style={styles.input}
                  placeholder="Nouveau mot de passe"
                  placeholderTextColor="#7B8190"
                  value={newPassword}
                  onChangeText={setNewPassword}
                  secureTextEntry
                  autoComplete="new-password"
                  textContentType="newPassword"
                />
                <TextInput
                  style={styles.input}
                  placeholder="Confirmer le nouveau mot de passe"
                  placeholderTextColor="#7B8190"
                  value={confirmation}
                  onChangeText={setConfirmation}
                  secureTextEntry
                  autoComplete="new-password"
                  textContentType="newPassword"
                />
              </View>
            )}
            {!!message && <Text style={styles.error}>{message}</Text>}
            <Pressable
              onPress={isComplete ? () => router.replace('/') : handleSubmit}
              disabled={isLoading}
              style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.buttonText}>{isComplete ? 'Retour à la connexion' : 'Modifier le mot de passe'}</Text>
              )}
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#FFFFFF' },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#FFFFFF' },
  keyboard: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  content: { width: '100%', maxWidth: 430, alignSelf: 'center' },
  brand: { color: GREEN, textAlign: 'center', fontSize: 26, fontWeight: '800', marginBottom: 28 },
  title: { color: '#142039', fontSize: 28, fontWeight: '700', textAlign: 'center' },
  subtitle: { color: '#596174', fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 9, marginBottom: 28 },
  form: { gap: 13 },
  input: { height: 56, borderWidth: 1, borderColor: '#C8CFD9', borderRadius: 14, paddingHorizontal: 16, fontSize: 16, color: '#202638' },
  error: { color: '#A33B31', fontSize: 13, lineHeight: 18, marginTop: 14 },
  button: { height: 56, backgroundColor: GREEN, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 22 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700', textAlign: 'center', paddingHorizontal: 12 },
  pressed: { opacity: 0.85 },
});
