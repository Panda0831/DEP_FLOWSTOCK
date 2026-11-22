import logging

from django.db import transaction
from django.utils import timezone

security_logger = logging.getLogger("security")


def security_event(event, *, user=None, ip_address=None, **details):
    identity = getattr(user, "email", None) or "anonymous"
    public_id = str(getattr(user, "public_id", "")) if user else ""
    extra = " ".join(f"{key}={value}" for key, value in details.items())
    security_logger.info(
        "event=%s user=%s public_id=%s ip=%s %s",
        event,
        identity,
        public_id,
        ip_address or "unknown",
        extra,
    )


@transaction.atomic
def change_password(*, user, new_password, ip_address=None):
    user.set_password(new_password)
    user.last_password_change = timezone.now()
    user.save(update_fields=("password", "last_password_change", "updated_at"))
    security_event("password_changed", user=user, ip_address=ip_address)


@transaction.atomic
def change_role(*, actor, target, role, ip_address=None):
    if role not in ("ADMIN", "VENDEUR"):
        raise ValueError("Rôle invalide")
    previous = target.role
    target.role = role
    target.save(update_fields=("role", "updated_at"))
    security_event(
        "role_changed",
        user=actor,
        ip_address=ip_address,
        target=str(target.public_id),
        from_role=previous,
        to_role=role,
    )
