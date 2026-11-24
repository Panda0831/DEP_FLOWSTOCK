import { useEffect, useMemo, useRef } from 'react';
import { AccessibilityInfo, Animated, Easing, StyleSheet, Text, View } from 'react-native';
import Svg, { Line, Path } from 'react-native-svg';

import { Radius, Type } from '@/constants/theme';
import { useAppTheme } from '@/hooks/use-app-theme';

export type ProfitTrendPoint = { month: string; value: number };

const CHART_WIDTH = 280;
const CHART_HEIGHT = 132;
const LEFT = 8;
const RIGHT = 272;
const TOP = 16;
const BOTTOM = 100;
const MID = (TOP + BOTTOM) / 2;

function createSmoothPath(points: { x: number; y: number }[]) {
  if (points.length < 2) return '';
  let path = `M ${points[0].x} ${points[0].y}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const previous = points[Math.max(0, index - 1)];
    const start = points[index];
    const end = points[index + 1];
    const next = points[Math.min(points.length - 1, index + 2)];
    const minY = Math.min(start.y, end.y);
    const maxY = Math.max(start.y, end.y);
    const control1 = {
      x: start.x + (end.x - previous.x) / 6,
      y: Math.min(maxY, Math.max(minY, start.y + (end.y - previous.y) / 6)),
    };
    const control2 = {
      x: end.x - (next.x - start.x) / 6,
      y: Math.min(maxY, Math.max(minY, end.y - (next.y - start.y) / 6)),
    };
    path += ` C ${control1.x} ${control1.y}, ${control2.x} ${control2.y}, ${end.x} ${end.y}`;
  }
  return path;
}

function monthLabel(value: string) {
  const [year, month] = value.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('fr-FR', { month: 'short' }).replace('.', '');
}

function fullMonthLabel(value: string) {
  const [year, month] = value.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('fr-FR', { month: 'long' });
}

function formatAxisValue(value: number) {
  const compact = new Intl.NumberFormat('fr-FR', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
  return `${compact} Ar`;
}

function formatMonthValue(value: number) {
  return new Intl.NumberFormat('fr-FR', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
}

export function ProfitTrendChart({ points }: { points: ProfitTrendPoint[] }) {
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const entrance = useRef(new Animated.Value(0)).current;

  const geometry = useMemo(() => {
    const values = points.map((point) => point.value);
    let minimum = Math.min(0, ...values);
    let maximum = Math.max(0, ...values);
    if (minimum === maximum) {
      minimum = -1;
      maximum = 1;
    }
    const rawRange = maximum - minimum || Math.max(Math.abs(maximum), 1);
    const padding = rawRange * 0.1;
    minimum -= padding;
    maximum += padding;
    const range = maximum - minimum;
    const chartPoints = points.map((point, index) => ({
      x: LEFT + (RIGHT - LEFT) * index / Math.max(points.length - 1, 1),
      y: BOTTOM - ((point.value - minimum) / range) * (BOTTOM - TOP),
    }));
    const path = createSmoothPath(chartPoints);
    return {
      chartPoints,
      path,
      axisValues: [maximum, (maximum + minimum) / 2, minimum],
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
  const currentPoint = points.at(-1);
  const previousPoint = points.at(-2);
  const change = currentPoint && previousPoint ? currentPoint.value - previousPoint.value : 0;
  const previousMonth = previousPoint ? monthLabel(previousPoint.month) : '';
  const changeLabel = change > 0
    ? `En hausse de ${Math.abs(change).toLocaleString('fr-FR')} Ar depuis ${previousMonth}.`
    : change < 0
      ? `En baisse de ${Math.abs(change).toLocaleString('fr-FR')} Ar depuis ${previousMonth}.`
      : 'Stable par rapport au mois précédent.';
  const resultLabel = currentValue < 0
    ? `En ${currentPoint ? fullMonthLabel(currentPoint.month) : ''}, le résultat est négatif.`
    : currentValue > 0
      ? `En ${currentPoint ? fullMonthLabel(currentPoint.month) : ''}, le résultat est positif.`
      : `En ${currentPoint ? fullMonthLabel(currentPoint.month) : ''}, le résultat est à l’équilibre.`;
  const accessibleSummary = points
    .map((point) => `${monthLabel(point.month)} : ${point.value.toLocaleString('fr-FR')} ariary`)
    .join(', ');

  return (
    <View style={styles.panel}>
      <View style={styles.header}>
        <View style={styles.heading}>
          <Text style={styles.title}>Bénéfice net par mois</Text>
          <Text style={styles.subtitle}>Après dépenses, en ariary (Ar)</Text>
        </View>
        <View style={styles.current}>
          <Text style={styles.currentMonth}>{currentPoint ? fullMonthLabel(currentPoint.month) : ''}</Text>
          <Text style={styles.value} numberOfLines={1} adjustsFontSizeToFit>{currentValue.toLocaleString('fr-FR')} Ar</Text>
        </View>
      </View>
      {points.length > 1 ? (
        <View accessible accessibilityRole="image" accessibilityLabel={`Évolution du bénéfice net : ${accessibleSummary}`}>
          <Animated.View style={{ opacity: entrance, transform: [{ translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [5, 0] }) }] }}>
            <View style={styles.chartRow}>
              <View style={styles.axisLabels}>
                {geometry.axisValues.map((value, index) => (
                  <Text key={index} style={styles.axisLabel}>{formatAxisValue(value)}</Text>
                ))}
              </View>
              <View style={styles.plot}>
                <Svg width="100%" height={CHART_HEIGHT} viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`} preserveAspectRatio="none">
                  {[TOP, MID, BOTTOM].map((y) => (
                    <Line key={y} x1={LEFT} y1={y} x2={RIGHT} y2={y} stroke={t.separator} strokeWidth={1} />
                  ))}
                  {geometry.zeroY > TOP + 1 && geometry.zeroY < BOTTOM - 1 && (
                    <Line
                      x1={LEFT}
                      y1={geometry.zeroY}
                      x2={RIGHT}
                      y2={geometry.zeroY}
                      stroke={t.secondaryText}
                      strokeWidth={1}
                      strokeDasharray="3 5"
                      opacity={0.6}
                    />
                  )}
                  <Path
                    d={geometry.path}
                    fill="none"
                    stroke={t.tint}
                    strokeWidth={1.6}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </Svg>
                <View style={styles.months}>
                  {points.map((point) => <Text key={point.month} style={styles.month}>{monthLabel(point.month)}</Text>)}
                </View>
                <View style={styles.monthValues}>
                  {points.map((point) => (
                    <Text key={point.month} style={styles.monthValue} numberOfLines={1}>
                      {formatMonthValue(point.value)}
                    </Text>
                  ))}
                </View>
              </View>
            </View>
            <Text style={styles.unitHint}>Montants en Ar</Text>
            <Text style={styles.interpretation}>{resultLabel} {changeLabel}</Text>
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
  current: { alignItems: 'flex-end', maxWidth: '48%' },
  currentMonth: { ...Type.caption, color: t.secondaryText, textTransform: 'capitalize' },
  value: { color: t.tint, fontSize: 17, lineHeight: 22, fontWeight: '700', textAlign: 'right' },
  chartRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  axisLabels: { width: 52, height: CHART_HEIGHT, justifyContent: 'space-between', paddingTop: TOP - 7, paddingBottom: CHART_HEIGHT - BOTTOM - 7 },
  axisLabel: { color: t.secondaryText, fontSize: 10, lineHeight: 14, textAlign: 'right' },
  plot: { flex: 1, minWidth: 0 },
  months: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 2 },
  month: { ...Type.caption, color: t.secondaryText, flex: 1, textAlign: 'center', textTransform: 'capitalize' },
  monthValues: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 3 },
  monthValue: { color: t.text, fontSize: 10, lineHeight: 14, fontWeight: '600', flex: 1, textAlign: 'center' },
  unitHint: { color: t.secondaryText, fontSize: 10, lineHeight: 14, marginTop: 8 },
  interpretation: { ...Type.footnote, color: t.text, marginTop: 4 },
  empty: { ...Type.footnote, color: t.secondaryText, textAlign: 'center', paddingVertical: 28 },
});
