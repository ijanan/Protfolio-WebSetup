import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django.setup()

from core.models import Profile

profile = Profile.objects.first()
if profile:
    print(f"✓ Profile found: {profile.name}")
    print(f"✓ Bio: {profile.bio[:80] if profile.bio else 'EMPTY - using default'}")
    print(f"✓ Title: {profile.title}")
else:
    print("✗ No profile found - template will use defaults")
