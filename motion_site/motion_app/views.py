from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404
from django.utils import translation
from rest_framework import generics, status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import SAFE_METHODS, AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .chat import build_message_payload, can_access_chat, get_general_chat
from .models import Activity, Chat, Direction, Message, Project, ProjectMember, Review, Service, SiteInfo, Task, Team, TeamMember, Translation, UserProfile
from .permissions import IsAdminRole, IsAuthenticatedReadOnlyOrAdmin, IsAuthenticatedReadOnlyOrManager, IsManagerRole, ManagerWriteAdminDelete, ReviewPermission, can_manage_project, is_admin, is_manager, is_team_lead
from .serializers import ActivitySerializer, ChatSerializer, ContactsSerializer, DetailProjectSerializer, DetailTaskSerializer, DetailUserProfileSerializer, DirectionManageSerializer, DirectionSerializer, ListProjectSerializer, ListTaskSerializer, ListUserProfileSerializer, LoginSerializer, MessageSerializer, ProjectCreateSerializer, ProjectMemberSerializer, PublicUserProfileSerializer, ReviewSerializer, ServiceManageSerializer, ServiceSerializer, SiteInfoManageSerializer, SiteInfoSerializer, TaskCreateSerializer, TaskProgressSerializer, TeamMemberSerializer, TeamSerializer, TranslationSerializer, UserManageSerializer, UserSerializer


def add_activity(user, description):
    Activity.objects.create(user=user, description=description)


class LargePagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 500


class ChatPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


def filter_by_direction(queryset, value):
    if not value:
        return queryset
    condition = Q(directions__slug=value)
    if value.isdigit():
        condition |= Q(directions__id=int(value))
    return queryset.filter(condition).distinct()


def current_language():
    return (translation.get_language() or 'ru').split('-')[0]


def get_translations(prefix=''):
    items = Translation.objects.filter(key__startswith=prefix) if prefix else Translation.objects.all()
    return {item.key: item.value for item in items}


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        add_activity(request.user, f'Зарегистрирован новый пользователь: {user.get_full_name() or user.email}')
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CustomLoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'detail': 'Поле refresh обязательно.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response({'detail': 'Недействительный refresh-токен.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Вы успешно вышли из аккаунта.'}, status=status.HTTP_205_RESET_CONTENT)


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DetailUserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        add_activity(user, 'Обновил профиль')


class MyPermissionsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        admin = is_admin(request.user)
        manager = is_manager(request.user)

        return Response({
            'user_role': request.user.user_role,
            'role_display': request.user.get_user_role_display(),
            'cabinet': 'admin' if admin else 'team_lead' if is_team_lead(request.user) else 'employee',
            'is_admin': admin,
            'is_team_lead': is_team_lead(request.user),
            'can_access_admin_panel': bool(request.user.is_staff),
            'can_register_users': admin,
            'can_manage_users': admin,
            'can_manage_roles': admin,
            'can_create_projects': manager,
            'can_delete_projects': admin,
            'can_manage_project_members': manager,
            'can_create_tasks': manager,
            'can_update_tasks': manager,
            'can_delete_tasks': admin,
            'can_manage_teams': admin,
            'can_manage_content': admin
        })


class MyPortfolioView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        project_memberships = ProjectMember.objects.filter(user=user).select_related('project', 'project__team')
        project_ids = project_memberships.values_list('project_id', flat=True)

        projects = Project.objects.filter(id__in=project_ids).select_related('team').order_by('-created_at')

        tasks = Task.objects.filter(project_id__in=project_ids, assigned_to=user).select_related('project').prefetch_related('assigned_to').order_by('-updated_at')

        team_membership = TeamMember.objects.filter(user=user).select_related('team').prefetch_related('team__members__user').first()

        activity = Activity.objects.filter(user=user).select_related('user').order_by('-created_at')[:10]

        team = TeamSerializer(team_membership.team).data if team_membership else None

        return Response({
            'user': DetailUserProfileSerializer(user).data,
            'stats': {
                'projects_count': projects.count(),
                'tasks_count': tasks.count(),
                'completed_tasks_count': tasks.filter(status='done').count()
            },
            'projects': ListProjectSerializer(projects, many=True).data,
            'tasks': ListTaskSerializer(tasks, many=True).data,
            'team': team,
            'activity': ActivitySerializer(activity, many=True).data
        })


