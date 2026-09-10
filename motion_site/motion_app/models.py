from django.db import models
from django.contrib.auth.models import AbstractUser


class UserProfile(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    position = models.CharField(max_length=150)
    bio = models.TextField()
    avatar = models.ImageField(upload_to='avatars')
    cv_file = models.FileField(upload_to='cv')
    RoleChoices = (
        ('admin', 'admin'),
        ('employee', 'employee'),
    )
    user_role = models.CharField(max_length=20, choices=RoleChoices, default='employee')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


    def get_average_rating(self):
        ratings = self.review_user.all()
        if ratings.exists():
            return round(sum([i.rating for i in ratings]) / ratings.count(), 2)
        return 0

    def get_count_people(self):
        return self.review_user.count()


class Direction(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10)

    def __str__(self):
        return self.title


class Project(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField()
    icon = models.CharField(max_length=10)
    CategoryChoices = (
        ('AI', 'AI'),
        ('Web', 'Web'),
        ('LLM', 'LLM'),
        ('ML', 'ML'),
        ('Backend', 'Backend'),
        ('Frontend', 'Frontend'),
        ('Design', 'Design'),
    )
    category = models.CharField(max_length=50, choices=CategoryChoices)
    StatusChoices = (
        ('active', 'Active'),
        ('review', 'Review'),
        ('done', 'Done'),
        ('on_hold', 'On hold'),
    )
    status = models.CharField(max_length=20, choices=StatusChoices, default='active')

    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_average_rating(self):
        ratings = self.project_review.all()
        if ratings.exists():
            return round(sum([i.rating for i in ratings]) / ratings.count(), 2)
        return 0

    def get_count_people(self):
        return self.project_review.count()



class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='project_memberships')
    role_in_project = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.user} - {self.project}'


class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()

    PriorityChoices = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High priority'),
    )
    priority = models.CharField(max_length=20, choices=PriorityChoices, default='medium')

    StatusChoices = (
        ('new', 'New'),
        ('hold', 'Hold'),
        ('in_progress', 'In progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    )
    status = models.CharField(max_length=20, choices=StatusChoices, default='new')

    assigned_to = models.ManyToManyField(UserProfile, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Activity(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='activities')
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user}: {self.description}'


class SiteInfo(models.Model):
    about_text = models.TextField()
    contact_email = models.EmailField()
    instagram = models.CharField(max_length=100)
    telegram = models.CharField(max_length=100)
    location = models.CharField(max_length=150)

    def __str__(self):
        return 'Site info'


class Review(models.Model):
    text_review = models.TextField()
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='review_user')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_review', null=True, blank=True)
    rating = models.PositiveIntegerField(choices=[(i,str(i))for i in range(1,6)])
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user},{self.rating}'