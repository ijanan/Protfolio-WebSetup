import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio.settings')
django.setup()

from core.models import Profile

profile = Profile.objects.first()
if profile:
    new_bio = """I'm a Computer Science & Engineering graduate from Daffodil International University with 4+ years of hands-on experience delivering data analytics, BI, and database projects for real clients — not just coursework.

I specialize in building Power BI dashboards with custom DAX measures, designing SQL databases, and automating reporting workflows using Excel Power Query and Python. My work spans e-commerce sales analysis, retail inventory management, supply chain reporting, and academic research.

I've delivered 20+ paid projects, built dashboards tracking millions in revenue, and helped clients cut costs through data-driven decisions. I'm currently open to freelance engagements and full-time Data Analyst roles in Bangladesh and remotely."""
    
    profile.bio = new_bio
    profile.title = "CSE Graduate | Data Analyst | Web Developer"
    profile.save()
    print("✓ Profile bio updated successfully!")
    print(f"✓ New bio first 100 chars: {profile.bio[:100]}")
else:
    print("✗ No profile found to update")
