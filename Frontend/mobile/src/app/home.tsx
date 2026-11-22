import { useCallback, useEffect, useMemo, useRef, useState, type PropsWithChildren } from 'react';
import { ActivityIndicator, Animated, Pressable, ScrollView, StyleSheet, Text, View, useWindowDimensions, type StyleProp, type ViewStyle } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import Svg, { Circle, Defs, LinearGradient, Line, Path, Stop, Text as SvgText } from 'react-native-svg';
import { useAuth } from '@/lib/auth-context';
import { api, type Categorie, type Page, type Produit, type Stock } from '@/lib/session-api';
import { BrandLockup } from '@/components/brand-lockup';

type Dashboard = { resume_financier: { chiffre_affaires: string; benefice_net: string; commandes_livrees: number }; alertes_stock: Stock[]; commandes_en_attente: number };
type Order = { public_id: string; date: string; statut: string; client: string };
type Monthly = { mois: string; benefice_net: string; depenses: string };
type ChartPoint = { month: string; net: number; expenses: number; orders: number };
type Segment = { label: string; value: number; color: string };

const PALETTE = ['#078343', '#D39A29', '#778078', '#B63838', '#D8F1E1'];

async function fetchAllPages<T>(endpoint: string): Promise<T[]> {
  const first = await api.get<Page<T> | T[]>(endpoint);
  if (Array.isArray(first)) return first;
  const results = [...first.results];
  let page = 2;
  let next = first.next;
  while (next && page < 100) {
    const response = await api.get<Page<T> | T[]>(endpoint, { page });
    if (Array.isArray(response)) return [...results, ...response];
    results.push(...response.results);
    next = response.next;
    page += 1;
  }
  return results;
}

function toLocalDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function monthKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function makePath(values: number[], min: number, max: number, width: number, height: number, padding: number) {
  const usableWidth = width - padding * 2;
  const usableHeight = height - padding * 2;
  const range = max - min || 1;
  const points = values.map((value, index) => ({
    x: padding + index * (usableWidth / Math.max(1, values.length - 1)),
    y: padding + ((max - value) / range) * usableHeight,
  }));
  if (!points.length) return { path: '', points };
  const path = points.reduce((result, point, index) => {
    if (index === 0) return `M ${point.x} ${point.y}`;
    const previous = points[index - 1];
    const midX = (previous.x + point.x) / 2;
    return `${result} C ${midX} ${previous.y}, ${midX} ${point.y}, ${point.x} ${point.y}`;
  }, '');
  return { path, points };
}

function Reveal({ children, delay = 0, style }: PropsWithChildren<{ delay?: number; style?: StyleProp<ViewStyle> }>) {
  const progress = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const animation = Animated.timing(progress, { toValue: 1, duration: 520, delay, useNativeDriver: true });
    animation.start();
    return () => animation.stop();
  }, [delay, progress]);
  return <Animated.View style={[{ opacity: progress, transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [13, 0] }) }] }, style]}>{children}</Animated.View>;
}

function StatCard({ label, value, hint, mark, delay }: { label: string; value: string; hint: string; mark: string; delay: number }) {
  const [pressed, setPressed] = useState(false);
  return <Reveal delay={delay} style={styles.statWrap}>
    <Pressable onPressIn={() => setPressed(true)} onPressOut={() => setPressed(false)} style={[styles.stat, pressed && styles.statPressed]}>
      <View style={styles.statTop}><Text style={styles.statLabel}>{label}</Text><View style={styles.statMark}><Text style={styles.statMarkText}>{mark}</Text></View></View>
      <Text style={styles.statValue} numberOfLines={1}>{value}</Text>
      <Text style={styles.statHint}>{hint}</Text>
    </Pressable>
  </Reveal>;
}

