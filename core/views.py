import json
import logging
import mimetypes
import os

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.http import FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .models import (
    Profile, Skill, Education, Experience, Project,
    BlogPost,
)
from .forms import ContactForm
from .github_sync import maybe_sync_github_projects


logger = logging.getLogger(__name__)

HERO_BIO = (
    'I turn raw, messy data into clean dashboards and business insights using Power BI, SQL, Python, and Excel. '
    'Available for freelance and full-time opportunities.'
)

ABOUT_BIO = (
    "I'm a Computer Science & Engineering graduate from Daffodil International University with 4+ years of hands-on "
    'experience delivering data analytics, BI, and database projects for real clients — not just coursework.\n\n'
    'I specialize in building Power BI dashboards with custom DAX measures, designing SQL databases, and automating '
    'reporting workflows using Excel Power Query and Python. My work spans e-commerce sales analysis, retail inventory '
    'management, supply chain reporting, and academic research.\n\n'
    "I've delivered 20+ paid projects, built dashboards tracking millions in revenue, and helped clients cut costs "
    'through data-driven decisions. I\'m currently open to freelance engagements and full-time Data Analyst roles in '
    'Bangladesh and remotely.'
)


def index(request):
    profile = Profile.objects.first()
    try:
        maybe_sync_github_projects(cache=cache, profile=profile, token=os.environ.get('GITHUB_TOKEN'))
    except Exception as exc:
        logger.warning('GitHub sync skipped for homepage: %s', exc)

    skills = Skill.objects.all()
    skill_categories = {}
    for skill in skills:
        cat = skill.get_category_display()
        skill_categories.setdefault(cat, []).append(skill)

    context = {
        'profile': profile,
        'hero_bio': (profile.hero_tagline if profile and profile.hero_tagline else HERO_BIO),
        'about_bio': (profile.bio if profile and profile.bio else ABOUT_BIO),
        'primary_title': profile.get_primary_title() if profile else 'CSE Graduate',
        'skill_categories': skill_categories,
        'education': Education.objects.all(),
        'experience': Experience.objects.all(),
        'projects': Project.objects.prefetch_related('gallery_images').all(),
        'blog_posts': BlogPost.objects.filter(is_published=True)[:3],
        'contact_form': ContactForm(),
        'typing_texts': json.dumps(profile.get_typing_list()) if profile else json.dumps([
            'A Student',
            'A Learner',
            'Data Analyst',
            'Web Developer',
        ]),
    }
    return render(request, 'index.html', context)


def project_list(request):
    profile = Profile.objects.first()
    projects_qs = Project.objects.prefetch_related('gallery_images').all().order_by('-created_at')
    paginator = Paginator(projects_qs, 9)
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    return render(request, 'projects_list.html', {'projects': projects, 'profile': profile})


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True)
    paginator = Paginator(posts, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    return render(request, 'blog_list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    recent = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    return render(request, 'blog_detail.html', {'post': post, 'recent_posts': recent})


def contact_submit(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            message = form.save()
            profile = Profile.objects.first()
            recipient_email = profile.email if profile else getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost')
            email_subject = f"Portfolio contact: {message.subject}"
            email_body = (
                f"Name: {message.name}\n"
                f"Email: {message.email}\n"
                f"Subject: {message.subject}\n\n"
                f"Message:\n{message.message}"
            )

            try:
                email = EmailMessage(
                    subject=email_subject,
                    body=email_body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@localhost'),
                    to=[recipient_email],
                    reply_to=[message.email],
                )
                email.send(fail_silently=False)
            except Exception as exc:
                logger.exception('Failed to send contact email: %s', exc)
                return JsonResponse({'success': False, 'message': 'Message saved, but email delivery failed.'}, status=500)

            return JsonResponse({'success': True, 'message': 'Thank you! Your message has been sent.'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)


def download_resume(request):
    profile = Profile.objects.first()
    if not profile or not profile.resume:
        return JsonResponse({'error': 'No resume uploaded'}, status=404)
    content_type, _ = mimetypes.guess_type(profile.resume.path)
    return FileResponse(
        open(profile.resume.path, 'rb'),
        content_type=content_type or 'application/octet-stream',
        as_attachment=True,
        filename=f"{profile.name.replace(' ', '_')}_Resume.pdf",
    )
