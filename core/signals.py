from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .models import Profile


@receiver(post_migrate)
def create_default_profile(sender, **kwargs):
    """Ensure a single Profile row exists after migrations.

    On fresh deployments (e.g. PythonAnywhere) the DB starts empty and the
    Profile admin change form has nothing to edit, so updates appear to fail.
    Creating a default row here makes the admin usable immediately.
    """
    if not Profile.objects.exists():
        Profile.objects.create(
            name='Your Name',
            title='Your Title | e.g. Data Analyst',
            bio='Tell visitors about yourself.',
            email='your-email@example.com',
        )
