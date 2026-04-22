from .models import Profile


def site_profile(request):
    """Expose the primary Profile globally for base template usage."""
    return {
        'site_profile': Profile.objects.first(),
    }
