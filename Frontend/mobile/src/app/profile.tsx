import { useState } from 'react';
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '@/lib/auth-context';
import { changeMyPassword, updateMyProfile } from '@/lib/session-api';
import { Action, uiStyles as ui } from '@/components/resource-screen';
import { AppPageHeading } from '@/components/page-heading';
import { FadeIn, MotionPressable } from '@/components/motion';

function getInitials(name: string, email: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length > 1) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toLocaleUpperCase('fr-FR');
  if (parts.length === 1) return parts[0].slice(0, 2).toLocaleUpperCase('fr-FR');
  return email.slice(0, 2).toLocaleUpperCase('fr-FR') || 'FS';
}

export default function ProfileScreen() {
  const router = useRouter();
  const { user, updateUser, signOut } = useAuth();
  const [nomComplet, setNomComplet] = useState(user?.nom_complet ?? '');
  const [ancien, setAncien] = useState('');
  const [nouveau, setNouveau] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirmDisconnect, setConfirmDisconnect] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const roleLabel = user?.role === 'ADMIN' || user?.is_staff ? 'Administrateur' : 'Vendeur';
  const initials = getInitials(user?.nom_complet ?? '', user?.email ?? '');

  const saveProfile = async () => {
    setBusy(true); setError(''); setNotice('');
    try {
      const updatedUser = await updateMyProfile({ nom_complet: nomComplet.trim() });
      updateUser(updatedUser);
      setNomComplet(updatedUser.nom_complet);
      setNotice('Votre profil a été mis à jour.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Modification impossible.');
    } finally {
      setBusy(false);
    }
  };

  const savePassword = async () => {
    if (!ancien || !nouveau || !confirmation) { setError('Renseignez les trois champs du mot de passe.'); return; }
    if (nouveau !== confirmation) { setError('La confirmation ne correspond pas au nouveau mot de passe.'); return; }
    setBusy(true); setError(''); setNotice('');
    try {
      await changeMyPassword(ancien, nouveau);
      setAncien(''); setNouveau(''); setConfirmation('');
      setNotice('Votre mot de passe a été modifié.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Modification impossible.');
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async () => {
    setBusy(true); setError('');
    try {
      await signOut();
      router.replace('/');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Déconnexion impossible.');
    } finally {
      setBusy(false);
    }
  };

  return <ScrollView style={ui.page} contentContainerStyle={ui.content} keyboardShouldPersistTaps="handled">
    <AppPageHeading title="Mon compte" subtitle="Gérez vos informations personnelles et votre sécurité." />

    <FadeIn delay={100}>
      <View style={styles.identityCard}>
        <View style={styles.identityTop}>
          <View style={styles.avatar}><Text style={styles.avatarText}>{initials}</Text></View>
          <View style={styles.identityCopy}>
            <Text style={styles.identityName} numberOfLines={2}>{user?.nom_complet || 'Bienvenue'}</Text>
            <Text style={styles.identityEmail} numberOfLines={1}>{user?.email}</Text>
          </View>
          <View style={styles.roleBadge}><View style={styles.roleDot} /><Text style={styles.roleText}>{roleLabel}</Text></View>
        </View>
        <View style={styles.identityDivider} />
        <View style={styles.identityFooter}>
          <Text style={styles.identityFooterLabel}>Compte FlowStock</Text>
          <Text style={styles.identityFooterValue}>Actif</Text>
        </View>
      </View>
    </FadeIn>

    {!!error && <FadeIn><View accessibilityRole="alert" style={styles.messageError}><Text style={styles.messageErrorMark}>!</Text><Text style={styles.messageText}>{error}</Text></View></FadeIn>}
    {!!notice && <FadeIn><View accessibilityLiveRegion="polite" style={styles.messageSuccess}><Text style={styles.messageSuccessMark}>✓</Text><Text style={styles.messageText}>{notice}</Text></View></FadeIn>}

    <FadeIn delay={150}>
      <View style={styles.formCard}>
        <View style={styles.cardHeading}>
          <View style={[styles.cardIcon, styles.profileIcon]}><Text style={styles.profileIconText}>✦</Text></View>
          <View style={styles.cardHeadingCopy}>
            <Text style={styles.cardTitle}>Informations personnelles</Text>
            <Text style={styles.cardSubtitle}>Le nom affiché sur votre compte.</Text>
          </View>
        </View>
        <Text style={styles.fieldLabel}>Nom complet</Text>
        <TextInput
          style={styles.input}
          value={nomComplet}
          onChangeText={(value) => { setNomComplet(value); setError(''); setNotice(''); }}
          placeholder="Ex. Marie Rakoto"
          placeholderTextColor="#929B95"
          autoComplete="name"
          returnKeyType="done"
        />
        <Action label={busy ? 'Enregistrement…' : 'Enregistrer les modifications'} onPress={() => void saveProfile()} disabled={busy} />
      </View>
    </FadeIn>

    <FadeIn delay={210}>
      <View style={styles.formCard}>
        <View style={styles.cardHeading}>
          <View style={[styles.cardIcon, styles.securityIcon]}><Text style={styles.securityIconText}>⌑</Text></View>
          <View style={styles.cardHeadingCopy}>
            <Text style={styles.cardTitle}>Sécurité du compte</Text>
            <Text style={styles.cardSubtitle}>Choisissez un mot de passe que vous n’utilisez pas ailleurs.</Text>
          </View>
        </View>
        <Text style={styles.fieldLabel}>Mot de passe actuel</Text>
        <TextInput style={styles.input} value={ancien} onChangeText={setAncien} secureTextEntry placeholder="Saisissez votre mot de passe actuel" placeholderTextColor="#929B95" autoComplete="current-password" textContentType="password" />
        <Text style={styles.fieldLabel}>Nouveau mot de passe</Text>
        <TextInput style={styles.input} value={nouveau} onChangeText={setNouveau} secureTextEntry placeholder="Saisissez un nouveau mot de passe" placeholderTextColor="#929B95" autoComplete="new-password" textContentType="newPassword" />
        <Text style={styles.fieldLabel}>Confirmation</Text>
        <TextInput style={styles.input} value={confirmation} onChangeText={setConfirmation} secureTextEntry placeholder="Confirmez le nouveau mot de passe" placeholderTextColor="#929B95" autoComplete="new-password" textContentType="newPassword" />
        <Action label={busy ? 'Mise à jour…' : 'Mettre à jour le mot de passe'} onPress={() => void savePassword()} disabled={busy} />
      </View>
    </FadeIn>

    <FadeIn delay={270}>
      <View style={styles.signOutCard}>
        <View style={styles.signOutCopy}>
          <Text style={styles.signOutTitle}>Déconnexion</Text>
          <Text style={styles.signOutDescription}>Terminez votre session sur cet appareil.</Text>
        </View>
        <MotionPressable onPress={() => setConfirmDisconnect(true)} disabled={busy} style={[styles.signOutButton, busy && styles.disabled]} accessibilityRole="button">
          {busy ? <ActivityIndicator color="#B63838" /> : <Text style={styles.signOutText}>Se déconnecter</Text>}
        </MotionPressable>
      </View>
    </FadeIn>

    <Modal visible={confirmDisconnect} transparent animationType="fade" onRequestClose={() => setConfirmDisconnect(false)}>
      <View style={styles.modalBackdrop}>
        <View style={styles.confirmCard} accessibilityRole="alert">
          <View style={styles.confirmIcon}><Text style={styles.confirmIconText}>↗</Text></View>
          <Text style={styles.confirmTitle}>Se déconnecter ?</Text>
          <Text style={styles.confirmDescription}>Votre session FlowStock sera terminée sur cet appareil.</Text>
          <View style={styles.confirmActions}>
            <Pressable onPress={() => setConfirmDisconnect(false)} style={styles.keepButton} accessibilityRole="button">
              <Text style={styles.keepButtonText}>Non, rester</Text>
            </Pressable>
            <Pressable onPress={() => { setConfirmDisconnect(false); void disconnect(); }} style={styles.confirmLogoutButton} accessibilityRole="button">
              <Text style={styles.confirmLogoutText}>Oui, déconnecter</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  </ScrollView>;
}

const styles = StyleSheet.create({
  identityCard: { backgroundColor: '#E7F5EC', borderRadius: 20, padding: 20, marginBottom: 16, borderWidth: 1, borderColor: '#D4EBDD' },
  identityTop: { flexDirection: 'row', alignItems: 'center', gap: 13 },
  avatar: { width: 58, height: 58, borderRadius: 20, backgroundColor: '#FFFFFF', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#D4EBDD' },
  avatarText: { color: '#078343', fontSize: 18, fontWeight: '800', letterSpacing: 0.5 },
  identityCopy: { flex: 1, minWidth: 0 },
  identityName: { color: '#173D2B', fontSize: 17, fontWeight: '800' },
  identityEmail: { color: '#587162', fontSize: 12, marginTop: 4 },
  roleBadge: { flexDirection: 'row', alignItems: 'center', gap: 5, backgroundColor: '#FFFFFF', borderRadius: 20, paddingVertical: 7, paddingHorizontal: 9, borderWidth: 1, borderColor: '#D4EBDD' },
  roleDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#078343' },
  roleText: { color: '#17633A', fontSize: 10, fontWeight: '700' },
  identityDivider: { height: 1, backgroundColor: '#D4EBDD', marginTop: 18, marginBottom: 12 },
  identityFooter: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  identityFooterLabel: { color: '#668171', fontSize: 11 },
  identityFooterValue: { color: '#078343', fontSize: 11, fontWeight: '700' },
  messageError: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 13, borderRadius: 13, backgroundColor: '#FFF0F0', borderWidth: 1, borderColor: '#F3D1D1', marginBottom: 12 },
  messageSuccess: { flexDirection: 'row', alignItems: 'center', gap: 9, padding: 13, borderRadius: 13, backgroundColor: '#EAF7EE', borderWidth: 1, borderColor: '#CDEAD6', marginBottom: 12 },
  messageErrorMark: { color: '#B63838', fontSize: 15, fontWeight: '800' },
  messageSuccessMark: { color: '#078343', fontSize: 15, fontWeight: '800' },
  messageText: { flex: 1, color: '#465149', fontSize: 12, fontWeight: '600' },
  formCard: { backgroundColor: '#FFFFFF', borderRadius: 18, padding: 19, borderColor: '#E3E9E4', borderWidth: 1, marginBottom: 14 },
  cardHeading: { flexDirection: 'row', alignItems: 'center', gap: 11, marginBottom: 18 },
  cardIcon: { width: 40, height: 40, borderRadius: 13, alignItems: 'center', justifyContent: 'center' },
  profileIcon: { backgroundColor: '#E7F5EC' },
  profileIconText: { color: '#078343', fontSize: 18, fontWeight: '800' },
  securityIcon: { backgroundColor: '#EEF1F6' },
  securityIconText: { color: '#173D2B', fontSize: 21, fontWeight: '700' },
  cardHeadingCopy: { flex: 1 },
  cardTitle: { color: '#173D2B', fontSize: 15, fontWeight: '800' },
  cardSubtitle: { color: '#77827A', fontSize: 11, lineHeight: 16, marginTop: 3 },
  fieldLabel: { color: '#4F5A52', fontSize: 11, fontWeight: '700', marginBottom: 6 },
  input: { minHeight: 47, borderWidth: 1, borderColor: '#DDE4DE', borderRadius: 12, paddingHorizontal: 13, color: '#173D2B', marginBottom: 13, backgroundColor: '#FBFCFB', fontSize: 13 },
  signOutCard: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: '#FFFFFF', borderRadius: 17, padding: 17, borderWidth: 1, borderColor: '#F0DCDC', marginTop: 2 },
  signOutCopy: { flex: 1 },
  signOutTitle: { color: '#173D2B', fontSize: 14, fontWeight: '800' },
  signOutDescription: { color: '#77827A', fontSize: 11, marginTop: 4, lineHeight: 15 },
  signOutButton: { minHeight: 40, justifyContent: 'center', paddingHorizontal: 12, borderRadius: 11, backgroundColor: '#FFF0F0', borderWidth: 1, borderColor: '#F3D1D1' },
  signOutText: { color: '#B63838', fontSize: 11, fontWeight: '800' },
  disabled: { opacity: 0.55 },
  modalBackdrop: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24, backgroundColor: 'rgba(23,61,43,0.34)' },
  confirmCard: { width: '100%', maxWidth: 380, alignItems: 'center', padding: 24, borderRadius: 22, backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#DDE9DF', shadowColor: '#38704A', shadowOffset: { width: 0, height: 8 }, shadowOpacity: 0.12, shadowRadius: 20, elevation: 6 },
  confirmIcon: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: '#FFF0F0' },
  confirmIconText: { color: '#B63838', fontSize: 23, fontWeight: '800' },
  confirmTitle: { color: '#173D2B', fontSize: 18, fontWeight: '800', marginTop: 14 },
  confirmDescription: { color: '#65736A', fontSize: 13, textAlign: 'center', lineHeight: 19, marginTop: 7 },
  confirmActions: { flexDirection: 'row', alignSelf: 'stretch', gap: 10, marginTop: 22 },
  keepButton: { flex: 1, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#F0F8F2', borderWidth: 1, borderColor: '#DDE9DF' },
  keepButtonText: { color: '#17633A', fontSize: 12, fontWeight: '800' },
  confirmLogoutButton: { flex: 1, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 12, backgroundColor: '#B63838' },
  confirmLogoutText: { color: '#FFFFFF', fontSize: 12, fontWeight: '800' },
});
