import { useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';

import { useAuth } from '@/lib/auth-context';
import { getRememberedEmail, requestPasswordReset, setRememberedEmail } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { BrandDivider, FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

function FieldIcon({ kind }: { kind: 'person' | 'mail' | 'lock' }) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  if (kind === 'mail') return <Text style={styles.mailIcon}>✉</Text>;
  if (kind === 'person') {
    return (
      <View style={styles.personIcon}>
        <View style={styles.personHead} />
        <View style={styles.personShoulders} />
      </View>
    );
  }
  return (
    <View style={styles.lockIcon}>
      <View style={styles.lockArch} />
      <View style={styles.lockBody} />
    </View>
  );
}

function PasswordEye({ hidden }: { hidden: boolean }) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  return (
    <View style={styles.eyeIcon}>
      <View style={styles.eyePupil} />
      {hidden && <View style={styles.eyeSlash} />}
    </View>
  );
}

function Field({
  icon,
  placeholder,
  value,
  onChangeText,
  secureTextEntry,
  keyboardType,
  autoComplete,
  textContentType,
  trailing,
}: {
  icon: 'person' | 'mail' | 'lock';
  placeholder: string;
  value: string;
  onChangeText: (value: string) => void;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address';
  autoComplete?: 'email' | 'password' | 'name';
  textContentType?: 'emailAddress' | 'password' | 'name';
  trailing?: ReactNode;
}) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  return (
    <View style={styles.field}>
      <View style={styles.fieldIcon} accessibilityElementsHidden>
        <FieldIcon kind={icon} />
      </View>
      <TextInput
        style={styles.input}
        placeholder={placeholder}
        placeholderTextColor={t.secondaryText}
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        keyboardType={keyboardType}
        autoCapitalize="none"
        autoComplete={autoComplete}
        textContentType={textContentType}
        returnKeyType="done"
      />
      {trailing}
    </View>
  );
}

