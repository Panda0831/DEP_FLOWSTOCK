import { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';

export function BrandLockup({ variant = 'compact', tagline = false }: { variant?: 'compact' | 'hero'; tagline?: boolean }) {
  const motion = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(motion, { toValue: 1, duration: 1150, useNativeDriver: true }),
      Animated.timing(motion, { toValue: 0, duration: 1150, useNativeDriver: true }),
    ]));
    animation.start();
    return () => animation.stop();
  }, [motion]);

  const scale = motion.interpolate({ inputRange: [0, 1], outputRange: [1, 1.055] });
  const waveShift = motion.interpolate({ inputRange: [0, 1], outputRange: [-3, 4] });
  const hero = variant === 'hero';

  return (
    <View style={hero ? styles.hero : styles.compact} accessibilityLabel="StockFlow">
      <View style={hero ? styles.heroHalo : styles.compactHalo}>
        <Animated.View style={[hero ? styles.heroMark : styles.compactMark, { transform: [{ scale }] }]}>
          <Text style={hero ? styles.heroLetter : styles.compactLetter}>S</Text>
          <Animated.View style={[hero ? styles.heroWave : styles.compactWave, { transform: [{ translateX: waveShift }, { rotate: '-19deg' }] }]} />
        </Animated.View>
      </View>
      <View style={hero ? styles.heroCopy : styles.compactCopy}>
        <Text style={hero ? styles.heroName : styles.compactName}>StockFlow</Text>
        {tagline && <Text style={hero ? styles.heroTagline : styles.compactTagline}>Gérez votre activité en toute simplicité</Text>}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  compact: { flexDirection: 'row', alignItems: 'center', gap: 11 },
  compactHalo: { width: 52, height: 52, borderRadius: 26, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' },
  compactMark: { width: 42, height: 42, borderRadius: 22, backgroundColor: '#078343', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  compactLetter: { color: '#FFFFFF', fontSize: 33, lineHeight: 40, fontWeight: '800', marginTop: -2 },
  compactWave: { position: 'absolute', width: 49, height: 12, borderTopWidth: 3, borderColor: '#A8E8BF', borderRadius: 20, top: 20, left: -3 },
  compactCopy: { gap: 2 },
  compactName: { color: '#173D2B', fontSize: 25, fontWeight: '800', letterSpacing: -0.7 },
  compactTagline: { color: '#65736A', fontSize: 11 },
  hero: { alignItems: 'center', gap: 12 },
  heroHalo: { width: 76, height: 76, borderRadius: 38, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' },
  heroMark: { width: 66, height: 66, borderRadius: 33, backgroundColor: '#078343', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  heroLetter: { color: '#FFFFFF', fontSize: 49, lineHeight: 58, fontWeight: '800', marginTop: -3 },
  heroWave: { position: 'absolute', width: 76, height: 17, borderTopWidth: 5, borderColor: '#A8E8BF', borderRadius: 20, top: 31, left: -5 },
  heroCopy: { alignItems: 'center', gap: 4 },
  heroName: { color: '#173D2B', fontSize: 36, fontWeight: '800', letterSpacing: -1.2 },
  heroTagline: { color: '#65736A', fontSize: 15, textAlign: 'center' },
});
