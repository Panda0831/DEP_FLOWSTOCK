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
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';

import { useAuth } from '@/lib/auth-context';
import { ApiError, getRememberedEmail, requestPasswordReset, setRememberedEmail } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { BrandDivider, FadeIn, MotionPressable } from '@/components/motion';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

function FieldIcon({ kind }: { kind: 'mail' | 'lock' }) {
  const t = useAppTheme();
  return <Svg width={22} height={22} viewBox="0 0 24 24" fill="none">
    {kind === 'mail' ? <>
      <Rect x={3.5} y={5.5} width={17} height={13} rx={2} stroke={t.tint} strokeWidth={1.7} />
      <Path d="m4.5 7 7.5 6 7.5-6" stroke={t.tint} strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" />
    </> : <>
      <Path d="M7.5 10V7.5a4.5 4.5 0 0 1 9 0V10" stroke={t.tint} strokeWidth={1.7} strokeLinecap="round" />
      <Rect x={5} y={10} width={14} height={11} rx={2} stroke={t.tint} strokeWidth={1.7} />
      <Circle cx={12} cy={15} r={1} fill={t.tint} />
      <Path d="M12 16v2" stroke={t.tint} strokeWidth={1.7} strokeLinecap="round" />
    </>}
  </Svg>;
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
  icon: 'mail' | 'lock';
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
  const [focused, setFocused] = useState(false);
  return (
    <View style={[styles.field, focused && styles.fieldFocused]}>
      <View style={styles.fieldIcon} accessibilityElementsHidden>
        <FieldIcon kind={icon} />
      </View>
      <TextInput
        nativeID={`flowstock-login-${icon}`}
        style={styles.input}
        accessibilityLabel={placeholder}
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
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
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
  const [loginLocked, setLoginLocked] = useState(false);
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
    setLoginLocked(false);
    setIsLoading(true);
    try {
      await signIn(email.trim(), password);
      try { await setRememberedEmail(rememberMe ? email.trim() : null); } catch { /* Login should not fail if local storage is unavailable. */ }
    } catch (error) {
      if (error instanceof ApiError && error.status === 429) {
        setMessage(error.message);
        setLoginLocked(true);
      } else {
        setMessage(error instanceof Error ? error.message : 'Connexion impossible. Réessayez.');
      }
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
    setLoginLocked(false);
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
                  setLoginLocked(false);
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
                  setLoginLocked(false);
                }}
                secureTextEntry={!showPassword}
                autoComplete="password"
                textContentType="password"
                trailing={
                  <Pressable
                    onPress={() => setShowPassword((visible) => !visible)}
                    accessibilityRole="button"
                    accessibilityLabel={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
                    style={styles.passwordToggle}
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
                <Text
                  accessibilityRole={loginLocked ? 'alert' : undefined}
                  accessibilityLiveRegion={loginLocked ? 'polite' : 'none'}
                  style={[styles.message, messageIsSuccess && styles.successMessage]}>
                  {message}
                </Text>
              )}
              {loginLocked && (
                <MotionPressable onPress={handleForgotPassword} style={styles.lockoutAction} accessibilityRole="button">
                  <Text style={styles.lockoutActionText}>Réinitialiser mon mot de passe</Text>
                </MotionPressable>
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
  brand: { alignItems: 'center', marginBottom: 26 },
  form: { gap: 15, backgroundColor: t.surface, padding: 22, borderWidth: 1, borderColor: t.separator, borderRadius: 20 },
  heading: { color: t.text, fontSize: 28, fontWeight: '700', textAlign: 'center', marginBottom: 7 },
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
  fieldFocused: { borderColor: t.tint },
  input: {
    flex: 1,
    color: t.text,
    fontSize: 16,
    paddingVertical: 0,
    outlineWidth: 0,
  },
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
  rememberButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8 },
  checkbox: { width: 18, height: 18, borderWidth: 1.5, borderColor: t.separator, borderRadius: 5, backgroundColor: t.surface, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: t.tint, borderColor: t.tint },
  checkboxMark: { color: t.onTint, fontSize: 12, fontWeight: '900', lineHeight: 14 },
  rememberText: { color: t.secondaryText, fontSize: 14, lineHeight: 20, fontWeight: '600' },
  forgotButton: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 2 },
  forgotText: { color: t.tint, fontWeight: '600', fontSize: 14 },
  message: { color: t.danger, fontSize: 14, lineHeight: 21, marginTop: -4, paddingVertical: 10, paddingHorizontal: 12, backgroundColor: t.dangerSurface, borderRadius: 11 },
  lockoutAction: { alignSelf: 'flex-start', minHeight: 44, justifyContent: 'center', paddingHorizontal: 4 },
  lockoutActionText: { color: t.tint, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  successMessage: { color: t.tint, backgroundColor: t.tintSurface },
  disabled: { opacity: 0.72 },
  primaryButton: {
    minHeight: 56,
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
  passwordToggle: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center' },
  footer: { alignItems: 'center', marginTop: 24, gap: 5 },
  footerPrompt: { color: t.secondaryText, fontSize: 15 },
  footerLink: { color: t.tint, fontWeight: '700', fontSize: 16, paddingVertical: 4 },
});
