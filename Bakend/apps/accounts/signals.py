import logging

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

security_logger = logging.getLogger("security")


def client_ip(request):
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return forwarded.split(",", 1)[0].strip() if forwarded else request.META.get("REMOTE_ADDR")


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    security_logger.info(
        "event=login_success user=%s public_id=%s ip=%s",
        user.email,
        user.public_id,
        client_ip(request),
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    security_logger.info(
        "event=logout user=%s public_id=%s ip=%s",
        getattr(user, "email", "anonymous"),
        getattr(user, "public_id", ""),
        client_ip(request),
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    security_logger.info("event=login_failed ip=%s", client_ip(request))


try:
    from axes.signals import user_locked_out

    @receiver(user_locked_out)
    def audit_lockout(sender, request, username, **kwargs):
        security_logger.info("event=account_locked ip=%s username=%s", client_ip(request), username)
except ImportError:
    pass


@receiver(pre_save, sender="accounts.User")
def capture_role_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    previous = sender.objects.filter(pk=instance.pk).values("password", "role").first()
    if previous:
        if previous["password"] != instance.password and instance.last_password_change is None:
            instance.last_password_change = timezone.now()
        if previous["role"] != instance.role:
            instance._previous_role = previous["role"]


@receiver(post_save, sender="accounts.User")
def audit_role_change(sender, instance, created, **kwargs):
    previous = getattr(instance, "_previous_role", None)
    if previous is not None:
        security_logger.info(
            "event=role_changed target=%s actor=admin-system from_role=%s to_role=%s",
            instance.public_id,
            previous,
            instance.role,
        )
