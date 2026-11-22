"""Rend le journal de sécurité réellement immuable au niveau PostgreSQL.

Les méthodes ``save``/``delete`` du modèle ne protègent que le code Python :
``QuerySet.update()``, ``QuerySet.delete()`` et le SQL direct les contournent.
Ce trigger refuse toute modification ou suppression de ligne, quel que soit
le chemin d'accès.

``TRUNCATE`` n'est volontairement pas bloqué : Django l'utilise pour vider la
base entre deux tests transactionnels. En production, retirez ce droit au rôle
applicatif (``REVOKE TRUNCATE, UPDATE, DELETE ON journaux_securite FROM ...``).
"""

from django.db import migrations

CREER = """
CREATE FUNCTION journaux_securite_refuser_modification() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Le journal de sécurité est immuable (% interdit).', TG_OP
        USING ERRCODE = 'integrity_constraint_violation';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER journaux_securite_immuable_ligne
    BEFORE UPDATE OR DELETE ON journaux_securite
    FOR EACH ROW EXECUTE FUNCTION journaux_securite_refuser_modification();
"""

SUPPRIMER = """
DROP TRIGGER IF EXISTS journaux_securite_immuable_ligne ON journaux_securite;
DROP FUNCTION IF EXISTS journaux_securite_refuser_modification();
"""


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [migrations.RunSQL(sql=CREER, reverse_sql=SUPPRIMER)]