class UserPortfolioView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        user = get_object_or_404(UserProfile, pk=pk, is_active=True)

        project_memberships = ProjectMember.objects.filter(user=user).select_related('project', 'project__team')
        project_ids = project_memberships.values_list('project_id', flat=True)

        projects = Project.objects.filter(id__in=project_ids).select_related('team').order_by('-created_at')

        team_membership = TeamMember.objects.filter(user=user).select_related('team').prefetch_related('team__members__user').first()

        team = TeamSerializer(team_membership.team).data if team_membership else None

        return Response({
            'user': PublicUserProfileSerializer(user, context={'request': request}).data,
            'stats': {
                'projects_count': projects.count()
            },
            'projects': ListProjectSerializer(projects, many=True).data,
            'team': team
        })


class UserProfileListAPIView(generics.ListAPIView):
    serializer_class = ListUserProfileSerializer
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.filter(is_active=True).prefetch_related('directions').order_by('first_name', 'last_name')

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        queryset = filter_by_direction(queryset, params.get('direction'))
        if params.get('work_status'):
            queryset = queryset.filter(work_status=params['work_status'])
        if params.get('role'):
            queryset = queryset.filter(user_role=params['role'])
        return queryset


class DetailUserProfileAPIView(generics.RetrieveAPIView):
    serializer_class = PublicUserProfileSerializer
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.filter(is_active=True).prefetch_related('directions')


class DirectionListAPIView(generics.ListAPIView):
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]
    pagination_class = LargePagination
    queryset = Direction.objects.all().order_by('title')


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().select_related('created_by').prefetch_related('members__user')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]

    def perform_create(self, serializer):
        team = serializer.save(created_by=self.request.user)
        add_activity(self.request.user, f'Создал команду «{team.name}»')

    def perform_update(self, serializer):
        team = serializer.save()
        add_activity(self.request.user, f'Изменил команду «{team.name}»')

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        add_activity(self.request.user, f'Удалил команду «{name}»')


class TeamMemberViewSet(viewsets.ModelViewSet):
    queryset = TeamMember.objects.all().select_related('team', 'user')
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()

        if is_admin(self.request.user):
            return queryset

        return queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        member = serializer.save()
        add_activity(self.request.user, f'Добавил пользователя «{member.user.get_full_name() or member.user.email}» в команду «{member.team.name}»')

    def perform_update(self, serializer):
        member = serializer.save()
        add_activity(self.request.user, f'Изменил участника команды «{member.team.name}»')

    def perform_destroy(self, instance):
        user_name = instance.user.get_full_name() or instance.user.email
        team_name = instance.team.name
        instance.delete()
        add_activity(self.request.user, f'Удалил пользователя «{user_name}» из команды «{team_name}»')


class ProjectListAPIView(generics.ListAPIView):
    serializer_class = ListProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all().select_related('team').prefetch_related('directions').order_by('-created_at', '-id')

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        queryset = filter_by_direction(queryset, params.get('direction'))
        if params.get('status'):
            queryset = queryset.filter(status=params['status'])
        return queryset


class ProjectDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DetailProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all().select_related('created_by', 'team').prefetch_related('directions', 'participants__user__directions', 'tasks')


