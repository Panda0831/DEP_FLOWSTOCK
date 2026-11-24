import { useLocalSearchParams, useRouter } from 'expo-router';
import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';

export default function ClientsScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ flow?: string; focus?: string; open?: string }>();
  const { user } = useAuth();
  return <ResourceScreen
    title="Clients"
    subtitle="Votre fichier clients FlowStock"
    endpoint="/clients/"
    titleKey="nomClient"
    subtitleKeys={['contact', 'adresse']}
    focusId={typeof params.focus === 'string' ? params.focus : undefined}
    openFocused={params.open === '1'}
    canDelete={user?.role === 'ADMIN' || !!user?.is_staff}
    fields={[
      { key: 'nomClient', label: 'Nom du client' },
      { key: 'contact', label: 'Téléphone ou e-mail' },
      { key: 'adresse', label: 'Adresse' },
    ]}
    onCreated={(client) => {
      if (params.flow === 'order') {
        router.replace({ pathname: '/orders/new', params: { client: client.public_id } });
      }
    }}
  />;
}
