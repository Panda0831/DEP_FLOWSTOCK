#!/usr/bin/env python
"""Utilitaire de gestion Django."""

import os
import sys


def main() -> None:
    """Lance les commandes d’administration Django."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django est introuvable. Installez les dépendances du backend.") from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