class MyProjectListAPIView(generics.ListAPIView):
    serializer_class = ListProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(participants__user=user) | Q(created_by=user)).select_related('team').prefetch_related('directions').distinct().order_by('-created_at', '-id')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related('created_by', 'team').prefetch_related('directions', 'participants__user', 'tasks')
    serializer_class = ProjectCreateSerializer
    permission_classes = [ManagerWriteAdminDelete]

    def get_object(self):
        project = super().get_object()
        if self.request.method not in SAFE_METHODS and not can_manage_project(self.request.user, project):
            raise PermissionDenied('Вы не управляете этим проектом.')
        return project

    def get_serializer_class(self):
        if self.action == 'list':
            return ListProjectSerializer

        if self.action == 'retrieve':
            return DetailProjectSerializer

        return ProjectCreateSerializer

    def perform_create(self, serializer):
        project = serializer.save(created_by=self.request.user)
        add_activity(self.request.user, f'Создал проект «{project.title}»')

    def perform_update(self, serializer):
        project = serializer.save()
        add_activity(self.request.user, f'Изменил проект «{project.title}»')

    def perform_destroy(self, instance):
        title = instance.title
        instance.delete()
        add_activity(self.request.user, f'Удалил проект «{title}»')


class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all().select_related('project', 'user')
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrManager]

    def get_queryset(self):
        queryset = super().get_queryset()

        if is_admin(self.request.user):
            return queryset

        return queryset.filter(Q(project__participants__user=self.request.user) | Q(project__created_by=self.request.user)).distinct()

    def get_object(self):
        member = super().get_object()
        if self.request.method not in SAFE_METHODS and not can_manage_project(self.request.user, member.project):
            raise PermissionDenied('Вы не управляете этим проектом.')
        return member

    def perform_create(self, serializer):
        if not can_manage_project(self.request.user, serializer.validated_data['project']):
            raise PermissionDenied('Вы не управляете этим проектом.')
        member = serializer.save()
        add_activity(self.request.user, f'Добавил пользователя «{member.user.get_full_name() or member.user.email}» в проект «{member.project.title}»')

    def perform_update(self, serializer):
        if not can_manage_project(self.request.user, serializer.validated_data.get('project', serializer.instance.project)):
            raise PermissionDenied('Вы не управляете этим проектом.')
        member = serializer.save()
        add_activity(self.request.user, f'Изменил участника проекта «{member.project.title}»')

    def perform_destroy(self, instance):
        project_title = instance.project.title
        user_name = instance.user.get_full_name() or instance.user.email
        instance.delete()
        add_activity(self.request.user, f'Удалил пользователя «{user_name}» из проекта «{project_title}»')


class TaskListAPIView(generics.ListAPIView):
    serializer_class = ListTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.filter(assigned_to=self.request.user).select_related('project').prefetch_related('assigned_to').order_by('-updated_at')
        if self.request.query_params.get('status'):
            queryset = queryset.filter(status=self.request.query_params['status'])
        return queryset


class TaskDetailAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch', 'head', 'options']
    queryset = Task.objects.all().select_related('project').prefetch_related('assigned_to')

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return TaskProgressSerializer
        return DetailTaskSerializer

    def get_object(self):
        task = super().get_object()
        user = self.request.user
        is_assignee = task.assigned_to.filter(pk=user.pk).exists()

        if self.request.method == 'PATCH':
            allowed = is_assignee
        else:
            allowed = is_assignee or can_manage_project(user, task.project)

        if not allowed:
            raise PermissionDenied('Нет доступа к этой задаче.')
        return task

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        add_activity(request.user, f'Обновил задачу «{task.title}» (статус: {task.status})')
        return Response(DetailTaskSerializer(task, context={'request': request}).data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related('project').prefetch_related('assigned_to')
    serializer_class = TaskCreateSerializer

    def get_permissions(self):
        # создавать/менять: админ и тимлид; удалять: только админ
        if self.action == 'destroy':
            return [IsAdminRole()]
        return [IsManagerRole()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if is_admin(user):
            return queryset

        return queryset.filter(Q(project__created_by=user) | Q(project__participants__user=user)).distinct()

    def perform_create(self, serializer):
        if not can_manage_project(self.request.user, serializer.validated_data['project']):
            raise PermissionDenied('Вы не управляете этим проектом.')
        task = serializer.save()
        add_activity(self.request.user, f'Создал задачу «{task.title}»')

    def perform_update(self, serializer):
        if not can_manage_project(self.request.user, serializer.validated_data.get('project', serializer.instance.project)):
            raise PermissionDenied('Вы не управляете этим проектом.')
        task = serializer.save()
        add_activity(self.request.user, f'Изменил задачу «{task.title}»')

    def perform_destroy(self, instance):
        title = instance.title
        instance.delete()
        add_activity(self.request.user, f'Удалил задачу «{title}»')


class ActivityListAPIView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Activity.objects.all().select_related('user').order_by('-created_at')

        if is_admin(self.request.user) and self.request.query_params.get('all') == 'true':
            return queryset

        return queryset.filter(user=self.request.user)


class SiteInfoView(generics.RetrieveAPIView):
    serializer_class = SiteInfoSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        obj = SiteInfo.objects.first()
        if not obj:
            raise NotFound('Информация о сайте ещё не заполнена.')
        return obj


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related('user', 'project')
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]

    # def get_queryset(self):
    #     if is_admin(self.request.user):
    #         return self.queryset
    #
    #     return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        review = serializer.save()
        add_activity(self.request.user, f'Оставил отзыв с оценкой {review.rating}')

    def update(self, request, *args, **kwargs):
        obj = self.get_object()

        if not is_admin(request.user) and obj.user_id != request.user.id:
            raise PermissionDenied('Нельзя изменять чужой отзыв.')

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()

        if not is_admin(request.user) and obj.user_id != request.user.id:
            raise PermissionDenied('Нельзя удалять чужой отзыв.')

        return super().destroy(request, *args, **kwargs)


class ContactsView(generics.RetrieveAPIView):
    serializer_class = ContactsSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        obj = SiteInfo.objects.first()
        if not obj:
            raise NotFound('Контактная информация ещё не заполнена.')
        return obj


class ServiceListAPIView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]
    pagination_class = LargePagination
    queryset = Service.objects.filter(is_active=True)


class TranslationListAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request):
        return Response({'language': current_language(), 'translations': get_translations(request.query_params.get('prefix', ''))})


class HomeView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request):
        language = current_language()
        texts = get_translations('home.')
        context = {'request': request}

        projects = Project.objects.select_related('team').prefetch_related('directions').order_by('-created_at', '-id')[:3]
        directions = Direction.objects.filter(slug__isnull=False).order_by('title')

        return Response({
            'language': language,
            'hero': {
                'title': texts.get('home.title', ''),
                'subtitle': texts.get('home.subtitle', ''),
                'description': texts.get('home.description', '')
            },
            'actions': [
                {'key': 'projects', 'label': texts.get('home.cta.projects', ''), 'target': 'projects'},
                {'key': 'work_with_us', 'label': texts.get('home.cta.work_with_us', ''), 'target': 'contacts'}
            ],
            'stats': {
                'members_count': UserProfile.objects.filter(is_active=True).count(),
                'projects_count': Project.objects.count(),
                'directions_count': directions.count()
            },
            'featured_projects': ListProjectSerializer(projects, many=True, context=context).data,
            'directions': DirectionSerializer(directions, many=True, context=context).data
        })


class AboutView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    pagination_class = None

    def get(self, request):
        language = current_language()
        texts = get_translations('about.')
        info = SiteInfo.objects.first()

        about_text = info.about_text if info else ''

        focus_prefix = 'about.focus.'
        focus_areas = [{'key': key[len(focus_prefix):], 'title': value} for key, value in sorted(texts.items()) if key.startswith(focus_prefix)]

        return Response({
            'language': language,
            'title': texts.get('about.title', ''),
            'about_text': about_text,
            'mission': texts.get('about.mission', ''),
            'goal': texts.get('about.goal', ''),
            'focus_areas': focus_areas,
            'stats': {
                'members_count': UserProfile.objects.filter(is_active=True).count(),
                'projects_count': Project.objects.count()
            }
        })


