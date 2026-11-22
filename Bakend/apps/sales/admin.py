from django.contrib import admin

from .models import Client, Commande, LigneCommande, Livraison

admin.site.register(Client)
admin.site.register(Commande)
admin.site.register(LigneCommande)
admin.site.register(Livraison)