function DonutCard({ title, caption, segments, delay }: { title: string; caption: string; segments: Segment[]; delay: number }) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  return <Reveal delay={delay} style={styles.donutWrap}>
    <View style={styles.donutCard}>
      <View style={styles.donutHeading}><View><Text style={styles.chartTitle}>{title}</Text><Text style={styles.chartCaption}>{caption}</Text></View><Text style={styles.chartDots}>•••</Text></View>
      <View style={styles.donutBody}>
        <View style={styles.donutGraphic}>
          <Svg width={128} height={128} viewBox="0 0 128 128">
            <Circle cx="64" cy="64" r={radius} fill="none" stroke="#E9EEE9" strokeWidth="16" />
            {total > 0 && segments.filter((segment) => segment.value > 0).map((segment) => {
              const fraction = segment.value / total;
              const arcLength = fraction * circumference;
              const currentOffset = offset;
              offset += fraction * circumference;
              return <Circle key={segment.label} cx="64" cy="64" r={radius} fill="none" stroke={segment.color} strokeWidth="16" strokeDasharray={`${arcLength} ${circumference - arcLength}`} strokeDashoffset={-currentOffset} transform="rotate(-90 64 64)" />;
            })}
            <SvgText x="64" y="62" textAnchor="middle" fill="#173D2B" fontSize="23" fontWeight="700">{total}</SvgText>
            <SvgText x="64" y="80" textAnchor="middle" fill="#89938C" fontSize="8" fontWeight="700">TOTAL</SvgText>
          </Svg>
        </View>
        <View style={styles.legend}>
          {segments.slice(0, 4).map((segment) => <View key={segment.label} style={styles.legendRow}>
            <View style={[styles.legendDot, { backgroundColor: segment.color }]} />
            <Text style={styles.legendLabel} numberOfLines={1}>{segment.label}</Text>
            <Text style={styles.legendValue}>{segment.value}</Text>
          </View>)}
          {segments.length > 4 && <View style={styles.legendRow}><View style={[styles.legendDot, { backgroundColor: PALETTE[4] }]} /><Text style={styles.legendLabel}>Autres</Text><Text style={styles.legendValue}>{segments.slice(4).reduce((sum, segment) => sum + segment.value, 0)}</Text></View>}
          {segments.length === 0 && <Text style={styles.emptyLegend}>Aucune donnée</Text>}
        </View>
      </View>
    </View>
  </Reveal>;
}

