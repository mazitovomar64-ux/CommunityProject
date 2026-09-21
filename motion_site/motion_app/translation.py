from modeltranslation.translator import TranslationOptions, register

from .models import Direction, Project, ProjectMember, Service, SiteInfo, Task, Team, TeamMember, Translation, UserProfile


@register(UserProfile)
class UserProfileTranslationOptions(TranslationOptions):
    fields = ('position', 'bio')


@register(Direction)
class DirectionTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(Team)
class TeamTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


@register(TeamMember)
class TeamMemberTranslationOptions(TranslationOptions):
    fields = ('role_in_team',)


@register(Project)
class ProjectTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(ProjectMember)
class ProjectMemberTranslationOptions(TranslationOptions):
    fields = ('role_in_project',)


@register(Task)
class TaskTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(SiteInfo)
class SiteInfoTranslationOptions(TranslationOptions):
    fields = ('about_text', 'location')


@register(Service)
class ServiceTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(Translation)
class TranslationTextOptions(TranslationOptions):
    fields = ('value',)