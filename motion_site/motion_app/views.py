from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Activity, Direction, Project, ProjectMember, Review, SiteInfo, Task, Team, TeamMember, UserProfile
from .permissions import IsAdminRole, IsAuthenticatedReadOnlyOrAdmin, ReadOnlyOrAdmin, ReviewPermission, is_admin
from .serializers import ActivitySerializer, DetailProjectSerializer, DetailTaskSerializer, DetailUserProfileSerializer, DirectionSerializer, ListProjectSerializer, ListTaskSerializer, ListUserProfileSerializer, LoginSerializer, ProjectCreateSerializer, ProjectMemberSerializer, ReviewSerializer, SiteInfoSerializer, TaskCreateSerializer, TeamMemberSerializer, TeamSerializer, UserSerializer


def add_activity(user, description):
    Activity.objects.create(user=user, description=description)


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

        return Response({
            'user_role': request.user.user_role,
            'role_display': request.user.get_user_role_display(),
            'is_admin': admin,
            'can_register_users': admin,
            'can_create_projects': admin,
            'can_manage_project_members': admin,
            'can_create_tasks': admin,
            'can_update_tasks': admin,
            'can_delete_tasks': admin,
            'can_manage_teams': admin
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


class UserProfileListAPIView(generics.ListAPIView):
    serializer_class = ListUserProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.filter(is_active=True).order_by('first_name', 'last_name')


class DetailUserProfileAPIView(generics.RetrieveAPIView):
    serializer_class = DetailUserProfileSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserProfile.objects.filter(is_active=True)


class DirectionListAPIView(generics.ListAPIView):
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]
    queryset = Direction.objects.all().order_by('title')


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all().select_related('created_by').prefetch_related('members__user')
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()

        if is_admin(self.request.user):
            return queryset

        return queryset.filter(members__user=self.request.user).distinct()

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
    queryset = Project.objects.all().select_related('team').order_by('-created_at')


class ProjectDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DetailProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all().select_related('created_by', 'team').prefetch_related('participants__user', 'tasks')


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related('created_by', 'team').prefetch_related('participants__user', 'tasks')
    serializer_class = ProjectCreateSerializer
    permission_classes = [ReadOnlyOrAdmin]

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
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()

        if is_admin(self.request.user):
            return queryset

        return queryset.filter(project__participants__user=self.request.user).distinct()

    def perform_create(self, serializer):
        member = serializer.save()
        add_activity(self.request.user, f'Добавил пользователя «{member.user.get_full_name() or member.user.email}» в проект «{member.project.title}»')

    def perform_update(self, serializer):
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
        return Task.objects.filter(assigned_to=self.request.user).select_related('project').prefetch_related('assigned_to').order_by('-updated_at')


class TaskDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DetailTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if is_admin(self.request.user):
            return Task.objects.all().select_related('project').prefetch_related('assigned_to')

        return Task.objects.filter(assigned_to=self.request.user).select_related('project').prefetch_related('assigned_to')


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related('project').prefetch_related('assigned_to')
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAdminRole]

    def perform_create(self, serializer):
        task = serializer.save()
        add_activity(self.request.user, f'Создал задачу «{task.title}»')

    def perform_update(self, serializer):
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
        return SiteInfo.objects.first()


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().select_related('user', 'project')
    serializer_class = ReviewSerializer
    permission_classes = [ReviewPermission]

    def get_queryset(self):
        if is_admin(self.request.user):
            return self.queryset

        return self.queryset.filter(user=self.request.user)

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