from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

class Category(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    icon        = models.CharField(max_length=50, default='bi-book')  # Bootstrap icon class
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)



class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title       = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    instructor  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses_taught')
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    thumbnail   = models.ImageField(upload_to='course_thumbnail/')
    trailer_url = models.URLField(blank=True, help_text="Youtube or Vimeo embed URL for free trailer")
    description = models.TextField()
    short_desc  = models.CharField(max_length=300)
    level       = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    price       = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_free     = models.BooleanField(default=False)
    is_published= models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    tags        = models.CharField(max_length=300, blank=True, help_text='Comma-seperated tags')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]
    
    @property
    def total_lessons(self):
        return self.lessons.count()
    @property
    def total_duration_minutes(self):
        return sum(l.duration_minutes for l in self.lessons.all())
        
    @property
    def total_duration_display(self):
        mins = self.total_duration_minutes
        h, m = divmod(mins, 60)
        return f'{h}h {m}m' if h else f'{m}m'

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)
    
    @property
    def review_count(self):
        return self.reviews.count()
    
    @property
    def enrollment_count(self):
        return self.enrollments.count()
    

class Lesson(models.Model):
    course          = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title           = models.CharField(max_length=200)
    order           = models.PositiveIntegerField(default=0)
    video_url       = models.URLField(help_text='YouTube/Vimeo embed URL or hosted video path')
    duration_minutes= models.PositiveIntegerField(default=0)
    description     = models.TextField(blank=True)
    is_free_preview = models.BooleanField(default=False)
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-order']

    def __str__(self):
        return f'{self.course.title} - {self.title}'

class Enrollment(models.Model):
    user            = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course          = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at     = models.DateTimeField(auto_now_add=True)
    completed       = models.BooleanField(default=False)
    minutes_watched = models.PositiveIntegerField(default=0)
    last_lesson     = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ('user', 'course')

    def __str__(self):
        return f'{self.user.email} -> {self.course.title}'

    @property
    def progress_percent(self):
        total = self.course.total_lessons
        if not total:
            return 0
        watched = self.minutes_watched
        total_mins = self.course.total_duration_minutes
        if not total_mins:
            return 0
        return min(int(watched / total_mins * 100), 100)
    

class Review(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course     = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating     = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} rated {self.course.title} {self.rating}★'
