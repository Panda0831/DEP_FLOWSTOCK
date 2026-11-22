import { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { signup } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';

export default function SignupScreen() {
  const router = useRouter(); const { signIn } = useAuth();
  const [name, setName] = useState(''); const [email, setEmail] = useState(''); const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const submit = async () => {
    if (!name.trim() || !email.trim() || !password) { setError('Renseignez tous les champs.'); return; }
    setBusy(true); setError('');
    try { const user = await signup(email.trim(), name.trim(), password); signIn(user); router.replace('/home'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Création du compte impossible.'); }
    finally { setBusy(false); }
  };
  return <SafeAreaView style={styles.safe}><KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled"><View style={styles.card}>
    <Text style={styles.brand}>FLOWSTOCK</Text><Text style={styles.title}>Créer un compte</Text><Text style={styles.sub}>Votre espace de gestion commence ici.</Text>
    <TextInput style={styles.input} placeholder="Nom complet" value={name} onChangeText={setName} autoCapitalize="words" />
    <TextInput style={styles.input} placeholder="Adresse e-mail" value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" />
    <TextInput style={styles.input} placeholder="Mot de passe (12 caractères minimum)" value={password} onChangeText={setPassword} secureTextEntry autoComplete="new-password" />
    {!!error && <Text style={styles.error}>{error}</Text>}
    <Pressable onPress={submit} disabled={busy} style={styles.button}>{busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Créer mon compte</Text>}</Pressable>
    <Pressable onPress={() => router.replace('/')} style={{ marginTop: 18 }}><Text style={styles.link}>J’ai déjà un compte · Se connecter</Text></Pressable>
  </View></ScrollView></KeyboardAvoidingView></SafeAreaView>;
}
const styles = StyleSheet.create({ safe: { flex: 1, backgroundColor: '#F5F7F5' }, content: { flexGrow: 1, justifyContent: 'center', padding: 22 }, card: { width: '100%', maxWidth: 440, alignSelf: 'center', backgroundColor: '#fff', borderRadius: 22, padding: 24, borderWidth: 1, borderColor: '#E3E9E4' }, brand: { color: '#078343', fontSize: 12, fontWeight: '800', letterSpacing: 2 }, title: { color: '#142039', fontSize: 29, fontWeight: '800', marginTop: 15 }, sub: { color: '#69736D', fontSize: 14, marginTop: 5, marginBottom: 22 }, input: { height: 52, borderWidth: 1, borderColor: '#D9E0DA', borderRadius: 13, paddingHorizontal: 14, marginBottom: 12, color: '#142039' }, error: { color: '#B63838', marginBottom: 12 }, button: { height: 52, borderRadius: 13, backgroundColor: '#078343', justifyContent: 'center', alignItems: 'center', marginTop: 4 }, buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' }, link: { textAlign: 'center', color: '#078343', fontWeight: '700' } });
