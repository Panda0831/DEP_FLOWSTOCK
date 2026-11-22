import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { api, type Page } from '@/lib/session-api';

export type ResourceField = { key: string; label: string; placeholder?: string; optional?: boolean };
type Resource = Record<string, unknown> & { public_id: string };

export function ResourceScreen({ title, subtitle, endpoint, fields, titleKey, subtitleKeys = [], canEdit = true, canDelete = canEdit }: {
  title: string; subtitle: string; endpoint: string; fields: ResourceField[]; titleKey: string; subtitleKeys?: string[]; canEdit?: boolean; canDelete?: boolean;
}) {
  const router = useRouter();
  const [items, setItems] = useState<Resource[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<Resource | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const result = await api.get<Resource[] | Page<Resource>>(endpoint);
      setItems(Array.isArray(result) ? result : result.results);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, [endpoint]);
  useEffect(() => { void refresh(); }, [refresh]);

  const startEdit = (item: Resource) => { setEditing(item); setValues(Object.fromEntries(fields.map((f) => [f.key, String(item[f.key] ?? '')]))); };
  const resetForm = () => { setEditing(null); setValues({}); };
  const save = async () => {
    const missing = fields.find((f) => !f.optional && !values[f.key]?.trim());
    if (missing) { setError(`Le champ « ${missing.label} » est obligatoire.`); return; }
    setSaving(true); setError('');
    const payload = Object.fromEntries(fields.map((f) => [f.key, values[f.key]?.trim() || (f.optional ? null : '')]));
    try {
      if (editing) await api.patch(`${endpoint}${editing.public_id}/`, payload);
      else await api.post(endpoint, payload);
      resetForm(); await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : 'Enregistrement impossible.'); }
    finally { setSaving(false); }
  };
  const remove = (item: Resource) => Alert.alert('Supprimer cet élément ?', String(item[titleKey] || ''), [
    { text: 'Annuler', style: 'cancel' },
    { text: 'Supprimer', style: 'destructive', onPress: () => { void api.delete(`${endpoint}${item.public_id}/`).then(refresh).catch((e) => setError(e.message)); } },
  ]);

  return <ScrollView style={styles.page} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
    <View style={styles.top}><Pressable onPress={() => router.back()}><Text style={styles.back}>‹ Retour</Text></Pressable><Text style={styles.brand}>FLOWSTOCK</Text></View>
    <Text style={styles.title}>{title}</Text><Text style={styles.subtitle}>{subtitle}</Text>
    {canEdit && <View style={styles.card}>
      <Text style={styles.cardTitle}>{editing ? 'Modifier' : 'Ajouter'}</Text>
      {fields.map((field) => <TextInput key={field.key} value={values[field.key] || ''} onChangeText={(value) => setValues((old) => ({ ...old, [field.key]: value }))} placeholder={field.placeholder || field.label} placeholderTextColor="#89919E" style={styles.input} />)}
      {!!error && <Text style={styles.error}>{error}</Text>}
      <View style={styles.actions}><Action label={saving ? 'Enregistrement…' : editing ? 'Enregistrer' : 'Ajouter'} onPress={save} disabled={saving} /><Pressable onPress={resetForm} style={styles.ghost}><Text style={styles.ghostText}>{editing ? 'Annuler' : 'Effacer'}</Text></Pressable></View>
    </View>}
    {error && !canEdit ? <Text style={styles.error}>{error}</Text> : null}
    <View style={styles.listHeader}><Text style={styles.section}>Éléments</Text><Pressable onPress={() => void refresh()}><Text style={styles.refresh}>Actualiser</Text></Pressable></View>
    {loading ? <ActivityIndicator color="#078343" style={{ marginTop: 28 }} /> : items.length === 0 ? <Text style={styles.empty}>Aucun élément trouvé.</Text> : items.map((item) => <View key={item.public_id} style={styles.row}>
      <View style={{ flex: 1 }}><Text style={styles.rowTitle}>{String(item[titleKey] ?? 'Sans nom')}</Text>{subtitleKeys.map((key) => <Text key={key} style={styles.rowSub}>{String(item[key] ?? '—')}</Text>)}</View>
      {canEdit && <View style={styles.rowActions}><Pressable onPress={() => startEdit(item)}><Text style={styles.actionText}>Modifier</Text></Pressable>{canDelete && <Pressable onPress={() => remove(item)}><Text style={[styles.actionText, { color: '#B63838' }]}>Supprimer</Text></Pressable>}</View>}
    </View>)}
  </ScrollView>;
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#F5F7F5' }, content: { width: '100%', maxWidth: 650, alignSelf: 'center', padding: 20, paddingBottom: 48 },
  top: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 25 }, back: { color: '#078343', fontWeight: '700', fontSize: 15 }, brand: { color: '#078343', letterSpacing: 1.8, fontWeight: '800', fontSize: 12 },
  title: { color: '#142039', fontSize: 29, fontWeight: '800' }, subtitle: { color: '#6B7380', fontSize: 14, marginTop: 6, marginBottom: 20 }, card: { backgroundColor: '#fff', borderRadius: 18, padding: 18, borderColor: '#E3E9E4', borderWidth: 1, marginBottom: 22 }, cardTitle: { color: '#142039', fontSize: 17, fontWeight: '700', marginBottom: 13 }, input: { height: 48, borderWidth: 1, borderColor: '#D9E0DA', borderRadius: 12, paddingHorizontal: 13, color: '#142039', marginBottom: 10, backgroundColor: '#FCFDFC' },
  actions: { flexDirection: 'row', alignItems: 'center', gap: 10, marginTop: 4 }, button: { minHeight: 44, paddingHorizontal: 18, backgroundColor: '#078343', borderRadius: 12, alignItems: 'center', justifyContent: 'center' }, buttonText: { color: '#fff', fontSize: 14, fontWeight: '700' }, ghost: { paddingHorizontal: 12, paddingVertical: 10 }, ghostText: { color: '#657064', fontWeight: '600' }, error: { color: '#B63838', marginBottom: 12, fontSize: 13 }, listHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }, section: { color: '#142039', fontSize: 18, fontWeight: '700' }, refresh: { color: '#078343', fontWeight: '700' }, empty: { color: '#79827C', textAlign: 'center', marginVertical: 28 }, row: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', borderWidth: 1, borderColor: '#E6EBE6', borderRadius: 15, padding: 15, marginBottom: 9, gap: 12 }, rowTitle: { color: '#17233B', fontWeight: '700', fontSize: 15 }, rowSub: { color: '#758079', fontSize: 13, marginTop: 3 }, rowActions: { gap: 10, alignItems: 'flex-end' }, actionText: { color: '#078343', fontWeight: '700', fontSize: 12 },
});
export const uiStyles = styles;
export function Action({ label, onPress, disabled }: { label: string; onPress: () => void; disabled?: boolean }) {
  return <Pressable disabled={disabled} onPress={onPress} style={({ pressed }) => [styles.button, pressed && { opacity: 0.8 }, disabled && { opacity: 0.6 }]}><Text style={styles.buttonText}>{label}</Text></Pressable>;
}
