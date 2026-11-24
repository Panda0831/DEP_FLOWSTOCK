import { StyleSheet, Text, TextInput, View } from 'react-native';

import { HitSize, Radius, Type } from '@/constants/theme';
import { MotionPressable } from '@/components/motion';
import { useAppTheme } from '@/hooks/use-app-theme';

/** Clearly labeled integer quantity entry with large one-tap adjustments. */
export function QuantityField({ label = 'Quantité *', value, onChange, hint, disabled = false }: {
  label?: string;
  value: string;
  onChange: (value: string) => void;
  hint?: string;
  disabled?: boolean;
}) {
  const t = useAppTheme();
  const update = (delta: number) => {
    const current = Number.parseInt(value, 10);
    onChange(String(Math.max(1, (Number.isFinite(current) ? current : 0) + delta)));
  };

  return (
    <View style={styles.wrap}>
      <Text style={[styles.label, { color: t.text }]}>{label}</Text>
      <View style={[styles.control, { backgroundColor: t.surface, borderColor: t.separator }]}>
        <MotionPressable
          onPress={() => update(-1)}
          disabled={disabled || Number(value) <= 1}
          style={[styles.step, { borderColor: t.separator }, (disabled || Number(value) <= 1) && styles.disabled]}
          accessibilityRole="button"
          accessibilityLabel={`Diminuer ${label.toLowerCase()}`}>
          <Text style={[styles.stepText, { color: t.tint }]}>−</Text>
        </MotionPressable>
        <TextInput
          value={value}
          onChangeText={(text) => onChange(text.replace(/[^0-9]/g, ''))}
          keyboardType="number-pad"
          selectTextOnFocus
          style={[styles.input, { color: t.text }]}
          accessibilityLabel={label}
          accessibilityHint={hint}
          editable={!disabled}
        />
        <MotionPressable
          onPress={() => update(1)}
          disabled={disabled}
          style={[styles.step, { borderColor: t.separator }, disabled && styles.disabled]}
          accessibilityRole="button"
          accessibilityLabel={`Augmenter ${label.toLowerCase()}`}>
          <Text style={[styles.stepText, { color: t.tint }]}>＋</Text>
        </MotionPressable>
      </View>
      {!!hint && <Text style={[styles.hint, { color: t.secondaryText }]}>{hint}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 14 },
  label: { ...Type.footnote, fontWeight: '600', marginBottom: 6 },
  control: { minHeight: HitSize, borderWidth: 1, borderRadius: Radius.control, flexDirection: 'row', alignItems: 'center', padding: 4 },
  step: { width: 40, height: 40, borderWidth: 1, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  stepText: { fontSize: 20, lineHeight: 24, fontWeight: '600' },
  input: { flex: 1, minWidth: 48, textAlign: 'center', fontSize: 17, fontWeight: '600', paddingVertical: 6 },
  hint: { ...Type.footnote, marginTop: 5 },
  disabled: { opacity: 0.4 },
});
