import { useLocalSearchParams, useRouter } from 'expo-router';
import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';

export default function SuppliersScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ flow?: string }>();
  const { user } = useAuth();
  return <ResourceScreen
    title="Fournisseurs"
    subtitle="Retrouvez les partenaires associés à votre catalogue."
    endpoint="/suppliers/"
    titleKey="nomFournisseur"
    listTitle="Fournisseurs enregistrés"
    emptyText="Aucun fournisseur enregistré pour le moment."
    itemMarker="FRN"
    canEdit={user?.role === 'ADMIN' || !!user?.is_staff}
    fields={[{ key: 'nomFournisseur', label: 'Nom du fournisseur' }]}
    onCreated={(supplier) => {
      if (params.flow === 'purchase') {
        router.replace({ pathname: '/purchases', params: { add: '1', supplier: supplier.public_id } });
      }
    }}
  />;
}
