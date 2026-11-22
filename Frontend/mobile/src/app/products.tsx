import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
export default function ProductsScreen() {
  const { user } = useAuth(); const admin = user?.role === 'ADMIN' || user?.is_staff;
  return <ResourceScreen title="Produits" subtitle="Catalogue, prix de vente et niveaux d’alerte" endpoint="/products/" titleKey="nomProduit" subtitleKeys={['prixVente', 'seuilAlerte']} canEdit={!!admin} fields={[
    { key: 'nomProduit', label: 'Nom du produit' }, { key: 'prixVente', label: 'Prix de vente', placeholder: 'Prix de vente (Ar)' }, ...(admin ? [{ key: 'prixAchat', label: 'Prix d’achat', placeholder: 'Prix d’achat (Ar)' }] : []), { key: 'seuilAlerte', label: 'Seuil d’alerte', placeholder: 'Stock minimum' }, { key: 'idCategorie', label: 'UUID catégorie (facultatif)', optional: true }, { key: 'idFournisseur', label: 'UUID fournisseur (facultatif)', optional: true },
  ]} />;
}