function ProgressChart({ points, isAdmin, period, onPeriodChange }: { points: ChartPoint[]; isAdmin: boolean; period: 6 | 12; onPeriodChange: (period: 6 | 12) => void }) {
  const values = points.flatMap((point) => isAdmin ? [point.net, point.expenses] : [point.orders]);
  const min = Math.min(0, ...values);
  const max = Math.max(1, ...values);
  const width = 680;
  const height = 236;
  const padding = 22;
  const firstSeries = points.map((point) => isAdmin ? point.net : point.orders);
  const { path, points: coordinates } = makePath(firstSeries, min, max, width, height, padding);
  const spending = isAdmin ? makePath(points.map((point) => point.expenses), min, max, width, height, padding) : null;
  const baselineY = height - padding;
  const areaPath = path && coordinates.length ? `${path} L ${coordinates[coordinates.length - 1].x} ${baselineY} L ${coordinates[0].x} ${baselineY} Z` : '';
  const visibleLabels = points.map((point, index) => index === 0 || index === Math.floor((points.length - 1) / 2) || index === points.length - 1 ? point.month : '');

  return <Reveal delay={360}>
    <View style={styles.progressCard}>
      <View style={styles.chartHeader}>
        <View><Text style={styles.chartTitle}>Progression de l’activité</Text><Text style={styles.chartCaption}>{isAdmin ? 'Bénéfice net et dépenses par mois' : 'Commandes créées par mois'}</Text></View>
        <View style={styles.periodSwitch}>
          {[6, 12].map((value) => <Pressable key={value} onPress={() => onPeriodChange(value as 6 | 12)} style={[styles.periodButton, period === value && styles.periodButtonActive]}><Text style={[styles.periodText, period === value && styles.periodTextActive]}>{value}M</Text></Pressable>)}
        </View>
      </View>
      <View style={styles.chartSummary}><Text style={styles.currentValue}>{isAdmin ? `${Math.round(firstSeries[firstSeries.length - 1] || 0).toLocaleString('fr-FR')} Ar` : `${firstSeries.reduce((sum, value) => sum + value, 0)} commandes`}</Text><Text style={styles.currentLabel}>{isAdmin ? 'Bénéfice net du mois courant' : 'Commandes sur la période'}</Text></View>
      <Svg width="100%" height={236} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <Defs><LinearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1"><Stop offset="0" stopColor="#078343" stopOpacity="0.18"/><Stop offset="1" stopColor="#078343" stopOpacity="0.01"/></LinearGradient></Defs>
        {[0, 1, 2, 3].map((row) => <Line key={row} x1={padding} x2={width - padding} y1={padding + row * ((height - padding * 2) / 3)} y2={padding + row * ((height - padding * 2) / 3)} stroke="#E7ECE7" strokeWidth="1" strokeDasharray="3 5" />)}
        {areaPath ? <Path d={areaPath} fill="url(#areaFill)" /> : null}
        {spending?.path ? <Path d={spending.path} fill="none" stroke="#D39A29" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="6 5" opacity="0.8" /> : null}
        {path ? <Path d={path} fill="none" stroke="#078343" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" /> : null}
        {coordinates.map((point, index) => index === coordinates.length - 1 ? <Circle key={index} cx={point.x} cy={point.y} r="5" fill="#FFFFFF" stroke="#078343" strokeWidth="3" /> : null)}
        {visibleLabels.map((label, index) => label ? <SvgText key={`${label}-${index}`} x={padding + index * ((width - padding * 2) / Math.max(1, points.length - 1))} y={height - 3} textAnchor={index === 0 ? 'start' : index === points.length - 1 ? 'end' : 'middle'} fill="#89938C" fontSize="10">{label}</SvgText> : null)}
      </Svg>
      <View style={styles.chartLegend}>
        <View style={styles.chartLegendItem}><View style={styles.greenLine}/><Text style={styles.chartLegendText}>{isAdmin ? 'Bénéfice net' : 'Commandes'}</Text></View>
      {isAdmin && <View style={styles.chartLegendItem}><View style={styles.amberLine}/><Text style={styles.chartLegendText}>Dépenses</Text></View>}
      </View>
    </View>
  </Reveal>;
}

export default function HomeScreen() {
  const router = useRouter();
  const { user, isReady } = useAuth();
  const { width } = useWindowDimensions();
  const [summary, setSummary] = useState<Dashboard | null>(null);
  const [pending, setPending] = useState<Order[]>([]);
  const [stock, setStock] = useState<Stock[]>([]);
  const [products, setProducts] = useState<Produit[]>([]);
  const [categories, setCategories] = useState<Categorie[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [monthly, setMonthly] = useState<Monthly[]>([]);
  const [period, setPeriod] = useState<6 | 12>(6);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const isAdmin = user?.role === 'ADMIN' || user?.is_staff;

  useEffect(() => {
    if (isReady && !user) router.replace('/');
  }, [isReady, router, user]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError('');
    try {
      const tasks = [
        api.get<Order[] | Page<Order>>('/dashboard/pending-orders/'),
        api.get<Stock[]>('/stock/alerts/'),
        fetchAllPages<Produit>('/products/'),
        fetchAllPages<Categorie>('/categories/'),
        fetchAllPages<Order>('/orders/'),
      ] as const;
      const [pendingResult, stockResult, productResult, categoryResult, orderResult] = await Promise.all(tasks);
      setPending(Array.isArray(pendingResult) ? pendingResult : pendingResult.results);
      setStock(stockResult);
      setProducts(productResult);
      setCategories(categoryResult);
      setOrders(orderResult);
      if (isAdmin) {
        const today = new Date();
        const start = new Date(today.getFullYear(), today.getMonth() - 11, 1);
        const [dashboard, trend] = await Promise.all([
          api.get<Dashboard>('/dashboard/summary/'),
          api.get<Monthly[]>('/reports/monthly/', { start_date: toLocalDate(start), end_date: toLocalDate(today) }),
        ]);
        setSummary(dashboard);
        setMonthly(trend);
      } else {
        setSummary(null);
        setMonthly([]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Le tableau de bord est indisponible.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isAdmin]);

  useEffect(() => { if (isReady && user) void refresh(); }, [isReady, refresh, user]);

  const chartPoints = useMemo(() => {
    const today = new Date();
    const byMonth = new Map(monthly.map((item) => [item.mois.slice(0, 7), item]));
    const orderCounts = new Map<string, number>();
    for (const order of orders) {
      const key = order.date.slice(0, 7);
      orderCounts.set(key, (orderCounts.get(key) || 0) + 1);
    }
    return Array.from({ length: 12 }, (_, index) => {
      const date = new Date(today.getFullYear(), today.getMonth() - 11 + index, 1);
      const key = monthKey(date);
      const values = byMonth.get(key);
      return {
        month: date.toLocaleDateString('fr-FR', { month: 'short' }).replace('.', ''),
        net: Number(values?.benefice_net || 0),
        expenses: Number(values?.depenses || 0),
        orders: orderCounts.get(key) || 0,
      };
    });
  }, [monthly, orders]);

  const categorySegments = useMemo(() => {
    const counts = new Map(categories.map((category) => [category.public_id, { label: category.nomCategorie, value: 0 }]));
    let unassigned = 0;
    for (const product of products) {
      if (product.idCategorie && counts.has(product.idCategorie)) counts.get(product.idCategorie)!.value += 1;
      else unassigned += 1;
    }
    const ranked = [...counts.values()].filter((item) => item.value > 0).sort((a, b) => b.value - a.value);
    if (unassigned) ranked.push({ label: 'Sans catégorie', value: unassigned });
    const top = ranked.slice(0, 4).map((item, index) => ({ ...item, color: PALETTE[index % PALETTE.length] }));
    const otherCount = ranked.slice(4).reduce((sum, item) => sum + item.value, 0);
    if (otherCount) top.push({ label: 'Autres', value: otherCount, color: PALETTE[4] });
    return top;
  }, [categories, products]);

  const orderSegments = useMemo(() => {
    const statuses = [
      { key: 'confirmee', label: 'Confirmées', color: PALETTE[0] },
      { key: 'en_attente', label: 'En attente', color: '#D39A29' },
      { key: 'annulee', label: 'Annulées', color: '#B63838' },
    ];
    return statuses.map((status) => ({ label: status.label, color: status.color, value: orders.filter((order) => order.statut === status.key).length }));
  }, [orders]);

  if (!isReady || !user) return <SafeAreaView style={styles.safe}><ActivityIndicator color="#078343" size="large" style={{ flex: 1 }} /></SafeAreaView>;
  const visiblePoints = chartPoints.slice(-period);
  const isCompact = width < 700;
  const todayLabel = new Date().toLocaleDateString('fr-FR', isCompact ? { day: 'numeric', month: 'short' } : { weekday: 'long', day: 'numeric', month: 'long' });
  const currentMonthOrders = chartPoints[chartPoints.length - 1]?.orders || 0;

  return <SafeAreaView style={styles.safe} edges={['top']}>
    <StatusBar style="dark" />
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <Reveal>
        <View style={styles.header}><BrandLockup /></View>
      </Reveal>
      <Reveal delay={80}>
        <View style={styles.hello}>
          <View style={styles.helloTop}><View style={styles.live}><View style={styles.liveDot} /><Text style={styles.liveText}>VUE D’ENSEMBLE</Text></View><Text style={styles.dateLabel}>{todayLabel}</Text></View>
          <View style={[styles.heroBody, isCompact && styles.heroBodyCompact]}>
            <View style={styles.heroCopy}><Text style={styles.helloTitle}>Votre activité évolue</Text><Text style={styles.helloSub}>Suivez les tendances et les indicateurs clés de FlowStock.</Text></View>
            <View style={[styles.heroMetric, isCompact && styles.heroMetricCompact]}>
              <Text style={styles.heroMetricLabel}>{isAdmin ? 'CHIFFRE D’AFFAIRES · CE MOIS' : 'COMMANDES · CE MOIS'}</Text>
              <Text style={styles.heroMetricValue}>{isAdmin ? summary ? `${Number(summary.resume_financier.chiffre_affaires).toLocaleString('fr-FR')} Ar` : '—' : String(currentMonthOrders)}</Text>
              <Text style={styles.heroMetricFoot}>{isAdmin ? summary ? `${summary.resume_financier.commandes_livrees} commandes livrées` : 'Résumé indisponible' : 'commandes enregistrées'}</Text>
            </View>
          </View>
        </View>
      </Reveal>

      {!!error && <Text style={styles.error}>{error}</Text>}
      {loading ? <ActivityIndicator color="#078343" size="large" style={{ margin: 40 }} /> : <>
        <View style={styles.stats}>
          <StatCard label={isAdmin ? 'Commandes livrées' : 'Commandes'} value={isAdmin ? summary ? String(summary.resume_financier.commandes_livrees) : '—' : String(orders.length)} hint={isAdmin ? 'Période en cours' : 'Dans votre activité'} mark="CO" delay={140} />
          <StatCard label={isAdmin ? 'Bénéfice net' : 'Produits actifs'} value={isAdmin ? summary ? `${Number(summary.resume_financier.benefice_net).toLocaleString('fr-FR')} Ar` : '—' : String(products.filter((product) => product.isActif).length)} hint={isAdmin ? 'Après dépenses' : 'Dans le catalogue'} mark={isAdmin ? 'BN' : 'PR'} delay={210} />
          <StatCard label="En attente" value={String(pending.length)} hint="Commandes à traiter" mark="AT" delay={280} />
          <StatCard label="Alertes de stock" value={String(stock.length)} hint="Produits sous le seuil" mark="ST" delay={350} />
        </View>

        {stock.length > 0 && <Reveal delay={360}><View style={styles.alert}><View style={styles.alertHeader}><Text style={styles.alertTitle}>Stock à surveiller</Text><Text style={styles.alertCount}>{stock.length} alerte{stock.length > 1 ? 's' : ''}</Text></View><Text style={styles.alertText}>{stock.slice(0, 4).map((product) => `${product.nomProduit} (${product.stock}/${product.seuilAlerte})`).join('   ·   ')}</Text></View></Reveal>}

        <ProgressChart points={visiblePoints} isAdmin={!!isAdmin} period={period} onPeriodChange={setPeriod} />

        <View style={styles.sectionHeading}><Text style={styles.section}>Répartition</Text><Text style={styles.sectionHint}>Vue d’ensemble de vos données</Text></View>
        <View style={styles.donutGrid}>
          <DonutCard title="Produits enregistrés" caption="Par catégorie" segments={categorySegments} delay={430} />
          <DonutCard title="Commandes" caption="Par statut" segments={orderSegments} delay={500} />
        </View>
      </>}

      <Pressable onPress={() => void refresh()} disabled={refreshing} style={({ pressed }) => [styles.refresh, pressed && styles.pressed, refreshing && { opacity: 0.7 }]}>
        {refreshing ? <ActivityIndicator size="small" color="#078343" /> : <Text style={styles.refreshIcon}>↻</Text>}
        <Text style={styles.refreshText}>{refreshing ? 'Actualisation…' : 'Actualiser les données'}</Text>
      </Pressable>
    </ScrollView>
  </SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F5F8F5' },
  content: { width: '100%', maxWidth: 1080, alignSelf: 'center', paddingHorizontal: 24, paddingTop: 26, paddingBottom: 28 },
  header: { flexDirection: 'row', justifyContent: 'flex-start', alignItems: 'center', minHeight: 58 },
  hello: { backgroundColor: '#078343', borderRadius: 20, paddingHorizontal: 23, paddingVertical: 19, marginTop: 22, marginBottom: 18, minHeight: 156, overflow: 'hidden' },
  helloTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 10 },
  live: { flexDirection: 'row', alignItems: 'center', gap: 7, backgroundColor: '#FFFFFF22', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20 },
  liveDot: { width: 6, height: 6, borderRadius: 4, backgroundColor: '#D8F1E1' },
  liveText: { color: '#D8F1E1', fontSize: 9, fontWeight: '800', letterSpacing: 1 },
  dateLabel: { color: '#D8F1E1', fontSize: 11, fontWeight: '600', textTransform: 'capitalize' },
  heroBody: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 22 },
  heroBodyCompact: { flexDirection: 'column', alignItems: 'stretch', gap: 14 },
  heroCopy: { flex: 1 },
  helloTitle: { color: '#FFFFFF', fontWeight: '800', fontSize: 22 },
  helloSub: { color: '#D8F1E1', fontSize: 13, marginTop: 6, maxWidth: 430, lineHeight: 19 },
  heroMetric: { minWidth: 230, paddingLeft: 22, borderLeftWidth: 1, borderLeftColor: '#D8F1E1' },
  heroMetricCompact: { minWidth: 0, paddingLeft: 0, paddingTop: 13, borderLeftWidth: 0, borderTopWidth: 1, borderTopColor: '#D8F1E1' },
  heroMetricLabel: { color: '#D8F1E1', fontSize: 9, fontWeight: '800', letterSpacing: 0.8 },
  heroMetricValue: { color: '#FFFFFF', fontWeight: '800', fontSize: 22, marginTop: 6 },
  heroMetricFoot: { color: '#D8F1E1', fontSize: 10, marginTop: 3 },
  stats: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  statWrap: { flexGrow: 1, flexBasis: 155, minWidth: 145 },
  stat: { backgroundColor: '#FFFFFF', borderRadius: 17, padding: 17, borderWidth: 1, borderColor: '#DDE9DF', minHeight: 122, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 7, elevation: 1 },
  statPressed: { transform: [{ scale: 0.985 }], borderColor: '#078343' },
  statTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  statMark: { width: 30, height: 30, borderRadius: 10, backgroundColor: '#E7F5EC', alignItems: 'center', justifyContent: 'center' },
  statMarkText: { color: '#078343', fontSize: 9, fontWeight: '900' },
  statLabel: { color: '#66716A', fontSize: 12, fontWeight: '600' },
  statValue: { color: '#173D2B', fontWeight: '800', fontSize: 20, marginTop: 10 },
  statHint: { color: '#89938C', fontSize: 11, marginTop: 4 },
  alert: { backgroundColor: '#FFF7E7', borderColor: '#F1DFAF', borderWidth: 1, borderRadius: 15, padding: 16, marginTop: 14 },
  alertHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  alertTitle: { color: '#7A5811', fontWeight: '800', fontSize: 14 },
  alertCount: { color: '#806925', fontSize: 11, fontWeight: '700' },
  alertText: { color: '#806925', fontSize: 12, marginTop: 7 },
  progressCard: { backgroundColor: '#FFFFFF', borderRadius: 19, borderWidth: 1, borderColor: '#DDE9DF', padding: 19, marginTop: 17, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 7, elevation: 1 },
  chartHeader: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  chartTitle: { color: '#173D2B', fontSize: 14, fontWeight: '800' },
  chartCaption: { color: '#89938C', fontSize: 11, marginTop: 4 },
  chartDots: { color: '#89938C', fontSize: 18, letterSpacing: 2 },
  periodSwitch: { flexDirection: 'row', backgroundColor: '#F0F4F1', padding: 3, borderRadius: 10 },
  periodButton: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8 },
  periodButtonActive: { backgroundColor: '#078343' },
  periodText: { color: '#66716A', fontSize: 10, fontWeight: '700' },
  periodTextActive: { color: '#FFFFFF' },
  chartSummary: { marginTop: 17 },
  currentValue: { color: '#173D2B', fontSize: 22, fontWeight: '800' },
  currentLabel: { color: '#89938C', fontSize: 11, marginTop: 3 },
  chartLegend: { flexDirection: 'row', gap: 18, marginTop: 4 },
  chartLegendItem: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  chartLegendText: { color: '#69756D', fontSize: 10, fontWeight: '600' },
  greenLine: { width: 15, height: 3, borderRadius: 3, backgroundColor: '#078343' },
  amberLine: { width: 15, height: 3, borderRadius: 3, backgroundColor: '#D39A29' },
  sectionHeading: { marginTop: 26, marginBottom: 12 },
  section: { color: '#173D2B', fontWeight: '800', fontSize: 19 },
  sectionHint: { color: '#89938C', fontSize: 11, marginTop: 4 },
  donutGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 13 },
  donutWrap: { flexGrow: 1, flexBasis: 370, minWidth: 250 },
  donutCard: { backgroundColor: '#FFFFFF', borderRadius: 19, borderWidth: 1, borderColor: '#DDE9DF', padding: 17, minHeight: 208, shadowColor: '#38704A', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.03, shadowRadius: 7, elevation: 1 },
  donutHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  donutBody: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginTop: 9 },
  donutGraphic: { width: 132, height: 132, alignItems: 'center', justifyContent: 'center' },
  legend: { flex: 1, gap: 12, paddingLeft: 6 },
  legendRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  legendDot: { width: 7, height: 7, borderRadius: 5 },
  legendLabel: { color: '#727D75', fontSize: 10, flex: 1 },
  legendValue: { color: '#173D2B', fontSize: 10, fontWeight: '800' },
  emptyLegend: { color: '#89938C', fontSize: 11 },
  error: { color: '#A33B31', marginVertical: 10, padding: 12, backgroundColor: '#FCEBE9', borderRadius: 10 },
  refresh: { alignSelf: 'center', flexDirection: 'row', alignItems: 'center', gap: 8, paddingVertical: 14, paddingHorizontal: 16, marginTop: 12, borderRadius: 12 },
  refreshIcon: { color: '#078343', fontSize: 18, fontWeight: '800' },
  refreshText: { color: '#078343', fontWeight: '700', fontSize: 12 },
  pressed: { opacity: 0.75 },
});
