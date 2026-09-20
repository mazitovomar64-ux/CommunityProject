from .models import UserProfile,Direction,Team,TeamMember,Project,ProjectMember,Task,Activity,SiteInfo
from modeltranslation.translator import TranslationOptions,register


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


@register(Activity)
class ActivityTranslationOptions(TranslationOptions):
    fields = ('description',)


@register(SiteInfo)
class SiteInfoTranslationOptions(TranslationOptions):
    fields = ('about_text', 'location')
