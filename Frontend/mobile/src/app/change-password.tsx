import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';

import { useAuth } from '@/lib/auth-context';
import { changeMyPassword } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { BrandDivider, FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

export default function ChangePasswordScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const router = useRouter();
  const { isReady, user } = useAuth();
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
      await changeMyPassword(currentPassword, newPassword);
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
        <ActivityIndicator color={t.tint} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="auto" />
      <KeyboardAvoidingView style={styles.keyboard} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          <FadeIn style={styles.content}>
            <View style={styles.brand}><BrandLockup variant="hero" tagline /></View>
            <BrandDivider />
            <Text style={styles.title}>{isComplete ? 'Mot de passe modifié' : 'Sécurisez votre compte'}</Text>
            <Text style={styles.subtitle}>
              {isComplete
                ? 'Votre session reste ouverte. Vous pouvez reprendre la gestion de votre activité.'
                : 'Choisissez un nouveau mot de passe pour continuer.'}
            </Text>
            {!isComplete && (
              <View style={styles.form}>
                <Text style={styles.fieldLabel}>Mot de passe temporaire</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Saisissez votre mot de passe actuel"
                  placeholderTextColor={t.secondaryText}
                  value={currentPassword}
                  onChangeText={setCurrentPassword}
                  secureTextEntry
                  autoComplete="current-password"
                  textContentType="password"
                />
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
            {!!message && <Text accessibilityRole="alert" style={styles.error}>{message}</Text>}
            <MotionPressable
              onPress={isComplete ? () => router.replace('/home') : handleSubmit}
              disabled={isLoading}
              style={styles.button}>
              {isLoading ? (
                <ActivityIndicator color={t.onTint} />
              ) : (
                <Text style={styles.buttonText}>{isComplete ? 'Continuer' : 'Modifier le mot de passe'}</Text>
              )}
            </MotionPressable>
          </FadeIn>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: t.background },
  loading: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: t.background },
  keyboard: { flex: 1 },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  content: { width: '100%', maxWidth: 430, alignSelf: 'center', backgroundColor: t.surface, padding: 24, borderRadius: 22, borderWidth: 1, borderColor: t.separator, shadowColor: '#38704A', shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.05, shadowRadius: 16, elevation: 2 },
  brand: { alignItems: 'center', marginBottom: 8 },
  title: { color: t.text, fontSize: 28, fontWeight: '800', textAlign: 'center' },
  subtitle: { color: t.secondaryText, fontSize: 15, lineHeight: 22, textAlign: 'center', marginTop: 9, marginBottom: 19 },
  form: { gap: 0 },
  fieldLabel: { color: t.text, fontSize: 12, fontWeight: '700', marginBottom: 7, marginTop: 11 },
  input: { height: 54, borderWidth: 1, borderColor: t.separator, borderRadius: 14, paddingHorizontal: 16, fontSize: 15, color: t.text, backgroundColor: t.surface },
  error: { color: t.danger, fontSize: 13, lineHeight: 18, marginTop: 14, padding: 11, borderRadius: 11, backgroundColor: t.dangerSurface },
  button: { height: 56, backgroundColor: t.tint, borderRadius: 14, alignItems: 'center', justifyContent: 'center', marginTop: 22 },
  buttonText: { color: t.onTint, fontSize: 16, fontWeight: '700', textAlign: 'center', paddingHorizontal: 12 },
});
