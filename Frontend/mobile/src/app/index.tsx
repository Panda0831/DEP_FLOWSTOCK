import { useEffect, useState, type ReactNode } from 'react';
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
import { requestPasswordReset } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';
import { FadeIn, MotionPressable } from '@/components/motion';

const GREEN = '#078343';

function FieldIcon({ kind }: { kind: 'person' | 'mail' | 'lock' }) {
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
  return (
    <View style={styles.field}>
      <View style={styles.fieldIcon} accessibilityElementsHidden>
        <FieldIcon kind={icon} />
      </View>
      <TextInput
        style={styles.input}
        placeholder={placeholder}
        placeholderTextColor="#7B8190"
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
  const router = useRouter();
  const { isReady, signIn, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState('');
  const [messageIsSuccess, setMessageIsSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

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
        <ActivityIndicator color={GREEN} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'bottom']}>
      <StatusBar style="dark" />
      <View pointerEvents="none" style={styles.topGlow} />
      <View pointerEvents="none" style={styles.bottomGlowLeft} />
      <View pointerEvents="none" style={styles.bottomGlowRight} />
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}>
          <View style={styles.content}>
            <FadeIn><View style={styles.brand}><BrandLockup variant="hero" tagline /></View></FadeIn>

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

              <MotionPressable onPress={handleForgotPassword} style={styles.forgotButton}>
                <Text style={styles.forgotText}>Mot de passe oublié ?</Text>
              </MotionPressable>

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
                {isLoading ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryButtonText}>Se connecter</Text>}
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

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#FFFFFF' },
  loadingScreen: { alignItems: 'center', justifyContent: 'center' },
  keyboardView: { flex: 1 },
  scrollContent: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 24, paddingVertical: 30 },
  content: { width: '100%', maxWidth: 420, alignSelf: 'center' },
  topGlow: {
    position: 'absolute',
    width: 260,
    height: 260,
    borderRadius: 140,
    backgroundColor: '#E8F8EF',
    top: -190,
    left: -130,
  },
  bottomGlowLeft: {
    position: 'absolute',
    width: 190,
    height: 190,
    borderRadius: 100,
    backgroundColor: '#F0FBF4',
    bottom: -145,
    left: -95,
  },
  bottomGlowRight: {
    position: 'absolute',
    width: 220,
    height: 220,
    borderRadius: 120,
    backgroundColor: '#F1FBF5',
    bottom: -175,
    right: -135,
  },
  brand: { alignItems: 'center', marginBottom: 26 },
  form: { gap: 15 },
  heading: { color: '#142039', fontSize: 28, fontWeight: '700', textAlign: 'center', marginBottom: 7 },
  field: {
    height: 58,
    borderWidth: 1,
    borderColor: '#C8CFD9',
    borderRadius: 15,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
    backgroundColor: 'rgba(255,255,255,0.92)',
  },
  fieldIcon: { width: 29, alignItems: 'flex-start', justifyContent: 'center' },
  mailIcon: { color: GREEN, fontSize: 20, lineHeight: 24 },
  personIcon: { width: 19, height: 22, alignItems: 'center', justifyContent: 'flex-end' },
  personHead: { width: 8, height: 8, borderWidth: 1.7, borderColor: GREEN, borderRadius: 5, marginBottom: 2 },
  personShoulders: { width: 17, height: 9, borderWidth: 1.7, borderColor: GREEN, borderTopLeftRadius: 10, borderTopRightRadius: 10, borderBottomWidth: 0 },
  lockIcon: { width: 19, height: 22, justifyContent: 'flex-end', alignItems: 'center' },
  lockArch: { width: 12, height: 10, borderWidth: 1.7, borderColor: GREEN, borderBottomWidth: 0, borderTopLeftRadius: 7, borderTopRightRadius: 7 },
  lockBody: { width: 17, height: 12, borderWidth: 1.7, borderColor: GREEN, borderRadius: 3, backgroundColor: '#FFFFFF' },
  input: { flex: 1, color: '#202638', fontSize: 16, paddingVertical: 0 },
  eyeIcon: {
    width: 22,
    height: 15,
    borderWidth: 1.7,
    borderColor: '#62697A',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  eyePupil: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#62697A' },
  eyeSlash: {
    position: 'absolute',
    width: 26,
    height: 1.7,
    backgroundColor: '#62697A',
    transform: [{ rotate: '-42deg' }],
  },
  forgotButton: { alignSelf: 'flex-end', marginTop: -3, paddingVertical: 2 },
  forgotText: { color: GREEN, fontWeight: '600', fontSize: 14 },
  message: { color: '#A33B31', fontSize: 13, lineHeight: 18, marginTop: -4 },
  successMessage: { color: GREEN },
  disabled: { opacity: 0.72 },
  primaryButton: {
    height: 58,
    backgroundColor: GREEN,
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
  primaryButtonText: { color: '#FFFFFF', fontSize: 19, fontWeight: '700' },
  footer: { alignItems: 'center', marginTop: 38, gap: 5 },
  footerPrompt: { color: '#252B3A', fontSize: 15 },
  footerLink: { color: GREEN, fontWeight: '700', fontSize: 16, paddingVertical: 4 },
});
