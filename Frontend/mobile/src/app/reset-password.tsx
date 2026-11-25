import { useMemo, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useLocalSearchParams, useRouter } from 'expo-router';

import { confirmPasswordReset } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { BrandDivider, FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

export default function ResetPasswordScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
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
      <StatusBar style="auto" />
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
          <FadeIn style={styles.content}>
            <View style={styles.brand}><BrandLockup variant="hero" tagline /></View>
            <BrandDivider />
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
                  placeholderTextColor={t.secondaryText}
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
                  placeholderTextColor={t.secondaryText}
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
                <ActivityIndicator color={t.onTint} />
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

const makeStyles = (t: AppTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: t.background },
  keyboard: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  content: { width: '100%', maxWidth: 430, alignSelf: 'center', backgroundColor: t.surface, padding: 22, borderRadius: 20, borderWidth: 1, borderColor: t.separator },
  brand: { alignItems: 'center', marginBottom: 8 },
  title: { color: t.text, fontSize: 28, fontWeight: '700', textAlign: 'center' },
  subtitle: { color: t.secondaryText, fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 9, marginBottom: 22 },
  form: { gap: 0 },
  fieldLabel: { color: t.text, fontSize: 14, lineHeight: 20, fontWeight: '700', marginBottom: 7, marginTop: 11 },
  input: { minHeight: 52, borderWidth: 1, borderColor: t.separator, borderRadius: 12, paddingHorizontal: 14, fontSize: 16, color: t.text, backgroundColor: t.surface },
  message: { color: t.danger, fontSize: 13, lineHeight: 18, marginTop: 14, padding: 11, borderRadius: 11, backgroundColor: t.dangerSurface },
  success: { color: t.tint, backgroundColor: t.tintSurface },
  button: { minHeight: 56, paddingHorizontal: 12, backgroundColor: t.tint, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 22 },
  buttonText: { color: t.onTint, fontSize: 16, fontWeight: '700', textAlign: 'center' },
  backButton: { marginTop: 14, alignItems: 'center', padding: 8 },
  backText: { color: t.tint, fontSize: 15, fontWeight: '700' },
});
