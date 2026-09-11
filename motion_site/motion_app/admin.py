from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Activity, Direction, Project, ProjectMember, Review, SiteInfo, Task, Team, TeamMember, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'position', 'user_role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (
            'Motion Community',
            {
                'fields': (
                    'position',
                    'bio',
                    'avatar',
                    'cv_file',
                    'user_role'
                )
            }
        ),
    )


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'icon']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'role_in_team', 'joined_at']


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'status', 'team', 'created_by', 'created_at']
    inlines = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role_in_project', 'joined_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'priority', 'status', 'created_at', 'updated_at']
    filter_horizontal = ['assigned_to']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'description', 'created_at']


@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ['contact_email', 'instagram', 'telegram', 'location']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'rating', 'created_date']