import { useEffect, useMemo, useRef } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Line, Path } from 'react-native-svg';

import { Radius, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export type ProfitTrendPoint = { month: string; value: number };

const CHART_WIDTH = 360;
const CHART_HEIGHT = 128;
const LEFT = 8;
const RIGHT = 352;
const TOP = 12;
const BOTTOM = 112;
function createSmoothPath(points: { x: number; y: number }[]) {
  if (points.length < 2) return '';
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[Math.max(0, index - 1)];
    const start = points[index];
    const end = points[index + 1];
    const next = points[Math.min(points.length - 1, index + 2)];
    const control1 = {
      x: start.x + (end.x - previous.x) / 6,
      y: start.y + (end.y - previous.y) / 6,
    };
    const control2 = {
      x: end.x - (next.x - start.x) / 6,
      y: end.y - (next.y - start.y) / 6,
    };
    path += ` C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${end.x} ${end.y}`;
  }
  return path;
}

function monthLabel(value: string) {
  const [year, month] = value.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('fr-FR', { month: 'short' }).replace('.', '');
}

export function ProfitTrendChart({ points }: { points: ProfitTrendPoint[] }) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const entrance = useRef(new Animated.Value(0)).current;

  const geometry = useMemo(() => {
    const values = points.map((point) => point.value);
    const minimum = Math.min(0, ...values);
    const maximum = Math.max(0, ...values);
    const range = maximum - minimum || 1;
    const chartPoints = points.map((point, index) => ({
      x: LEFT + (RIGHT - LEFT) * index / Math.max(points.length - 1, 1),
      y: BOTTOM - ((point.value - minimum) / range) * (BOTTOM - TOP),
    }));
    const path = createSmoothPath(chartPoints);
    return {
      chartPoints,
      path,
      zeroY: BOTTOM - ((0 - minimum) / range) * (BOTTOM - TOP),
    };
  }, [points]);

  useEffect(() => {
    let active = true;
    let animation: Animated.CompositeAnimation | undefined;
    const show = (reduced: boolean) => {
      if (!active) return;
      animation?.stop();
      if (reduced) {
        entrance.setValue(1);
        return;
      }
      entrance.setValue(0);
      animation = Animated.timing(entrance, {
        toValue: 1,
        duration: 420,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      });
      animation.start();
    };
    void AccessibilityInfo.isReduceMotionEnabled().then(show);
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (reduced) => {
      if (reduced) show(true);
    });
    return () => {
      active = false;
      animation?.stop();
      subscription.remove();
    };
  }, [entrance]);

  const currentValue = points.at(-1)?.value ?? 0;
  const accessibleSummary = points
    .map((point) => `${monthLabel(point.month)} : ${point.value.toLocaleString('fr-FR')} ariary`)
    .join(', ');

  return (
    <View style={styles.panel}>
      <View style={styles.header}>
        <View style={styles.heading}>
          <Text style={styles.title}>Bénéfice net</Text>
          <Text style={styles.subtitle}>Sur les six derniers mois</Text>
        </View>
        <Text style={styles.value} numberOfLines={1} adjustsFontSizeToFit>
          {currentValue.toLocaleString('fr-FR')} Ar
        </Text>
      </View>
      {points.length > 1 ? (
        <View accessible accessibilityRole="image" accessibilityLabel={`Évolution du bénéfice net : ${accessibleSummary}`}>
          <Animated.View style={{ opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [5, 0] }) }] }}>
            <Svg width="100%" height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} preserveAspectRatio="none">
              {[TOP, (TOP + BOTTOM) / 2, BOTTOM].map((y) => (
                <Line key={y} x1={LEFT} y1={y} x2={RIGHT} y2={y} stroke={t.separator} strokeWidth={1} />
              ))}
              <Line
                x1={LEFT}
                y1={geometry.zeroY}
                x2={RIGHT}
                y2={geometry.zeroY}
                stroke={t.secondaryText}
                strokeWidth={1}
                strokeDasharray="3 5"
                opacity={0.45}
              />
              <Path
                d={geometry.path}
                fill="none"
                stroke={t.tint}
                strokeWidth={3}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {geometry.chartPoints.length > 0 && (
                <>
                  <Circle cx={geometry.chartPoints.at(-1)?.x} cy={geometry.chartPoints.at(-1)?.y} r={7} fill={t.surface} />
                  <Circle cx={geometry.chartPoints.at(-1)?.x} cy={geometry.chartPoints.at(-1)?.y} r={4} fill={t.tint} />
                </>
              )}
            </Svg>
            <View style={styles.months}>
              {points.map((point) => <Text key={point.month} style={styles.month}>{monthLabel(point.month)}</Text>)}
            </View>
          </Animated.View>
        </View>
      ) : (
        <Text style={styles.empty}>Aucune donnée disponible pour cette période.</Text>
      )}
    </View>
  );
}

const makeStyles = (t: ReturnType<typeof useAppTheme>) => StyleSheet.create({
  panel: {
    backgroundColor: t.surface,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: t.separator,
    padding: 16,
    marginBottom: 24,
  },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 8 },
  heading: { flex: 1 },
  title: { ...Type.headline, color: t.text },
  subtitle: { ...Type.caption, color: t.secondaryText, marginTop: 2 },
  value: { color: t.tint, fontSize: 18, fontWeight: '700', maxWidth: '48%', textAlign: 'right' },
  months: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 2 },
  month: { ...Type.caption, color: t.secondaryText, flex: 1, textAlign: 'center', textTransform: 'capitalize' },
  empty: { ...Type.footnote, color: t.secondaryText, textAlign: 'center', paddingVertical: 28 },
});
