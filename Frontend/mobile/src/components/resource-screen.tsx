import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { ActivityIndicator, Alert, Modal, Platform, ScrollView, StyleSheet, Text, TextInput, View, type TextInputProps } from 'react-native';

import { api, fetchAll } from '@/lib/session-api';
import { HitSize, Radius, Type } from '@/constants/theme';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';
import { MotionPressable } from '@/components/motion';
import { AppPageHeading } from '@/components/page-heading';
import { OptionSelect } from '@/components/option-select';
import { LIST_PAGE_SIZE, ShowMore } from '@/components/show-more';
import { useAutoOpenForm } from '@/components/form-disclosure';

export type ResourceOption = { value: string; label: string };
export type ResourceField = { key: string; label: string; placeholder?: string; hint?: string; keyboardType?: TextInputProps['keyboardType']; optional?: boolean; clearToNull?: boolean; options?: ResourceOption[] };
export type ResourceItem = Record<string, unknown> & { public_id: string };

function formatResourceValue(key: string, value: unknown) {
  if (value === null || value === undefined || value === '') return '—';
  const normalizedKey = key.toLocaleLowerCase('fr-FR');
  if (normalizedKey.includes('date')) {
    const raw = String(value);
    const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(raw) ? `${raw}T00:00:00` : raw);
    if (!Number.isNaN(date.getTime())) return date.toLocaleDateString('fr-FR', { dateStyle: 'medium' });
  }
  if (['montant', 'prixvente', 'prixachat'].includes(normalizedKey)) {
    const amount = Number(value);
    if (Number.isFinite(amount)) return `${amount.toLocaleString('fr-FR')} Ar`;
  }
  return String(value);
}

/** Shared surface styles. Other screens reuse these so one change updates them all. */
export const uiStyles = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#F3F7F5' },
  content: { width: '100%', maxWidth: 720, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 20, paddingBottom: 32 },
  card: { backgroundColor: '#FFFFFF', borderRadius: Radius.card, borderWidth: 1, borderColor: '#DCE7E2', padding: 16, marginBottom: 20 },
  cardTitle: { ...Type.headline, color: '#18332F' },
  cardDescription: { ...Type.footnote, color: '#526864', marginTop: 4, marginBottom: 16 },
  input: { minHeight: HitSize, borderWidth: 1, borderColor: '#DCE7E2', borderRadius: Radius.control, paddingHorizontal: 14, fontSize: Type.body.fontSize, color: '#18332F', marginBottom: 12, backgroundColor: '#FFFFFF' },
  section: { ...Type.headline, color: '#18332F' },
  refresh: { color: '#11645D', fontSize: 15, fontWeight: '600', minHeight: HitSize, textAlignVertical: 'center' },
  empty: { color: '#526864', fontSize: 15, textAlign: 'center', marginVertical: 32 },
  error: { color: '#A43D32', fontSize: 14, lineHeight: 20, marginBottom: 12 },
  button: { minHeight: HitSize, paddingHorizontal: 20, backgroundColor: '#11645D', borderRadius: Radius.control, alignItems: 'center', justifyContent: 'center' },
  buttonText: { color: '#FFFFFF', fontSize: 15, fontWeight: '600' },
});

export function Action({ label, onPress, disabled, variant = 'primary' }: { label: string; onPress: () => void; disabled?: boolean; variant?: 'primary' | 'secondary' | 'danger' }) {
  const t = useAppTheme();
  const secondary = variant === 'secondary';
  const danger = variant === 'danger';
  return (
    <MotionPressable
      disabled={disabled}
      onPress={onPress}
      style={[uiStyles.button, secondary && { backgroundColor: 'transparent', borderWidth: 1, borderColor: t.separator }, danger && { backgroundColor: t.dangerSurface, borderWidth: 1, borderColor: t.dangerSurface }, disabled && { opacity: 0.5 }]}
      accessibilityRole="button"
      accessibilityLabel={label}>
      <Text style={[uiStyles.buttonText, secondary && { color: t.tint }, danger && { color: t.danger }]}>{label}</Text>
    </MotionPressable>
  );
}

