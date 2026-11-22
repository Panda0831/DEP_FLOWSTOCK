import { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { confirmPasswordReset } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { FadeIn, MotionPressable } from '@/components/motion';

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
          <FadeIn style={styles.content}>
            <View style={styles.brand}><BrandLockup variant="hero" tagline /></View>
            <Text style={styles.title}>{isComplete ? 'Mot de passe réinitialisé' : 'Nouveau mot de passe'}</Text>
            <Text style={styles.subtitle}>
              {isComplete
                ? 'Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.'
                : 'Choisissez un nouveau mot de passe pour votre compte.'}
            </Text>
            {!isComplete && !!uid && !!token && (
              <View style={styles.form}>
                <Text style={styles.fieldLabel}>Nouveau mot de passe</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Saisissez un nouveau mot de passe"
                  placeholderTextColor="#7B8190"
                  value={newPassword}
                  onChangeText={setNewPassword}
                  secureTextEntry
                  autoComplete="new-password"
                  textContentType="newPassword"
                />
                <Text style={styles.fieldLabel}>Confirmer le mot de passe</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Saisissez-le une seconde fois"
                  placeholderTextColor="#7B8190"
                  value={confirmation}
                  onChangeText={setConfirmation}
                  secureTextEntry
                  autoComplete="new-password"
                  textContentType="newPassword"
                />
              </View>
            )}
            {!!message && <Text accessibilityRole="alert" style={[styles.message, isComplete && styles.success]}>{message}</Text>}
            <MotionPressable
              onPress={isComplete ? () => router.replace('/') : handleSubmit}
              disabled={isLoading}
              style={styles.button}>
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.buttonText}>{isComplete ? 'Retour à la connexion' : 'Réinitialiser le mot de passe'}</Text>
              )}
            </MotionPressable>
            {!uid || !token ? (
              <MotionPressable onPress={() => router.replace('/')} style={styles.backButton}>
                <Text style={styles.backText}>Retour à la connexion</Text>
              </MotionPressable>
            ) : null}
          </FadeIn>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F5F8F5' },
  keyboard: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  content: { width: '100%', maxWidth: 430, alignSelf: 'center', backgroundColor: '#FFFFFF', padding: 24, borderRadius: 22, borderWidth: 1, borderColor: '#DDE9DF', shadowColor: '#38704A', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.05, shadowRadius: 16, elevation: 2 },
  brand: { alignItems: 'center', marginBottom: 24 },
  title: { color: '#173D2B', fontSize: 28, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: '#65736A', fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 9, marginBottom: 22 },
  form: { gap: 0 },
  fieldLabel: { color: '#4F5A52', fontSize: 12, fontWeight: '700', marginBottom: 7, marginTop: 11 },
  input: { height: 54, borderWidth: 1, borderColor: '#D9E3DB', borderRadius: 14, paddingHorizontal: 16, fontSize: 15, color: '#173D2B', backgroundColor: '#FBFDFB' },
  message: { color: '#A33B31', fontSize: 13, lineHeight: 18, marginTop: 14, padding: 11, borderRadius: 11, backgroundColor: '#FFF0EF' },
  success: { color: '#078343', backgroundColor: '#EAF7EE' },
  button: { minHeight: 56, paddingHorizontal: 12, backgroundColor: GREEN, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 22 },
  buttonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '700', textAlign: 'center' },
  backButton: { marginTop: 14, alignItems: 'center', padding: 8 },
  backText: { color: GREEN, fontSize: 15, fontWeight: '700' },
});