# class RolesView(generics.GenericAPIView):
#     permission_classes = [IsAdminRole]
#     pagination_class = None
#
#     def get(self, request):
#         return Response([{'value': value, 'label': label} for value, label in UserProfile.RoleChoices])


class UserManageViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all().prefetch_related('directions').order_by('id')
    serializer_class = UserManageSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if params.get('role'):
            queryset = queryset.filter(user_role=params['role'])
        if params.get('is_active') in ('true', 'false'):
            queryset = queryset.filter(is_active=params['is_active'] == 'true')
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()
        add_activity(self.request.user, f'Создал пользователя «{user.get_full_name() or user.email}» (роль: {user.user_role})')

    def perform_update(self, serializer):
        user = serializer.save()
        add_activity(self.request.user, f'Изменил пользователя «{user.get_full_name() or user.email}»')

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()

        if user.pk == request.user.pk:
            return Response({'detail': 'Нельзя удалить самого себя.'}, status=status.HTTP_400_BAD_REQUEST)

        name = user.get_full_name() or user.email
        try:
            user.delete()
        except ProtectedError:
            return Response(
                {'detail': 'Нельзя удалить пользователя: он создал проекты или команды. Передайте их другому или деактивируйте пользователя (is_active=false).'},
                status=status.HTTP_409_CONFLICT
            )

        add_activity(request.user, f'Удалил пользователя «{name}»')
        return Response(status=status.HTTP_204_NO_CONTENT)


class DirectionManageViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all().order_by('title')
    serializer_class = DirectionManageSerializer
    permission_classes = [IsAdminRole]
    pagination_class = LargePagination


class ServiceManageViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceManageSerializer
    permission_classes = [IsAdminRole]
    pagination_class = LargePagination


class TranslationManageViewSet(viewsets.ModelViewSet):
    queryset = Translation.objects.all()
    serializer_class = TranslationSerializer
    permission_classes = [IsAdminRole]
    pagination_class = LargePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('prefix'):
            queryset = queryset.filter(key__startswith=self.request.query_params['prefix'])
        return queryset


class SiteInfoManageView(generics.RetrieveUpdateAPIView):
    serializer_class = SiteInfoManageSerializer
    permission_classes = [IsAdminRole]

    def get_object(self):
        obj = SiteInfo.objects.first()
        if not obj:
            obj = SiteInfo.objects.create(about_text='', contact_email='', instagram='', telegram='', location='')
        return obj


class ChatListAPIView(generics.ListCreateAPIView):

    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        get_general_chat()
        return Chat.objects.filter(Q(person=self.request.user) | Q(is_general=True)).distinct().prefetch_related('person', 'messages').order_by('-is_general', '-created_date', '-id')

    def perform_create(self, serializer):
        chat = serializer.save()
        chat.person.add(self.request.user)


class GeneralChatAPIView(generics.RetrieveAPIView):
    serializer_class = ChatSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_general_chat()


class MessageListAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        chat = get_object_or_404(Chat, pk=self.kwargs['chat_id'])

        if not can_access_chat(self.request.user, chat):
            raise PermissionDenied('Вы не состоите в этом чате.')

        return Message.objects.filter(chat=chat).select_related('sender').order_by('-send_time', '-id')


class MessageCreateAPIView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        chat = get_object_or_404(Chat, pk=self.kwargs['chat_id'])

        if not can_access_chat(self.request.user, chat):
            raise PermissionDenied('Вы не состоите в этом чате.')

        message = serializer.save(chat=chat)

        # чтобы остальные участники получили сообщение сразу, как и текстовые
        async_to_sync(get_channel_layer().group_send)(f'chat_{chat.pk}', build_message_payload(message))