import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
export default function ExpensesScreen() {
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  return <ResourceScreen title="Dépenses" subtitle="Enregistrez et consultez les charges de votre activité." endpoint="/expenses/" titleKey="libelle" subtitleKeys={['date', 'montant']} listTitle="Dépenses enregistrées" emptyText="Aucune dépense enregistrée pour le moment." itemMarker="Ar" canEdit={!!admin} canView={!!admin} fields={[{ key: 'libelle', label: 'Nom de la dépense', placeholder: 'Ex. Transport' }, { key: 'montant', label: 'Montant (Ar)', placeholder: '0', keyboardType: 'decimal-pad' }, { key: 'date', label: 'Date', placeholder: 'AAAA-MM-JJ', optional: true }]} />;
}
