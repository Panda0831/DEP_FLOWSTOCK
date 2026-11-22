import { useEffect, useRef, type PropsWithChildren } from 'react';
import { Animated, Pressable, StyleSheet, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';

export function FadeIn({ children, delay = 0, style }: PropsWithChildren<{ delay?: number; style?: StyleProp<ViewStyle> }>) {
  const progress = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const animation = Animated.timing(progress, { toValue: 1, duration: 440, delay, useNativeDriver: true });
    animation.start();
    return () => animation.stop();
  }, [delay, progress]);
  return <Animated.View style={[{ opacity: progress, transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [10, 0] }) }] }, style]}>{children}</Animated.View>;
}

type MotionPressableProps = Omit<PressableProps, 'style'> & { style?: StyleProp<ViewStyle> };

export function MotionPressable({ style, ...props }: MotionPressableProps) {
  return <Pressable {...props} style={({ pressed }) => [style, pressed && styles.pressed]} />;
}

const styles = StyleSheet.create({
  pressed: { opacity: 0.88, transform: [{ scale: 0.98 }] },
});
