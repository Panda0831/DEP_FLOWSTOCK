import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
export default function ExpensesScreen() {
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  return <ResourceScreen title="Dépenses" subtitle="Charges enregistrées dans la comptabilité" endpoint="/expenses/" titleKey="libelle" subtitleKeys={['date', 'montant']} canEdit={!!admin} canView={!!admin} fields={[{ key: 'libelle', label: 'Libellé' }, { key: 'montant', label: 'Montant (Ar)' }, { key: 'date', label: 'Date (AAAA-MM-JJ)', optional: true }]} />;
}
