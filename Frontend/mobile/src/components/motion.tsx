import { useEffect, useRef, useState, type PropsWithChildren } from 'react';
import { AccessibilityInfo, Animated, Pressable, StyleSheet, View, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';

import { useAppTheme } from '@/hooks/use-app-theme';

/** One short entrance fade. Never loops, and disabled when Reduce Motion is on. */
export function FadeIn({ children, delay = 0, style }: PropsWithChildren<{ delay?: number; style?: StyleProp<ViewStyle> }>) {
  const [reduced, setReduced] = useState(false);
  const progress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    let active = true;
    void AccessibilityInfo.isReduceMotionEnabled().then((value) => {
      if (active) setReduced(value);
    });
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced);
    return () => {
      active = false;
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    if (reduced) {
      progress.setValue(1);
      return;
    }
    const animation = Animated.timing(progress, { toValue: 1, duration: 220, delay: Math.min(delay, 120), useNativeDriver: true });
    animation.start();
    return () => animation.stop();
  }, [delay, progress, reduced]);

  if (reduced) return <View style={style}>{children}</View>;
  return <Animated.View style={[{ opacity: progress }, style]}>{children}</Animated.View>;
}

/** A plain separator. Decorative dots and gradients were removed. */
export function BrandDivider({ style }: { style?: StyleProp<ViewStyle> }) {
  const t = useAppTheme();
  return <View style={[styles.divider, { backgroundColor: t.separator }, style]} />;
}

type MotionPressableProps = Omit<PressableProps, 'style'> & { style?: StyleProp<ViewStyle> };

/** Press feedback without scaling: predictable hit regions. */
export function MotionPressable({ style, ...props }: MotionPressableProps) {
  return <Pressable {...props} style={({ pressed }) => [style, pressed && styles.pressed]} />;
}

const styles = StyleSheet.create({
  pressed: { opacity: 0.75 },
  divider: { height: 1, width: '100%' },
});
