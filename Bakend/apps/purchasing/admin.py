from django.contrib import admin

from .models import Achat, HistoriqueAchat, LigneAchat, LigneReceptionAchat, ReceptionAchat


class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 0


class ReceptionAchatInline(admin.TabularInline):
    model = ReceptionAchat
    extra = 0


@admin.register(Achat)
class AchatAdmin(admin.ModelAdmin):
    list_display = ("reference", "idFournisseur", "dateCommande", "statut")
    search_fields = ("reference", "idFournisseur__nomFournisseur")
    list_filter = ("statut", "modeObtention")
    inlines = (LigneAchatInline, ReceptionAchatInline)


admin.site.register(LigneReceptionAchat)
admin.site.register(HistoriqueAchat)