const makeStyles = (t: AppTheme) => StyleSheet.create({
  page: { flex: 1, backgroundColor: t.background },
  headingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 },
  addButton: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 14, backgroundColor: t.tint, borderRadius: Radius.control },
  addText: { color: t.onTint, fontSize: 15, fontWeight: '600' },
  card: { backgroundColor: t.surface, borderRadius: Radius.card, borderWidth: 1, borderColor: t.separator, padding: 16, marginBottom: 16 },
  fieldLabel: { ...Type.footnote, fontWeight: '600', color: t.text, marginBottom: 6, marginTop: 8 },
  fieldHint: { ...Type.footnote, color: t.secondaryText, marginTop: 5, marginBottom: 8 },
  input: { minHeight: HitSize, borderWidth: 1, borderColor: t.separator, borderRadius: Radius.control, paddingHorizontal: 14, fontSize: Type.body.fontSize, color: t.text, backgroundColor: t.surface },
  sheet: { flex: 1, backgroundColor: t.background, padding: 20 },
  sheetHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  sheetTitle: { ...Type.headline, color: t.text },
  sheetDescription: { ...Type.footnote, color: t.secondaryText, marginTop: -10, marginBottom: 18 },
  close: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 8 },
  closeText: { color: t.tint, fontSize: 15, fontWeight: '600' },
  fieldGroupTitle: { ...Type.headline, color: t.text, marginBottom: 8 },
  optionalToggle: { minHeight: HitSize, justifyContent: 'center', marginTop: 6, marginBottom: 8 },
  optionalToggleText: { color: t.tint, fontSize: 15, fontWeight: '600' },
  listHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  section: { ...Type.headline, color: t.text },
  refresh: { color: t.tint, fontSize: 14, fontWeight: '600', minHeight: HitSize, textAlignVertical: 'center' },
  row: { backgroundColor: t.surface, borderRadius: Radius.card, borderWidth: 1, borderColor: t.separator, padding: 16, marginBottom: 10 },
  rowTitle: { ...Type.body, fontWeight: '600', color: t.text },
  rowSub: { ...Type.footnote, color: t.secondaryText, marginTop: 3 },
  rowActions: { flexDirection: 'row', gap: 16, marginTop: 12 },
  rowMetric: { minWidth: 86, alignItems: 'flex-end', justifyContent: 'center', paddingLeft: 12 },
  metricValue: { ...Type.headline, color: t.tint },
  metricLabel: { ...Type.footnote, color: t.secondaryText, marginTop: 2, textAlign: 'right' },
  metricLow: { color: t.danger },
  search: { minHeight: HitSize, borderWidth: 1, borderColor: t.separator, borderRadius: Radius.control, paddingHorizontal: 14, fontSize: Type.body.fontSize, color: t.text, backgroundColor: t.surface, marginBottom: 12 },
  actionText: { color: t.tint, fontSize: 14, fontWeight: '600' },
  deleteText: { color: t.danger },
  empty: { ...Type.body, color: t.secondaryText, textAlign: 'center', marginVertical: 28 },
  error: { color: t.danger, fontSize: 14, lineHeight: 20, marginBottom: 12 },
  loader: { marginVertical: 24 },
});

