import { useEffect, useRef, useState, type PropsWithChildren } from 'react';
import { Animated, Pressable, StyleSheet, View, type PressableProps, type StyleProp, type ViewStyle } from 'react-native';

export function FadeIn({ children, delay = 0, style }: PropsWithChildren<{ delay?: number; style?: StyleProp<ViewStyle> }>) {
  const progress = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const animation = Animated.timing(progress, { toValue: 1, duration: 440, delay, useNativeDriver: true });
    animation.start();
    return () => animation.stop();
  }, [delay, progress]);
  return <Animated.View style={[{ opacity: progress, transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [10, 0] }) }] }, style]}>{children}</Animated.View>;
}

export function BrandDivider({ style }: { style?: StyleProp<ViewStyle> }) {
  const progress = useRef(new Animated.Value(0)).current;
  const [trackWidth, setTrackWidth] = useState(0);
  useEffect(() => {
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(progress, { toValue: 1, duration: 1900, useNativeDriver: true }),
      Animated.timing(progress, { toValue: 0, duration: 1900, useNativeDriver: true }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [progress]);
  const travel = progress.interpolate({ inputRange: [0, 1], outputRange: [-Math.max(0, trackWidth / 2 - 6), Math.max(0, trackWidth / 2 - 6)] });
  return <View onLayout={(event) => setTrackWidth(event.nativeEvent.layout.width)} style={[styles.dividerTrack, style]}>
    <View style={styles.dividerLine} />
    <View style={[styles.dividerPoint, { left: '15%' }]} />
    <View style={[styles.dividerPoint, { left: '35%' }]} />
    <View style={[styles.dividerPoint, { left: '65%' }]} />
    <View style={[styles.dividerPoint, { left: '85%' }]} />
    <Animated.Text style={[styles.dividerDollar, { transform: [{ translateX: travel }] }]}>$</Animated.Text>
  </View>;
}

type MotionPressableProps = Omit<PressableProps, 'style'> & { style?: StyleProp<ViewStyle> };

export function MotionPressable({ style, ...props }: MotionPressableProps) {
  return <Pressable {...props} style={({ pressed }) => [style, pressed && styles.pressed]} />;
}

const styles = StyleSheet.create({
  pressed: { opacity: 0.88, transform: [{ scale: 0.98 }] },
  dividerTrack: { width: '100%', height: 18, justifyContent: 'center', marginBottom: 20, overflow: 'hidden' },
  dividerLine: { width: '100%', height: 2, borderRadius: 2, backgroundColor: '#D6EBDD' },
  dividerPoint: { position: 'absolute', top: 7, width: 4, height: 4, marginLeft: -2, borderRadius: 2, backgroundColor: '#7BBE91' },
  dividerDollar: { position: 'absolute', left: '50%', top: 0, width: 14, marginLeft: -7, color: '#078343', fontSize: 16, lineHeight: 18, fontWeight: '900', textAlign: 'center', textShadowColor: '#07834355', textShadowRadius: 4 },
});
