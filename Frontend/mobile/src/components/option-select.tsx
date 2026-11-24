import { useMemo, useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { MotionPressable } from '@/components/motion';
import { HitSize, Radius, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export type SelectOption = { value: string; label: string; detail?: string };

export function toOptions<T extends { public_id: string }>(
  items: T[],
  label: (item: T) => string,
  detail?: (item: T) => string | undefined,
): SelectOption[] {
  return items.map((item) => ({ value: item.public_id, label: label(item), detail: detail?.(item) }));
}

/** A compact field with a searchable, paginated list. No horizontal chip strip. */
export function OptionSelect({ label, options, value, onChange, placeholder = 'Choisir…', optional = false, pageSize = 6 }: {
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  optional?: boolean;
  pageSize?: number;
}) {
  const t = useAppTheme();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(0);

  const selected = options.find((option) => option.value === value);
  const filtered = useMemo(() => {
    const needle = query.trim().toLocaleLowerCase('fr-FR');
    if (!needle) return options;
    return options.filter((option) => `${option.label} ${option.detail || ''}`.toLocaleLowerCase('fr-FR').includes(needle));
  }, [options, query]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(currentPage * pageSize, (currentPage + 1) * pageSize);
  const needsSearch = options.length > pageSize;
  const canOpen = options.length > 0 || optional;

  const choose = (next: string) => {
    onChange(next);
    setOpen(false);
    setQuery('');
    setPage(0);
  };

  return (
    <View style={styles.wrap}>
      <Text style={[styles.label, { color: t.text }]}>{label}{optional ? ' · facultatif' : ' *'}</Text>
      <MotionPressable
        onPress={() => canOpen && setOpen((current) => !current)}
        style={[styles.field, { backgroundColor: t.surface, borderColor: t.separator }, !canOpen && styles.unavailable]}
        disabled={!canOpen}
        accessibilityRole="button"
        accessibilityLabel={`${label}, ${optional ? 'facultatif' : 'obligatoire'} : ${selected?.label || placeholder}`}
        accessibilityState={{ expanded: open, disabled: !canOpen }}>
        <Text style={[styles.fieldText, { color: selected ? t.text : t.secondaryText }]} numberOfLines={1}>
          {selected?.label || placeholder}
        </Text>
        <Text style={[styles.chevron, { color: t.tint }]}>{open ? '▴' : '▾'}</Text>
      </MotionPressable>

      {open && (
        <View style={[styles.panel, { backgroundColor: t.surface, borderColor: t.separator }]}>
          {needsSearch && <TextInput
            value={query}
            onChangeText={(text) => { setQuery(text); setPage(0); }}
            placeholder={`Rechercher ${label.toLowerCase()}`}
            placeholderTextColor={t.secondaryText}
            style={[styles.search, { color: t.text, borderColor: t.separator }]}
            accessibilityLabel={`Rechercher ${label.toLowerCase()}`}
          />}

          {optional && (
            <MotionPressable onPress={() => choose('')} style={styles.row} accessibilityRole="button">
              <Text style={[styles.rowText, { color: value ? t.text : t.tint }]}>Aucun</Text>
              {!value && <Text style={[styles.check, { color: t.tint }]}>✓</Text>}
            </MotionPressable>
          )}

          {visible.map((option) => {
            const active = option.value === value;
            return (
              <MotionPressable
                key={option.value}
                onPress={() => choose(option.value)}
                style={styles.row}
                accessibilityRole="button"
                accessibilityState={{ selected: active }}>
                <View style={styles.rowTextWrap}>
                  <Text style={[styles.rowText, { color: active ? t.tint : t.text }]} numberOfLines={1}>{option.label}</Text>
                  {!!option.detail && <Text style={[styles.rowDetail, { color: t.secondaryText }]} numberOfLines={1}>{option.detail}</Text>}
                </View>
                {active && <Text style={[styles.check, { color: t.tint }]}>✓</Text>}
              </MotionPressable>
            );
          })}

          {filtered.length === 0 && <Text style={[styles.empty, { color: t.secondaryText }]}>Aucun résultat</Text>}

          {pageCount > 1 && <View style={styles.pager}>
            <MotionPressable
              onPress={() => setPage((current) => Math.max(0, current - 1))}
              disabled={currentPage === 0}
              style={[styles.pageButton, currentPage === 0 && styles.disabled]}
              accessibilityRole="button"
              accessibilityLabel="Page précédente">
              <Text style={[styles.pageText, { color: t.tint }]}>‹ Précédent</Text>
            </MotionPressable>
            <Text style={[styles.pageCount, { color: t.secondaryText }]}>{currentPage + 1} / {pageCount}</Text>
            <MotionPressable
              onPress={() => setPage((current) => Math.min(pageCount - 1, current + 1))}
              disabled={currentPage >= pageCount - 1}
              style={[styles.pageButton, currentPage >= pageCount - 1 && styles.disabled]}
              accessibilityRole="button"
              accessibilityLabel="Page suivante">
              <Text style={[styles.pageText, { color: t.tint }]}>Suivant ›</Text>
            </MotionPressable>
          </View>}
        </View>
      )}
      {!canOpen && <Text style={[styles.helper, { color: t.secondaryText }]}>Aucune option disponible pour le moment.</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 12 },
  label: { ...Type.footnote, fontWeight: '600', marginBottom: 6 },
  field: { minHeight: HitSize, borderWidth: 1, borderRadius: Radius.control, paddingHorizontal: 14, flexDirection: 'row', alignItems: 'center' },
  fieldText: { ...Type.body, flex: 1 },
  chevron: { fontSize: 16, marginLeft: 10 },
  panel: { marginTop: 6, borderWidth: 1, borderRadius: Radius.card, padding: 8 },
  search: { minHeight: HitSize, borderWidth: 1, borderRadius: Radius.control, paddingHorizontal: 12, fontSize: Type.body.fontSize, marginBottom: 4 },
  row: { minHeight: HitSize, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 6 },
  rowTextWrap: { flex: 1, paddingRight: 8 },
  rowText: { ...Type.body, fontWeight: '600' },
  rowDetail: { ...Type.footnote, marginTop: 1 },
  check: { fontSize: 18, fontWeight: '700' },
  empty: { ...Type.footnote, textAlign: 'center', paddingVertical: 18 },
  pager: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: 'transparent', paddingTop: 4 },
  pageButton: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 8 },
  pageText: { ...Type.footnote, fontWeight: '600' },
  pageCount: { ...Type.footnote },
  disabled: { opacity: 0.4 },
  unavailable: { opacity: 0.65 },
  helper: { ...Type.footnote, marginTop: 6 },
});
