import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { HitSize, Radius, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';
import { MotionPressable } from '@/components/motion';

type ScreenStateProps = {
  type: 'loading' | 'empty' | 'error' | 'success';
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  compact?: boolean;
};

export function ScreenState({
  type,
  title,
  description,
  actionLabel,
  onAction,
  compact = false,
}: ScreenStateProps) {
  const t = useAppTheme();
  const isError = type === 'error';
  const isSuccess = type === 'success';

  return (
    <View
      style={[
        styles.container,
        compact && styles.compact,
        isError && { backgroundColor: t.dangerSurface },
        isSuccess && { backgroundColor: t.tintSurface },
      ]}
      accessibilityRole={isError ? 'alert' : 'summary'}
      accessibilityLiveRegion={isError || isSuccess ? 'polite' : 'none'}>
      {type === 'loading' && (
        <ActivityIndicator
          color={t.tint}
          style={styles.indicator}
          accessibilityLabel={title}
        />
      )}
      <Text style={[styles.title, compact && styles.compactTitle, { color: isError ? t.danger : t.text }]}>{title}</Text>
      {!!description && <Text style={[styles.description, compact && styles.compactDescription, { color: t.secondaryText }]}>{description}</Text>}
      {!!actionLabel && !!onAction && (
        <MotionPressable
          onPress={onAction}
          style={[styles.action, { borderColor: t.separator }]}
          accessibilityRole="button"
          accessibilityLabel={actionLabel}>
          <Text style={[styles.actionText, { color: t.tint }]}>{actionLabel}</Text>
        </MotionPressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 24,
    borderRadius: Radius.card,
    marginBottom: 16,
  },
  compact: { alignItems: 'flex-start', paddingHorizontal: 14, paddingVertical: 12, borderRadius: Radius.control },
  indicator: { marginBottom: 10 },
  title: { ...Type.body, fontWeight: '600', textAlign: 'center' },
  description: { ...Type.footnote, textAlign: 'center', marginTop: 4, maxWidth: 420 },
  compactTitle: { textAlign: 'left' },
  compactDescription: { textAlign: 'left' },
  action: {
    minHeight: HitSize,
    justifyContent: 'center',
    paddingHorizontal: 14,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: Radius.control,
    marginTop: 12,
  },
  actionText: { ...Type.footnote, fontWeight: '600' },
});
