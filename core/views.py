import json
import mimetypes

from django.http import FileResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .models import (
    Profile, Skill, Education, Experience, Project,
    Certificate, BlogPost, AcademicGoal,
)
from .forms import ContactForm


def index(request):
    profile = Profile.objects.first()
    skills = Skill.objects.all()
    skill_categories = {}
    for skill in skills:
        cat = skill.get_category_display()
        skill_categories.setdefault(cat, []).append(skill)

    context = {
        'profile': profile,
        'skill_categories': skill_categories,
        'education': Education.objects.all(),
        'experience': Experience.objects.all(),
        'projects': Project.objects.all(),
        'certificates': Certificate.objects.all(),
        'blog_posts': BlogPost.objects.filter(is_published=True)[:3],
        'academic_goals': AcademicGoal.objects.all(),
        'contact_form': ContactForm(),
        'typing_texts': json.dumps(profile.get_typing_list()) if profile else '[]',
    }
    return render(request, 'index.html', context)


def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    related = Project.objects.filter(category=project.category).exclude(pk=project.pk)[:3]
    return render(request, 'project_detail.html', {
        'project': project,
        'related_projects': related,
    })


def project_list(request):
    profile = Profile.objects.first()
    projects_qs = Project.objects.all().order_by('-created_at')
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
            form.save()
            return JsonResponse({'success': True, 'message': 'Thank you! Your message has been sent.'})
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=405)


def download_resume(request):
    profile = get_object_or_404(Profile)
    if not profile.resume:
        return JsonResponse({'error': 'No resume uploaded'}, status=404)
    content_type, _ = mimetypes.guess_type(profile.resume.path)
    return FileResponse(
        open(profile.resume.path, 'rb'),
        content_type=content_type or 'application/octet-stream',
        as_attachment=True,
        filename=f"{profile.name.replace(' ', '_')}_Resume.pdf",
    )
