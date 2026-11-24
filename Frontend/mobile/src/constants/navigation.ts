/** Main destinations stay focused on the everyday stock workflow. */
export type RouteHref =
  | '/home' | '/products' | '/categories' | '/suppliers'
  | '/orders' | '/orders/new' | '/clients' | '/deliveries' | '/deliveries/new' | '/stock' | '/stock/new' | '/purchases'
  | '/reports' | '/expenses' | '/profile' | '/change-password';

export type PrimaryLink = {
  label: string;
  href: RouteHref;
  icon: { ios: string; android: string; web: string };
  admin?: boolean;
};

export const PRIMARY_LINKS = [
  { label: 'Aperçu', href: '/home', icon: { ios: 'square.grid.2x2.fill', android: 'dashboard', web: 'dashboard' } },
  { label: 'Produits', href: '/products', icon: { ios: 'shippingbox.fill', android: 'inventory_2', web: 'inventory_2' } },
  { label: 'Stock', href: '/stock', icon: { ios: 'cube.box.fill', android: 'inventory', web: 'inventory' } },
  { label: 'Rapports', href: '/reports', admin: true, icon: { ios: 'chart.bar.fill', android: 'bar_chart', web: 'bar_chart' } },
] as const satisfies readonly PrimaryLink[];

export const SECTION_LINKS = [
  { label: 'Vue générale', href: '/home', group: 'Accueil' },
  { label: 'Produits', href: '/products', group: 'Catalogue' },
  { label: 'Catégories', href: '/categories', group: 'Catalogue' },
  { label: 'Fournisseurs', href: '/suppliers', group: 'Catalogue' },
  { label: 'Stock', href: '/stock', group: 'Activité' },
  { label: 'Commandes', href: '/orders', group: 'Activité' },
  { label: 'Clients', href: '/clients', group: 'Activité' },
  { label: 'Livraisons', href: '/deliveries', group: 'Activité' },
  { label: 'Achats', href: '/purchases', group: 'Activité', admin: true },
  { label: 'Dépenses', href: '/expenses', group: 'Finances', admin: true },
  { label: 'Rapports', href: '/reports', group: 'Finances', admin: true },
  { label: 'Mon compte', href: '/profile', group: 'Compte' },
  { label: 'Mot de passe', href: '/change-password', group: 'Compte' },
] as const;

export const PRIMARY_HREFS: readonly RouteHref[] = PRIMARY_LINKS.map((link) => link.href);

/** Sibling screens of the current section, shown as text links inside the page heading. */
export function siblingLinks(pathname: string) {
  const current = SECTION_LINKS.find((link) => link.href === pathname);
  if (!current) return [];
  return SECTION_LINKS.filter((link) => link.group === current.group && link.href !== pathname);
}
