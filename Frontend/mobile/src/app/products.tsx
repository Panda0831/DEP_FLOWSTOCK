import { useEffect, useState } from 'react';
import { ResourceScreen } from '@/components/resource-screen';
import { useAuth } from '@/lib/auth-context';
import { api, type Page } from '@/lib/session-api';

type Choice = { public_id: string; nomCategorie?: string; nomFournisseur?: string };

export default function ProductsScreen() {
  const { user } = useAuth();
  const admin = user?.role === 'ADMIN' || user?.is_staff;
  const [categories, setCategories] = useState<Choice[]>([]);
  const [suppliers, setSuppliers] = useState<Choice[]>([]);

  useEffect(() => {
    if (!admin) return;
    let active = true;
    Promise.all([api.get<Choice[] | Page<Choice>>('/categories/'), api.get<Choice[] | Page<Choice>>('/suppliers/')])
      .then(([categoryResult, supplierResult]) => {
        if (!active) return;
        setCategories(Array.isArray(categoryResult) ? categoryResult : categoryResult.results);
        setSuppliers(Array.isArray(supplierResult) ? supplierResult : supplierResult.results);
      })
      .catch(() => { if (active) { setCategories([]); setSuppliers([]); } });
    return () => { active = false; };
  }, [admin]);

  return <ResourceScreen
    title="Produits"
    subtitle="Catalogue, prix de vente et niveaux d’alerte"
    endpoint="/products/"
    titleKey="nomProduit"
    subtitleKeys={['prixVente', 'seuilAlerte']}
    canEdit={!!admin}
    fields={[
      { key: 'nomProduit', label: 'Nom du produit' },
      { key: 'prixVente', label: 'Prix de vente (Ar)', placeholder: 'Prix de vente (Ar)' },
      ...(admin ? [{ key: 'prixAchat', label: 'Prix d’achat (Ar)', placeholder: 'Prix d’achat (Ar)' }] : []),
      { key: 'seuilAlerte', label: 'Seuil d’alerte', placeholder: 'Stock minimum' },
      { key: 'idCategorie', label: 'Catégorie', optional: true, clearToNull: true, options: categories.map((item) => ({ value: item.public_id, label: item.nomCategorie || 'Catégorie' })) },
      { key: 'idFournisseur', label: 'Fournisseur', optional: true, clearToNull: true, options: suppliers.map((item) => ({ value: item.public_id, label: item.nomFournisseur || 'Fournisseur' })) },
    ]} />;
}