export function ResourceScreen({ title, subtitle, endpoint, fields, titleKey, subtitleKeys = [], listTitle = 'Éléments', emptyText = 'Aucun élément trouvé.', itemMarker, canEdit = true, canDelete = canEdit, canView = true, onCreated, searchable = false, summary, itemMetric }: {
  title: string; subtitle: string; endpoint: string; fields: ResourceField[]; titleKey: string; subtitleKeys?: string[]; listTitle?: string; emptyText?: string; itemMarker?: string; canEdit?: boolean; canDelete?: boolean; canView?: boolean; onCreated?: (item: ResourceItem) => void; searchable?: boolean; summary?: ReactNode; itemMetric?: (item: ResourceItem) => { value: string; label: string; warning?: boolean } | undefined;
}) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const [items, setItems] = useState<ResourceItem[]>([]);
  const [limit, setLimit] = useState(LIST_PAGE_SIZE);
  const [values, setValues] = useState<Record<string, string>>({});
  const autoOpen = useAutoOpenForm();
  const [editing, setEditing] = useState<ResourceItem | null>(null);
  const [formOpen, setFormOpen] = useState(autoOpen && canEdit);
  const [optionalOpen, setOptionalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

  const refresh = useCallback(async () => {
    if (!canView) { setItems([]); setLimit(LIST_PAGE_SIZE); setError('Cette section est réservée aux administrateurs.'); setLoading(false); return; }
    setLoading(true); setError('');
    try {
      setItems(await fetchAll<ResourceItem>(endpoint));
      setLimit(LIST_PAGE_SIZE);
    } catch (e) { setError(e instanceof Error ? e.message : 'Chargement impossible.'); }
    finally { setLoading(false); }
  }, [canView, endpoint]);
  useEffect(() => { void refresh(); }, [refresh]);

  const closeForm = () => { setFormOpen(false); setEditing(null); setValues({}); setOptionalOpen(false); setError(''); };
  const startEdit = (item: ResourceItem) => {
    setEditing(item);
    const nextValues = Object.fromEntries(fields.map((f) => [f.key, String(item[f.key] ?? '')]));
    setValues(nextValues);
    setOptionalOpen(fields.some((field) => field.optional && !!nextValues[field.key]?.trim()));
    setFormOpen(true);
    setError('');
  };
  const startCreate = () => { setEditing(null); setValues({}); setOptionalOpen(false); setFormOpen(true); setError(''); };

  const missingRequired = fields.find((f) => !f.optional && !values[f.key]?.trim());

  const save = async () => {
    if (missingRequired) { setError(`Le champ « ${missingRequired.label} » est obligatoire.`); return; }
    setSaving(true); setError('');
    const payload: Record<string, unknown> = {};
    for (const field of fields) {
      const value = values[field.key]?.trim();
      if (!value && field.optional) {
        if (field.clearToNull) payload[field.key] = null;
        continue;
      }
      payload[field.key] = value || '';
    }
    try {
      const created = editing
        ? await api.patch<ResourceItem>(`${endpoint}${editing.public_id}/`, payload)
        : await api.post<ResourceItem>(endpoint, payload);
      const wasEditing = !!editing;
      closeForm();
      await refresh();
      if (!wasEditing) onCreated?.(created);
    } catch (e) { setError(e instanceof Error ? e.message : 'Enregistrement impossible.'); }
    finally { setSaving(false); }
  };

  const remove = (item: ResourceItem) => Alert.alert('Supprimer cet élément ?', String(item[titleKey] || ''), [
    { text: 'Annuler', style: 'cancel' },
    { text: 'Supprimer', style: 'destructive', onPress: () => { void api.delete(`${endpoint}${item.public_id}/`).then(refresh).catch((e) => setError(e.message)); } },
  ]);

  const requiredFields = fields.filter((field) => !field.optional);
  const optionalFields = fields.filter((field) => field.optional);
  const filteredItems = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('fr-FR');
    if (!needle) return items;
    return items.filter((item) => [titleKey, ...subtitleKeys].some((key) => String(item[key] ?? '').toLocaleLowerCase('fr-FR').includes(needle)));
  }, [items, query, subtitleKeys, titleKey]);
  const renderField = (field: ResourceField) => field.options ? (
    <OptionSelect
      key={field.key}
      label={field.label}
      options={field.options}
      value={values[field.key] || ''}
      onChange={(value) => setValues((old) => ({ ...old, [field.key]: value }))}
      optional={field.optional}
    />
  ) : (
    <View key={field.key}>
      <Text style={styles.fieldLabel}>{field.label}{field.optional ? '' : ' *'}</Text>
      <TextInput
        value={values[field.key] || ''}
        onChangeText={(value) => setValues((old) => ({ ...old, [field.key]: value }))}
        placeholder={field.placeholder || field.label}
        placeholderTextColor={t.secondaryText}
        keyboardType={field.keyboardType}
        selectTextOnFocus={field.keyboardType === 'number-pad' || field.keyboardType === 'decimal-pad'}
        accessibilityLabel={field.label}
        accessibilityHint={field.hint}
        style={styles.input}
      />
      {!!field.hint && <Text style={styles.fieldHint}>{field.hint}</Text>}
    </View>
  );

  return (
    <ScrollView style={styles.page} contentContainerStyle={uiStyles.content} keyboardShouldPersistTaps="handled">
      <AppPageHeading title={title} subtitle={subtitle} />
      {summary}
      {canEdit && (
        <View style={styles.headingRow}>
          <Text style={styles.section}>{listTitle}</Text>
          <MotionPressable onPress={startCreate} style={styles.addButton} accessibilityRole="button" accessibilityLabel={`Ajouter ${title.toLowerCase()}`}>
            <Text style={styles.addText}>Ajouter</Text>
          </MotionPressable>
        </View>
      )}
      {!canEdit && <View style={styles.listHeader}><Text style={styles.section}>{listTitle}</Text></View>}
      {searchable && <TextInput value={query} onChangeText={setQuery} placeholder={`Rechercher ${title.toLocaleLowerCase('fr-FR')}`} placeholderTextColor={t.secondaryText} style={styles.search} accessibilityLabel={`Rechercher ${title.toLocaleLowerCase('fr-FR')}`} returnKeyType="search" />}
      {error && !formOpen && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
      {loading ? <ActivityIndicator color={t.tint} style={styles.loader} />
        : filteredItems.length === 0 ? <Text style={styles.empty}>{items.length ? 'Aucun résultat pour cette recherche.' : emptyText}</Text>
        : filteredItems.slice(0, limit).map((item) => {
          const metric = itemMetric?.(item);
          return <View key={item.public_id} style={styles.row}>
            <View style={{ flex: 1 }}>
              <Text style={styles.rowTitle}>{String(item[titleKey] ?? 'Sans nom')}</Text>
              {subtitleKeys.map((key) => <Text key={key} style={styles.rowSub}>{formatResourceValue(key, item[key])}</Text>)}
              {canEdit && <View style={styles.rowActions}>
                <MotionPressable onPress={() => startEdit(item)} accessibilityRole="button" accessibilityLabel={`Modifier ${String(item[titleKey] ?? '')}`}><Text style={styles.actionText}>Modifier</Text></MotionPressable>
                {canDelete && <MotionPressable onPress={() => remove(item)} accessibilityRole="button" accessibilityLabel={`Supprimer ${String(item[titleKey] ?? '')}`}><Text style={[styles.actionText, styles.deleteText]}>Supprimer</Text></MotionPressable>}
              </View>}
            </View>
            {!!metric && <View style={styles.rowMetric} accessibilityLabel={`${metric.value} ${metric.label}`}>
              <Text style={[styles.metricValue, metric.warning && styles.metricLow]}>{metric.value}</Text>
              <Text style={[styles.metricLabel, metric.warning && styles.metricLow]}>{metric.label}</Text>
            </View>}
          </View>;
        })}
      {!loading && <ShowMore remaining={filteredItems.length - limit} onPress={() => setLimit((current) => current + LIST_PAGE_SIZE)} />}
      {!loading && filteredItems.length > 0 && (
        <View style={styles.listHeader}>
          <MotionPressable onPress={() => void refresh()} accessibilityRole="button"><Text style={styles.refresh}>Actualiser</Text></MotionPressable>
        </View>
      )}

      <Modal
        visible={formOpen}
        animationType="slide"
        presentationStyle={Platform.OS === 'ios' ? 'pageSheet' : 'overFullScreen'}
        onRequestClose={closeForm}>
        <ScrollView style={styles.sheet} keyboardShouldPersistTaps="handled">
          <View style={styles.sheetHeader}>
            <Text style={styles.sheetTitle}>{editing ? `Modifier ${title.toLowerCase()}` : `Nouveau · ${title.toLowerCase()}`}</Text>
            <MotionPressable onPress={closeForm} style={styles.close} accessibilityRole="button" accessibilityLabel="Annuler et fermer"><Text style={styles.closeText}>Annuler</Text></MotionPressable>
          </View>
          <Text style={styles.sheetDescription}>Renseignez les champs marqués d’un astérisque.</Text>
          {!!requiredFields.length && <Text style={styles.fieldGroupTitle}>Informations principales</Text>}
          {requiredFields.map(renderField)}
          {!!optionalFields.length && <>
            <MotionPressable onPress={() => setOptionalOpen((current) => !current)} style={styles.optionalToggle} accessibilityRole="button" accessibilityState={{ expanded: optionalOpen }}>
              <Text style={styles.optionalToggleText}>{optionalOpen ? 'Masquer les détails facultatifs' : 'Ajouter des détails facultatifs'}</Text>
            </MotionPressable>
            {optionalOpen && optionalFields.map(renderField)}
          </>}
          {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
          <View style={{ marginTop: 12 }}>
            <Action label={saving ? 'Enregistrement…' : editing ? 'Enregistrer' : 'Ajouter'} onPress={() => void save()} disabled={saving || !!missingRequired} />
          </View>
        </ScrollView>
      </Modal>
    </ScrollView>
  );
}
