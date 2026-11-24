import type { Client, Commande, Produit } from './session-api';

export function orderDisplayName(order: Commande, clients: Client[], products: Produit[]) {
  const clientName = clients.find((client) => client.public_id === order.client)?.nomClient || 'Client';
  const productNames = order.lignes
    .map((line) => products.find((product) => product.public_id === line.product)?.nomProduit)
    .filter((name): name is string => !!name);
  const otherCount = productNames.length - 1;
  const items = productNames.length > 0
    ? `${productNames[0]}${otherCount > 0 ? ` + ${otherCount} autre${otherCount > 1 ? 's' : ''} article${otherCount > 1 ? 's' : ''}` : ''}`
    : `${order.lignes.length} article${order.lignes.length > 1 ? 's' : ''}`;
  return `${clientName} · ${items}`;
}
