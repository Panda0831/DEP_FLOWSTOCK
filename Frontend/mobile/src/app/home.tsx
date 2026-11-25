import { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import { useAuth } from '@/lib/auth-context';
import { api, type Stock } from '@/lib/session-api';
import { AppPageHeading } from '@/components/page-heading';
import { MotionPressable } from '@/components/motion';
import { ProfitTrendChart, type ProfitTrendPoint } from '@/components/profit-trend-chart';
import { ScreenState } from '@/components/screen-state';
import { HitSize, Radius, Type } from '@/constants/theme';
import { useAppTheme, type AppTheme } from '@/hooks/use-app-theme';

type MonthlyProfitReport = { mois: string; benefice_net: string };

const makeStyles = (t: AppTheme) => StyleSheet.create({
  page: { flex: 1, backgroundColor: t.background },
  content: { width: '100%', maxWidth: 920, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 20, paddingBottom: 36 },
  headingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 },
  heading: { flex: 1 },
  date: { color: t.secondaryText, fontSize: 14, textTransform: 'capitalize', marginTop: 4 },
  account: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 14, borderWidth: 1, borderColor: t.separator, borderRadius: Radius.control, backgroundColor: t.surface },
  accountText: { color: t.text, fontSize: 14, fontWeight: '600' },
  error: { color: t.danger, fontSize: 14, lineHeight: 20, marginBottom: 16 },
  sectionTitle: { ...Type.headline, color: t.text, marginBottom: 12 },
  statGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 26 },
  stat: { flexGrow: 1, flexBasis: 180, minHeight: 132, padding: 18, backgroundColor: t.surface, borderRadius: Radius.card, borderWidth: 1, borderColor: t.separator },
  statAlert: { backgroundColor: t.warningSurface, borderColor: t.warningSurface },
  statLabel: { ...Type.footnote, color: t.secondaryText, fontWeight: '600' },
  statValue: { color: t.text, fontSize: 32, lineHeight: 38, fontWeight: '700', marginTop: 14 },
  statHint: { color: t.secondaryText, fontSize: 13, marginTop: 3 },
  alertValue: { color: t.warning },
  actionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 26 },
  action: { flexGrow: 1, flexBasis: 190, minHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, backgroundColor: t.tint, borderRadius: Radius.control },
  actionSecondary: { backgroundColor: t.surface, borderWidth: 1, borderColor: t.separator },
  actionMark: { color: t.onTint, fontSize: 21, fontWeight: '500' },
  actionMarkSecondary: { color: t.tint },
  actionText: { color: t.onTint, fontSize: 15, fontWeight: '600' },
  actionTextSecondary: { color: t.text },
  panel: { backgroundColor: t.surface, borderRadius: Radius.card, borderWidth: 1, borderColor: t.separator, overflow: 'hidden', marginBottom: 24 },
  panelHeader: { minHeight: 60, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderBottomWidth: 1, borderBottomColor: t.separator },
  panelTitle: { ...Type.headline, color: t.text },
  seeAll: { color: t.tint, fontSize: 14, fontWeight: '600', minHeight: HitSize, textAlignVertical: 'center' },
  alertRow: { minHeight: 68, paddingHorizontal: 18, flexDirection: 'row', alignItems: 'center', gap: 12, borderBottomWidth: 1, borderBottomColor: t.separator },
  alertDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: t.warning },
  alertName: { color: t.text, fontSize: 15, fontWeight: '600', flex: 1 },
  alertQty: { color: t.warning, fontSize: 14, fontWeight: '700' },
  alertCopy: { flex: 1, minWidth: 0 },
  restockButton: { minHeight: 44, justifyContent: 'center', paddingHorizontal: 11, borderWidth: 1, borderColor: t.separator, borderRadius: Radius.control, backgroundColor: t.surface },
  restockButtonText: { color: t.tint, fontSize: 14, lineHeight: 20, fontWeight: '700' },
  empty: { color: t.secondaryText, fontSize: 15, padding: 20 },
  lowerLinks: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  lowerLink: { minHeight: HitSize, justifyContent: 'center', paddingHorizontal: 12 },
  lowerLinkText: { color: t.secondaryText, fontSize: 14, fontWeight: '500' },
  loader: { marginVertical: 32 },
});

