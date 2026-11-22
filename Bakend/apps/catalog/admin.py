from django.contrib import admin

from .models import Categorie, Fournisseur, Produit

admin.site.register(Categorie)
admin.site.register(Fournisseur)
admin.site.register(Produit)
