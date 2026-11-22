import { useState } from 'react';
import { ActivityIndicator, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/lib/auth-context';
import { changeMyPassword, updateMyProfile } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';

export default function ProfileScreen() {
  const router = useRouter();
  const { user, updateUser, signOut } = useAuth();
  const [nomComplet, setNomComplet] = useState(user?.nom_complet ?? '');
  const [ancien, setAncien] = useState('');
  const [nouveau, setNouveau] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const saveProfile = async () => {
    setBusy(true); setError(''); setNotice('');
    try { updateUser(await updateMyProfile({ nom_complet: nomComplet.trim() })); setNotice('Profil mis à jour.'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Modification impossible.'); }
    finally { setBusy(false); }
  };
  const savePassword = async () => {
    if (!ancien || !nouveau || !confirmation) { setError('Renseignez les trois champs du mot de passe.'); return; }
    if (nouveau !== confirmation) { setError('La confirmation ne correspond pas au nouveau mot de passe.'); return; }
    setBusy(true); setError(''); setNotice('');
    try { await changeMyPassword(ancien, nouveau); setAncien(''); setNouveau(''); setConfirmation(''); setNotice('Mot de passe modifié.'); }
    catch (e) { setError(e instanceof Error ? e.message : 'Modification impossible.'); }
    finally { setBusy(false); }
  };
  const disconnect = async () => { setBusy(true); setError(''); try { await signOut(); router.replace('/'); } catch (e) { setError(e instanceof Error ? e.message : 'Déconnexion impossible.'); } finally { setBusy(false); } };
  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Mon compte" subtitle={`${user?.email} · ${user?.role}`} />
    <FadeIn delay={130}><View style={ui.card}><Text style={ui.cardTitle}>Informations du profil</Text>
      <TextInput style={ui.input} value={nomComplet} onChangeText={setNomComplet} placeholder="Nom complet" />
      <Action label={busy ? '…' : 'Enregistrer le profil'} onPress={() => void saveProfile()} disabled={busy} />
    </View></FadeIn>
    <FadeIn delay={190}><View style={ui.card}><Text style={ui.cardTitle}>Changer le mot de passe</Text>
      <TextInput style={ui.input} value={ancien} onChangeText={setAncien} secureTextEntry placeholder="Mot de passe actuel" />
      <TextInput style={ui.input} value={nouveau} onChangeText={setNouveau} secureTextEntry placeholder="Nouveau mot de passe" />
      <TextInput style={ui.input} value={confirmation} onChangeText={setConfirmation} secureTextEntry placeholder="Confirmer le nouveau mot de passe" />
      <Action label={busy ? '…' : 'Modifier le mot de passe'} onPress={() => void savePassword()} disabled={busy} />
    </View></FadeIn>
    {!!error && <Text style={ui.error}>{error}</Text>}{!!notice && <Text style={styles.notice}>{notice}</Text>}
    <MotionPressable onPress={() => void disconnect()} disabled={busy} style={styles.signOut}>{busy ? <ActivityIndicator color="#B33C3C" /> : <Text style={styles.signOutText}>Se déconnecter</Text>}</MotionPressable>
  </ScrollView>;
}
const styles = StyleSheet.create({ notice: { color: '#078343', marginBottom: 12, fontWeight: '600' }, signOut: { alignSelf: 'center', padding: 14 }, signOutText: { color: '#B33C3C', fontWeight: '800' } });
