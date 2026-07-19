from django.db import models
from django.utils.text import slugify


class Profile(models.Model):
    """Singleton profile — only one instance should exist."""
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, help_text="e.g. CSE Graduate | Data Analyst | Web Developer")
    hero_tagline = models.TextField(
        blank=True,
        help_text="Short intro shown under your name in the hero section (leave blank to use the default).",
    )
    bio = models.TextField()
    academic_summary = models.TextField(blank=True, help_text="Brief academic aspirations for scholarship committees")
    photo = models.ImageField(upload_to='profile/', blank=True)
    resume = models.FileField(upload_to='resume/', blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    telegram_url = models.URLField(blank=True)
    email = models.EmailField()
    typing_texts = models.CharField(
        max_length=500, blank=True,
        help_text="Comma-separated phrases for the typing animation, e.g. 'Data Analyst,Web Developer,CSE Graduate'"
    )

    class Meta:
        verbose_name = "Profile / Hero Section"
        verbose_name_plural = "Profile / Hero Section"

    def __str__(self):
        return self.name

    def get_typing_list(self):
        if self.typing_texts:
            parts = [t.strip() for t in self.typing_texts.replace('|', ',').split(',')]
            return [part for part in parts if part]

        parts = [t.strip() for t in self.title.replace('|', ',').split(',')]
        return [part for part in parts if part] or [self.title]

    def get_primary_title(self):
        typing_list = self.get_typing_list()
        return typing_list[0] if typing_list else self.title


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('programming', 'Programming Languages'),
        ('data', 'Data Analysis'),
        ('web', 'Web Development'),
        ('tools', 'Tools & Frameworks'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    proficiency = models.PositiveIntegerField(help_text="Proficiency percentage (0-100)")
    icon_class = models.CharField(max_length=100, blank=True, help_text="Font Awesome or Devicon class, e.g. 'fab fa-python'")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['category', 'order', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Service(models.Model):
    ICON_CHOICES = [
        ('chart', 'Chart / Analytics'),
        ('database', 'Database'),
        ('globe', 'Web / Globe'),
        ('brain', 'AI / Brain'),
        ('file', 'Report / File'),
        ('cogs', 'Automation / Cogs'),
        ('code', 'Code'),
        ('cloud', 'Cloud'),
    ]
    title = models.CharField(max_length=150)
    description = models.TextField(help_text="Short description of the service offered.")
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='chart')
    button_label = models.CharField(
        max_length=50, default='Discuss',
        help_text="Label for the action button, e.g. 'Discuss', 'Contact', 'Place Order'.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    def icon_class(self):
        mapping = {
            'chart': 'fas fa-chart-line',
            'database': 'fas fa-database',
            'globe': 'fas fa-globe',
            'brain': 'fas fa-brain',
            'file': 'fas fa-file-alt',
            'cogs': 'fas fa-cogs',
            'code': 'fas fa-code',
            'cloud': 'fas fa-cloud',
        }
        return mapping.get(self.icon, 'fas fa-star')


class Education(models.Model):
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    field_of_study = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    gpa = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = "Education"

    def __str__(self):
        return f"{self.degree} — {self.institution}"


class Experience(models.Model):
    company = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.role} at {self.company}"


class Project(models.Model):
    CATEGORY_CHOICES = [
        ('data', 'Data Analysis'),
        ('web', 'Web Development'),
        ('app', 'App Development'),
        ('ml', 'Machine Learning'),
        ('programming', 'Programming'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='projects/', blank=True)
    tech_stack = models.CharField(max_length=500, help_text="Comma-separated, e.g. 'Python, Django, PostgreSQL'")
    github_url = models.URLField(blank=True, help_text="Link to the source code repository (e.g. GitHub).")
    live_url = models.URLField(blank=True, help_text="Link to the live demo / deployed app. For Power BI projects, paste your published dashboard link here (e.g. app.powerbi.com/view?r=...).")
    github_repo_id = models.BigIntegerField(
        blank=True,
        null=True,
        unique=True,
        help_text="GitHub repository ID for auto-synced projects (optional).",
    )
    synced_from_github = models.BooleanField(
        default=False,
        help_text="Set automatically for projects created by GitHub sync. "
                  "Synced projects are updated from GitHub; manually added/edited projects are never overwritten.",
    )
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def get_cover_image(self):
        if self.image:
            return self.image

        first_gallery_image = self.gallery_images.first()
        if first_gallery_image:
            return first_gallery_image.image

        return None

    def get_gallery_images(self):
        return self.gallery_images.all()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_tech_list(self):
        return [t.strip() for t in self.tech_stack.split(',')]


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, related_name='gallery_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'Project Image'
        verbose_name_plural = 'Project Images'

    def __str__(self):
        if self.caption:
            return f'{self.project.title} - {self.caption}'
        return f'{self.project.title} - Image {self.pk or self.order}'


class Certificate(models.Model):
    title = models.CharField(max_length=200)
    issuer = models.CharField(max_length=200)
    date = models.DateField()
    image = models.ImageField(upload_to='certificates/', blank=True)
    credential_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.title} — {self.issuer}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    excerpt = models.CharField(max_length=400, blank=True)
    image = models.ImageField(upload_to='blog/', blank=True)
    published_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class AcademicGoal(models.Model):
    target_degree = models.CharField(max_length=200, help_text="e.g. Master's in Computer Science")
    research_interests = models.TextField()
    target_countries = models.CharField(max_length=300, blank=True, help_text="Comma-separated, e.g. 'Germany, Canada, USA'")
    achievements = models.TextField(blank=True, help_text="Academic achievements, honors, publications")
    statement_summary = models.TextField(blank=True, help_text="Brief statement of purpose summary")

    class Meta:
        verbose_name = "Academic Goal"
        verbose_name_plural = "Academic Goals"

    def __str__(self):
        return self.target_degree

    def get_countries_list(self):
        if self.target_countries:
            return [c.strip() for c in self.target_countries.split(',')]
        return []


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} — {self.name}"