export default function HomeScreen() {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const router = useRouter();
  const { isReady, signIn, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState('');
  const [messageIsSuccess, setMessageIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let active = true;
    void getRememberedEmail().then((savedEmail) => {
      if (active && savedEmail) {
        setEmail(savedEmail);
        setRememberMe(true);
      }
    }).catch(() => {});
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (isReady && user) {
      router.replace('/home');
    }
  }, [isReady, router, user]);

  const handleSubmit = async () => {
    if (isLoading) return;
    if (!email.trim() || !password) {
      setMessage('Renseignez votre adresse e-mail et votre mot de passe.');
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setMessage('Vérifiez le format de votre adresse e-mail.');
      return;
    }

    setMessage('');
    setMessageIsSuccess(false);
    setIsLoading(true);
    try {
      await signIn(email.trim(), password);
      try { await setRememberedEmail(rememberMe ? email.trim() : null); } catch { /* Login should not fail if local storage is unavailable. */ }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Connexion impossible. Réessayez.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (isLoading) return;
    if (!email.trim()) {
      setMessage('Saisissez votre adresse e-mail pour réinitialiser le mot de passe.');
      setMessageIsSuccess(false);
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email.trim())) {
      setMessage('Vérifiez le format de votre adresse e-mail.');
      setMessageIsSuccess(false);
      return;
    }

    setIsLoading(true);
    setMessage('');
    try {
      const result = await requestPasswordReset(email.trim());
      setMessage(result.detail);
      setMessageIsSuccess(true);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Demande impossible. Réessayez.');
      setMessageIsSuccess(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isReady) {
    return (
      <SafeAreaView style={[styles.safeArea, styles.loadingScreen]}>
        <ActivityIndicator color={t.tint} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="auto" />
      <View pointerEvents="none" style={styles.topGlow} />
      <View pointerEvents="none" style={styles.bottomGlowLeft} />
      <View pointerEvents="none" style={styles.bottomGlowRight} />
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
          showsHorizontalScrollIndicator={false}>
          <View style={styles.content}>
            <FadeIn><View style={styles.brand}><BrandLockup variant="hero" tagline /></View></FadeIn>
            <BrandDivider />

            <FadeIn delay={120}><View style={styles.form}>
              <Text style={styles.heading}>Connexion</Text>
              <Field
                icon="mail"
                placeholder="Adresse e-mail"
                value={email}
                onChangeText={(value) => {
                  setEmail(value);
                  setMessage('');
                }}
                keyboardType="email-address"
                autoComplete="email"
                textContentType="emailAddress"
              />
              <Field
                icon="lock"
                placeholder="Mot de passe"
                value={password}
                onChangeText={(value) => {
                  setPassword(value);
                  setMessage('');
                }}
                secureTextEntry={!showPassword}
                autoComplete="password"
                textContentType="password"
                trailing={
                  <Pressable
                    onPress={() => setShowPassword((visible) => !visible)}
                    accessibilityRole="button"
                    accessibilityLabel={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    hitSlop={10}>
                    <PasswordEye hidden={!showPassword} />
                  </Pressable>
                }
              />

              <View style={styles.loginOptions}>
                <Pressable
                  onPress={() => {
                    const nextValue = !rememberMe;
                    setRememberMe(nextValue);
                    if (!nextValue) void setRememberedEmail(null).catch(() => {});
                  }}
                  style={styles.rememberButton}
                  accessibilityRole="checkbox"
                  accessibilityState={{ checked: rememberMe }}
                  accessibilityLabel="Se souvenir de moi">
                  <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                    {rememberMe && <Text style={styles.checkboxMark}>✓</Text>}
                  </View>
                  <Text style={styles.rememberText}>Se souvenir de moi</Text>
                </Pressable>

                <MotionPressable onPress={handleForgotPassword} style={styles.forgotButton}>
                  <Text style={styles.forgotText}>Mot de passe oublié ?</Text>
                </MotionPressable>
              </View>

              {!!message && (
                <Text style={[styles.message, messageIsSuccess && styles.successMessage]}>
                  {message}
                </Text>
              )}

              <MotionPressable
                onPress={handleSubmit}
                disabled={isLoading}
                style={[styles.primaryButton, isLoading && styles.disabled]}
                accessibilityRole="button">
                {isLoading ? <ActivityIndicator color={t.onTint} /> : <Text style={styles.primaryButtonText}>Se connecter</Text>}
              </MotionPressable>
            </View></FadeIn>

            <FadeIn delay={220}><View style={styles.footer}>
              <Text style={styles.footerPrompt}>Pas encore de compte ?</Text>
              <MotionPressable
                onPress={() => router.push('/signup')}
                accessibilityRole="button">
                <Text style={styles.footerLink}>Créer un compte</Text>
              </MotionPressable>
            </View></FadeIn>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: t.background },
  loadingScreen: { alignItems: 'center', justifyContent: 'center' },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 24, paddingVertical: 30 },
  content: { width: '100%', maxWidth: 420, alignSelf: 'center' },
  topGlow: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 140,
    backgroundColor: t.tintSurface,
    top: -190,
    left: -130,
  },
  bottomGlowLeft: {
    position: 'absolute',
    width: 190,
    height: 190,
    borderRadius: 100,
    backgroundColor: t.background,
    bottom: -145,
    left: -95,
  },
  bottomGlowRight: {
    position: 'absolute',
    width: 220,
    height: 220,
    borderRadius: 120,
    backgroundColor: t.background,
    bottom: -175,
    right: -135,
  },
  brand: { alignItems: 'center', marginBottom: 26 },
  form: { gap: 15 },
  heading: { color: t.text, fontSize: 28, fontWeight: '800', textAlign: 'center', marginBottom: 7 },
  field: {
    height: 58,
    borderWidth: 1,
    borderColor: t.separator,
    borderRadius: 15,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    backgroundColor: t.surface,
  },
  fieldIcon: { width: 29, alignItems: 'flex-start', justifyContent: 'center' },
  mailIcon: { color: t.tint, fontSize: 20, lineHeight: 24 },
  personIcon: { width: 19, height: 22, alignItems: 'center', justifyContent: 'flex-end' },
  personHead: { width: 8, height: 8, borderWidth: 1.7, borderColor: t.tint, borderRadius: 5, marginBottom: 2 },
  personShoulders: { width: 17, height: 9, borderWidth: 1.7, borderColor: t.tint, borderTopLeftRadius: 10, borderTopRightRadius: 10, borderBottomWidth: 0 },
  lockIcon: { width: 19, height: 22, justifyContent: 'flex-end', alignItems: 'center' },
  lockArch: { width: 12, height: 10, borderWidth: 1.7, borderColor: t.tint, borderBottomWidth: 0, borderTopLeftRadius: 7, borderTopRightRadius: 7 },
  lockBody: { width: 17, height: 12, borderWidth: 1.7, borderColor: t.tint, borderRadius: 3, backgroundColor: t.surface },
  input: { flex: 1, color: t.text, fontSize: 16, paddingVertical: 0 },
  eyeIcon: {
    width: 22,
    height: 15,
    borderWidth: 1.7,
    borderColor: t.secondaryText,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  eyePupil: { width: 6, height: 6, borderRadius: 3, backgroundColor: t.secondaryText },
  eyeSlash: {
    position: 'absolute',
    width: 26,
    height: 1.7,
    backgroundColor: t.secondaryText,
    transform: [{ rotate: '-42deg' }],
  },
  loginOptions: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginTop: -3 },
  rememberButton: { flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 3 },
  checkbox: { width: 18, height: 18, borderWidth: 1.5, borderColor: t.separator, borderRadius: 5, backgroundColor: t.surface, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: t.tint, borderColor: t.tint },
  checkboxMark: { color: t.onTint, fontSize: 12, fontWeight: '900', lineHeight: 14 },
  rememberText: { color: t.secondaryText, fontSize: 12, fontWeight: '600' },
  forgotButton: { paddingVertical: 2 },
  forgotText: { color: t.tint, fontWeight: '600', fontSize: 14 },
  message: { color: t.danger, fontSize: 13, lineHeight: 18, marginTop: -4, paddingVertical: 10, paddingHorizontal: 12, backgroundColor: t.dangerSurface, borderRadius: 11 },
  successMessage: { color: t.tint, backgroundColor: t.tintSurface },
  disabled: { opacity: 0.72 },
  primaryButton: {
    height: 58,
    backgroundColor: t.tint,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 13,
    shadowColor: '#006A34',
    shadowOpacity: 0.16,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 6 },
    elevation: 3,
  },
  primaryButtonText: { color: t.onTint, fontSize: 19, fontWeight: '700' },
  footer: { alignItems: 'center', marginTop: 38, gap: 5 },
  footerPrompt: { color: t.secondaryText, fontSize: 15 },
  footerLink: { color: t.tint, fontWeight: '700', fontSize: 16, paddingVertical: 4 },
});
