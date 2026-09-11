from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Activity, Direction, Project, ProjectMember, Review, SiteInfo, Task, Team, TeamMember, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'position', 'bio', 'avatar', 'cv_file', 'user_role']
        read_only_fields = ['id', 'user_role']
        extra_kwargs = {'password': {'write_only': True, 'min_length': 8}}

    def create(self, validated_data):
        validated_data['user_role'] = 'employee'
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        return UserProfile.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError('Неверная почта или пароль.')
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {'user': UserShortSerializer(instance).data, 'access': str(refresh.access_token), 'refresh': str(refresh)}


class UserShortSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'position', 'avatar', 'user_role', 'role_display']


class ListUserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'position', 'avatar', 'user_role', 'role_display', 'average_rating']

    def get_average_rating(self, obj):
        return obj.get_average_rating()


class TeamShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'description']


class DetailUserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)
    team = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'position', 'bio', 'avatar', 'cv_file', 'user_role', 'role_display', 'average_rating', 'team']
        read_only_fields = ['id', 'username', 'email', 'user_role', 'role_display', 'average_rating', 'team']

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_team(self, obj):
        membership = getattr(obj, 'team_membership', None)
        if not membership:
            return None
        return TeamShortSerializer(membership.team).data


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ['id', 'title', 'description', 'icon']


class TeamMemberSerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role='employee'), source='user', write_only=True)

    class Meta:
        model = TeamMember
        fields = ['id', 'team', 'user', 'user_id', 'role_in_team', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def validate(self, attrs):
        user = attrs.get('user', self.instance.user if self.instance else None)
        if user:
            queryset = TeamMember.objects.filter(user=user)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'user_id': 'Этот пользователь уже состоит в другой команде.'})
        return attrs


class TeamSerializer(serializers.ModelSerializer):
    members = TeamMemberSerializer(many=True, read_only=True)
    members_count = serializers.IntegerField(source='members.count', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'members', 'members_count']
        read_only_fields = ['id', 'created_by', 'created_at', 'members', 'members_count']


class ListProjectSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    members_count = serializers.IntegerField(source='participants.count', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'icon', 'category', 'category_display', 'status', 'status_display', 'team', 'created_at', 'members_count']


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role='employee'), source='user', write_only=True)

    class Meta:
        model = ProjectMember
        fields = ['id', 'project', 'user', 'user_id', 'role_in_project', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def validate(self, attrs):
        project = attrs.get('project', self.instance.project if self.instance else None)
        user = attrs.get('user', self.instance.user if self.instance else None)
        if project and user:
            queryset = ProjectMember.objects.filter(project=project, user=user)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({'user_id': 'Этот пользователь уже добавлен в проект.'})
        return attrs


class DetailProjectSerializer(serializers.ModelSerializer):
    participants = ProjectMemberSerializer(many=True, read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)
    average_rating = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'icon', 'category', 'category_display', 'status', 'status_display', 'created_at', 'created_by', 'team', 'participants', 'tasks_count', 'average_rating']

    def get_average_rating(self, obj):
        return obj.get_average_rating()


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'icon', 'category', 'status', 'team', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']


class ListTaskSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to = ListUserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'priority', 'priority_display', 'status', 'status_display', 'project', 'assigned_to', 'created_at', 'updated_at']


class DetailTaskSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to = ListUserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'priority_display', 'status', 'status_display', 'project', 'assigned_to', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role='employee'), many=True, required=False)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'status', 'project', 'assigned_to', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        project = attrs.get('project', self.instance.project if self.instance else None)
        assigned_users = attrs.get('assigned_to')

        if self.instance and assigned_users is None:
            assigned_users = list(self.instance.assigned_to.all())

        if project and assigned_users is not None:
            member_ids = set(project.participants.values_list('user_id', flat=True))
            invalid_users = [user.id for user in assigned_users if user.id not in member_ids]
            if invalid_users:
                raise serializers.ValidationError({'assigned_to': 'Все исполнители должны быть участниками выбранного проекта.'})

        return attrs


class ActivitySerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'user', 'description', 'created_at']


class SiteInfoSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    directions_count = serializers.SerializerMethodField()

    class Meta:
        model = SiteInfo
        fields = ['id', 'about_text', 'contact_email', 'instagram', 'telegram', 'location', 'participants_count', 'projects_count', 'directions_count']
        read_only_fields = ['id', 'participants_count', 'projects_count', 'directions_count']

    def get_participants_count(self, obj):
        return UserProfile.objects.filter(is_active=True).count()

    def get_projects_count(self, obj):
        return Project.objects.count()

    def get_directions_count(self, obj):
        return Direction.objects.count()


class ReviewSerializer(serializers.ModelSerializer):
    user = UserShortSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'text_review', 'user', 'project', 'rating', 'created_date']
        read_only_fields = ['id', 'user', 'created_date']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)