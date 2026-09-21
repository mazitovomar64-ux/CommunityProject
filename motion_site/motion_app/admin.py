from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from modeltranslation.admin import TranslationAdmin

from .models import Activity, Direction, Project, ProjectMember, Review, SiteInfo, Task, Team, TeamMember, UserProfile ,Chat,Message, Service, Translation


@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin, TranslationAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'position', 'user_role', 'work_status', 'is_active']
    list_filter = UserAdmin.list_filter + ('user_role', 'work_status')
    filter_horizontal = UserAdmin.filter_horizontal + ('directions',)
    fieldsets = UserAdmin.fieldsets + (
        (
            'Motion Community',
            {
                'fields': (
                    'position',
                    'bio',
                    'avatar',
                    'cv_file',
                    'user_role',
                    'work_status',
                    'directions'
                )
            }
        ),
    )


@admin.register(Direction)
class DirectionAdmin(TranslationAdmin):
    list_display = ['title', 'slug', 'description', 'icon']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Team)
class TeamAdmin(TranslationAdmin):
    list_display = ['name', 'created_by', 'created_at']


@admin.register(TeamMember)
class TeamMemberAdmin(TranslationAdmin):
    list_display = ['team', 'user', 'role_in_team', 'joined_at']


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 0


@admin.register(Project)
class ProjectAdmin(TranslationAdmin):
    list_display = ['title', 'category', 'status', 'team', 'created_by', 'created_at']
    list_filter = ['status', 'category', 'directions']
    filter_horizontal = ['directions']
    inlines = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(TranslationAdmin):
    list_display = ['project', 'user', 'role_in_project', 'joined_at']


@admin.register(Task)
class TaskAdmin(TranslationAdmin):
    list_display = ['title', 'project', 'priority', 'status', 'submitted_at', 'created_at', 'updated_at']
    filter_horizontal = ['assigned_to']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'description', 'created_at']


@admin.register(SiteInfo)
class SiteInfoAdmin(TranslationAdmin):
    list_display = ['contact_email', 'phone', 'instagram', 'telegram', 'linkedin', 'location']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'rating', 'created_date']

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_general', 'created_date']
    filter_horizontal = ['person']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'text', 'send_time']


@admin.register(Service)
class ServiceAdmin(TranslationAdmin):
    list_display = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Translation)
class TranslationEntryAdmin(TranslationAdmin):
    list_display = ['key', 'value']
    search_fields = ['key', 'value']