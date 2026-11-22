import { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { confirmPasswordReset } from '@/lib/session-api';

const GREEN = '#078343';

export default function ResetPasswordScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ uid?: string | string[]; token?: string | string[] }>();
  const uid = Array.isArray(params.uid) ? params.uid[0] : params.uid;
  const token = Array.isArray(params.token) ? params.token[0] : params.token;
  const [newPassword, setNewPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  const handleSubmit = async () => {
    if (!uid || !token) {
      setMessage('Le lien de réinitialisation est incomplet. Demandez-en un nouveau.');
      return;
    }
    if (!newPassword || !confirmation) {
      setMessage('Renseignez et confirmez votre nouveau mot de passe.');
      return;
    }
    if (newPassword !== confirmation) {
      setMessage('La confirmation ne correspond pas au nouveau mot de passe.');
      return;
    }

    setIsLoading(true);
    setMessage('');
    try {
      const result = await confirmPasswordReset(uid, token, newPassword);
      setMessage(result.detail);
      setIsComplete(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Réinitialisation impossible. Réessayez.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="dark" />
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <View style={styles.content}>
            <Text style={styles.brand}>StockFlow</Text>
            <Text style={styles.title}>{isComplete ? 'Mot de passe réinitialisé' : 'Nouveau mot de passe'}</Text>
            <Text style={styles.subtitle}>
              {isComplete
                ? 'Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.'
                : 'Choisissez un nouveau mot de passe pour votre compte.'}
            </Text>
            {!isComplete && !!uid && !!token && (
              <View style={styles.form}>
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
            {!!message && <Text style={[styles.message, isComplete && styles.success]}>{message}</Text>}
            <Pressable
              onPress={isComplete ? () => router.replace('/') : handleSubmit}
              disabled={isLoading}
              style={({ pressed }) => [styles.button, pressed && styles.pressed]}>
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.buttonText}>{isComplete ? 'Retour à la connexion' : 'Réinitialiser le mot de passe'}</Text>
              )}
            </Pressable>
            {!uid || !token ? (
              <Pressable onPress={() => router.replace('/')} style={styles.backButton}>
                <Text style={styles.backText}>Retour à la connexion</Text>
              </Pressable>
            ) : null}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#FFFFFF' },
  keyboard: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  content: { width: '100%', maxWidth: 430, alignSelf: 'center' },
  brand: { color: GREEN, textAlign: 'center', fontSize: 26, fontWeight: '800', marginBottom: 28 },
  title: { color: '#142039', fontSize: 28, fontWeight: '700', textAlign: 'center' },
  subtitle: { color: '#596174', fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 9, marginBottom: 28 },
  form: { gap: 13 },
  input: { height: 56, borderWidth: 1, borderColor: '#C8CFD9', borderRadius: 14, paddingHorizontal: 16, fontSize: 16, color: '#202638' },
  message: { color: '#A33B31', fontSize: 13, lineHeight: 18, marginTop: 14 },
  success: { color: GREEN },
  button: { minHeight: 56, paddingHorizontal: 12, backgroundColor: GREEN, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 22 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700', textAlign: 'center' },
  pressed: { opacity: 0.85 },
  backButton: { marginTop: 14, alignItems: 'center', padding: 8 },
  backText: { color: GREEN, fontSize: 15, fontWeight: '700' },
});
