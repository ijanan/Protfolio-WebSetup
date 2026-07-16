from django import forms
from django.contrib import admin
from .models import (
    Profile, Skill, Education, Experience, Project, ProjectImage,
    BlogPost, ContactMessage,
)


class ProjectAdminForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'short_description': forms.Textarea(attrs={'rows': 3}),
            'full_description': forms.Textarea(attrs={'rows': 10}),
            'tech_stack': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = Project.CATEGORY_CHOICES


class ProjectCategoryFilter(admin.SimpleListFilter):
    title = 'category'
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        return Project.CATEGORY_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category=self.value())
        return queryset


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'title')
    fieldsets = (
        ('Hero Section', {
            'description': 'These fields control the top (hero) section of your homepage.',
            'fields': ('name', 'title', 'typing_texts', 'hero_tagline'),
        }),
        ('About Section', {
            'fields': ('bio', 'academic_summary'),
        }),
        ('Photo & Resume', {
            'fields': ('photo', 'resume'),
        }),
        ('Contact & Social Links', {
            'fields': ('email', 'github_url', 'linkedin_url', 'telegram_url'),
        }),
    )

    def has_add_permission(self, request):
        return not Profile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'proficiency', 'order')
    list_filter = ('category',)
    list_editable = ('proficiency', 'order')
    ordering = ('category', 'order')


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'institution', 'field_of_study', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    fieldsets = (
        ('Role', {
            'fields': ('role', 'company', 'is_current'),
        }),
        ('Duration', {
            'fields': ('start_date', 'end_date'),
        }),
        ('Details', {
            'fields': ('description',),
        }),
    )


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    max_num = 10
    fields = ('image', 'caption', 'order')
    ordering = ('order', 'id')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('title', 'category', 'featured', 'order', 'created_at', 'github_repo_id')
    list_filter = (ProjectCategoryFilter, 'featured')
    list_editable = ('featured', 'order')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'short_description', 'tech_stack')
    inlines = [ProjectImageInline]
    fieldsets = (
        ('Project Basics', {
            'fields': ('title', 'slug', 'category', 'featured', 'order', 'github_repo_id'),
        }),
        ('Summary', {
            'fields': ('short_description', 'full_description'),
        }),
        ('Media and Links', {
            'fields': ('image', 'tech_stack', 'github_url', 'live_url'),
        }),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_date')
    list_filter = ('is_published',)
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')
    search_fields = ('name', 'email', 'subject')