export default function HomeScreen() {
  const router = useRouter();
  const t = useAppTheme();
  const styles = useMemo(() => makeStyles(t), [t]);
  const { user, isReady } = useAuth();
  const [items, setItems] = useState<Stock[]>([]);
  const [alerts, setAlerts] = useState<Stock[]>([]);
  const [profitTrend, setProfitTrend] = useState<ProfitTrendPoint[]>([]);
  const [profitError, setProfitError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const isAdmin = user?.role === 'ADMIN' || !!user?.is_staff;

  useEffect(() => {
    if (isReady && !user) router.replace('/');
  }, [isReady, router, user]);

  const refresh = useCallback(async () => {
    setRefreshing(true);
    setError('');
    try {
      const [stock, lowStock] = await Promise.all([
        api.get<Stock[]>('/stock/'),
        api.get<Stock[]>('/stock/alerts/'),
      ]);
      setItems(stock);
      setAlerts(lowStock);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Le stock est indisponible. Réessayez dans un instant.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { if (isReady && user) void refresh(); }, [isReady, refresh, user]);

  const refreshProfitTrend = useCallback(async () => {
    if (!isAdmin) return;
    setProfitError('');
    try {
      const today = new Date();
      const firstMonth = new Date(today.getFullYear(), today.getMonth() - 5, 1);
      const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
      const formatDate = (date: Date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      const reports = await api.get<MonthlyProfitReport[]>('/reports/monthly/', {
        start_date: formatDate(firstMonth),
        end_date: formatDate(lastDay),
      });
      const byMonth = new Map(reports.map((report) => [report.mois.slice(0, 7), Number(report.benefice_net)]));
      setProfitTrend(Array.from({ length: 6 }, (_, index) => {
        const month = new Date(firstMonth.getFullYear(), firstMonth.getMonth() + index, 1);
        const key = `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, '0')}`;
        return { month: key, value: byMonth.get(key) ?? 0 };
      }));
    } catch (e) {
      setProfitError(e instanceof Error ? e.message : 'L’évolution du bénéfice est indisponible.');
    }
  }, [isAdmin]);

  useEffect(() => {
    if (isReady && user && isAdmin) void refreshProfitTrend();
  }, [isAdmin, isReady, refreshProfitTrend, user]);

  const refreshDashboard = useCallback(async () => {
    await Promise.all([refresh(), refreshProfitTrend()]);
  }, [refresh, refreshProfitTrend]);

  if (!isReady || !user) return <SafeAreaView style={styles.page}><ScreenState type="loading" title="Préparation de votre espace…" /></SafeAreaView>;

  const totalUnits = items.reduce((sum, item) => sum + Number(item.stock || 0), 0);
  const today = new Date().toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <SafeAreaView style={styles.page} edges={['top']}>
      <StatusBar />
      <ScrollView showsVerticalScrollIndicator={false} showsHorizontalScrollIndicator={false} contentContainerStyle={styles.content} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void refreshDashboard()} tintColor={t.tint} />}>
        <View style={styles.headingRow}>
          <View style={styles.heading}>
            <AppPageHeading title="Vue d’ensemble" />
            <Text style={styles.date}>{today}</Text>
          </View>
          <MotionPressable onPress={() => router.push('/profile')} style={styles.account} accessibilityRole="link" accessibilityLabel="Ouvrir mon compte">
            <Text style={styles.accountText}>Mon compte</Text>
          </MotionPressable>
        </View>
        {loading ? <ScreenState type="loading" title="Chargement de votre stock…" compact />
          : !!error ? <ScreenState
            type="error"
            title="Le stock n’a pas pu être actualisé."
            description={error}
            actionLabel="Réessayer"
            onAction={() => void refreshDashboard()}
          /> : <>
          <View style={styles.statGrid}>
            <View style={styles.stat}>
              <Text style={styles.statLabel}>Références en stock</Text>
              <Text style={styles.statValue}>{items.length}</Text>
              <Text style={styles.statHint}>Produits suivis</Text>
            </View>
            <View style={styles.stat}>
              <Text style={styles.statLabel}>Unités disponibles</Text>
              <Text style={styles.statValue}>{totalUnits.toLocaleString('fr-FR')}</Text>
              <Text style={styles.statHint}>Toutes références</Text>
            </View>
            <View style={[styles.stat, alerts.length > 0 && styles.statAlert]}>
              <Text style={styles.statLabel}>À réapprovisionner</Text>
              <Text style={[styles.statValue, alerts.length > 0 && styles.alertValue]}>{alerts.length}</Text>
              <Text style={styles.statHint}>Seuil atteint ou dépassé</Text>
            </View>
          </View>

          {isAdmin && (profitError
            ? <Text accessibilityRole="alert" style={styles.error}>{profitError}</Text>
            : profitTrend.length > 0 && <ProfitTrendChart points={profitTrend} />)}

          <Text style={styles.sectionTitle}>Actions courantes</Text>
          <View style={styles.actionGrid}>
            {isAdmin && <MotionPressable onPress={() => router.push('/stock/new')} style={styles.action} accessibilityRole="link" accessibilityLabel="Enregistrer une entrée de stock">
              <Text style={styles.actionMark}>＋</Text><Text style={styles.actionText}>Entrée de stock</Text>
            </MotionPressable>}
            {isAdmin && <MotionPressable onPress={() => router.push({ pathname: '/products', params: { add: '1' } })} style={[styles.action, styles.actionSecondary]} accessibilityRole="link" accessibilityLabel="Ajouter un produit">
              <Text style={[styles.actionMark, styles.actionMarkSecondary]}>＋</Text><Text style={[styles.actionText, styles.actionTextSecondary]}>Ajouter un produit</Text>
            </MotionPressable>}
            <MotionPressable onPress={() => router.push('/orders/new')} style={[styles.action, styles.actionSecondary]} accessibilityRole="link" accessibilityLabel="Créer une commande">
              <Text style={[styles.actionMark, styles.actionMarkSecondary]}>＋</Text><Text style={[styles.actionText, styles.actionTextSecondary]}>Nouvelle commande</Text>
            </MotionPressable>
          </View>

          <View style={styles.panel}>
            <View style={styles.panelHeader}>
              <Text style={styles.panelTitle}>Stock à surveiller</Text>
              <MotionPressable onPress={() => router.push('/stock')} accessibilityRole="link"><Text style={styles.seeAll}>Voir le stock</Text></MotionPressable>
            </View>
            {alerts.length === 0 ? <ScreenState
              type="success"
              title={items.length ? 'Aucun réapprovisionnement à prévoir.' : 'Votre stock apparaîtra ici.'}
              description={items.length ? 'Tous les produits sont au-dessus de leur seuil d’alerte.' : 'Ajoutez des produits et enregistrez leurs premières quantités.'}
              actionLabel={!items.length && isAdmin ? 'Ajouter un produit' : undefined}
              onAction={!items.length && isAdmin ? () => router.push({ pathname: '/products', params: { add: '1' } }) : undefined}
            /> : alerts.slice(0, 5).map((item, index) => (
              <View key={item.public_id} style={[styles.alertRow, index === Math.min(alerts.length, 5) - 1 && { borderBottomWidth: 0 }]}>
                <View style={styles.alertDot} />
                <View style={styles.alertCopy}>
                  <Text style={styles.alertName} numberOfLines={1}>{item.nomProduit}</Text>
                  <Text style={styles.alertQty}>{item.stock} restant(s)</Text>
                </View>
                {isAdmin && <MotionPressable
                  onPress={() => router.push({ pathname: '/purchases', params: { add: '1', product: item.public_id } })}
                  style={styles.restockButton}
                  accessibilityRole="button"
                  accessibilityLabel={`Créer un achat pour réapprovisionner ${item.nomProduit}`}>
                  <Text style={styles.restockButtonText}>Commander</Text>
                </MotionPressable>}
              </View>
            ))}
          </View>

          {isAdmin && <View style={styles.lowerLinks}>
            <MotionPressable onPress={() => router.push('/reports')} style={styles.lowerLink} accessibilityRole="link"><Text style={styles.lowerLinkText}>Consulter les rapports</Text></MotionPressable>
          </View>}
        </>}
      </ScrollView>
    </SafeAreaView>
  );
}
