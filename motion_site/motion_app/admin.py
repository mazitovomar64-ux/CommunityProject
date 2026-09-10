from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Direction, Project, ProjectMember, Task, Activity, SiteInfo, Review


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'position', 'user_role']
    fieldsets = UserAdmin.fieldsets + (
        ('Motion Community', {'fields': ('position', 'bio', 'avatar', 'cv_file', 'user_role')}),
    )


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['title']


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'created_at']
    inlines = [ProjectMemberInline]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'priority', 'status', 'created_at']
    filter_horizontal = ['assigned_to']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'description', 'created_at']


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ['contact_email', 'instagram', 'telegram', 'location']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['text_review', 'user', 'project', 'rating', 'created_date']