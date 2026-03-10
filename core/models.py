from django.db import models
from django.utils.text import slugify


class Profile(models.Model):
    """Singleton profile — only one instance should exist."""
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, help_text="e.g. CSE Graduate | Data Analyst | Web Developer")
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
        verbose_name = "Profile"
        verbose_name_plural = "Profile"

    def __str__(self):
        return self.name

    def get_typing_list(self):
        if self.typing_texts:
            return [t.strip() for t in self.typing_texts.split(',')]
        return [self.title]


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
        ('ml', 'Machine Learning'),
        ('other', 'Other'),
    ]
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='projects/', blank=True)
    tech_stack = models.CharField(max_length=500, help_text="Comma-separated, e.g. 'Python, Django, PostgreSQL'")
    github_url = models.URLField(blank=True)
    live_url = models.URLField(blank=True)
    featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_tech_list(self):
        return [t.strip() for t in self.tech_stack.split(',')]


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
