"""Fixtures partagées des tests des applications."""

import factory
import pytest

from apps.accounts.models import Utilisateur


class UtilisateurFabrique(factory.django.DjangoModelFactory):
    """Construit un compte utilisateur valide pour les tests."""

    email = factory.Sequence(lambda numero: f"vendeur-{numero}@exemple.test")
    nom = "Rakoto"
    prenom = "Hery"
    telephone = ""

    class Meta:
        model = Utilisateur
        skip_postgeneration_save = True

    @factory.post_generation
    def mot_de_passe(self, cree: bool, extrait: str | None, **kwargs) -> None:
        """Affecte un mot de passe de test après la création du compte."""
        self.set_password(extrait or "Fleur!Miroir8472")
        if cree:
            self.save(update_fields=["password"])


@pytest.fixture
def utilisateur_vendeur(db) -> Utilisateur:
    """Fournit un compte vendeur actif pour un test isolé."""
    return UtilisateurFabrique()
