from django.contrib.auth import get_user_model


def get_user_by_public_id(public_id):
    return get_user_model().objects.filter(public_id=public_id, is_active=True).first()
