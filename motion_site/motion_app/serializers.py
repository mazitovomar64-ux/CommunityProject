from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Activity, Chat, Direction, Message, Project, ProjectMember, Review, Service, SiteInfo, Task, Team, TeamMember, Translation, UserProfile

# Роли, которых можно добавлять в проекты/команды и назначать на задачи
MEMBER_ROLES = ['employee', 'team_lead']


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


class DirectionShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Direction
        fields = ['id', 'slug', 'title', 'icon']


class ListUserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)
    work_status_display = serializers.CharField(source='get_work_status_display', read_only=True)
    directions = DirectionShortSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'first_name', 'last_name', 'position', 'avatar', 'user_role', 'role_display', 'work_status', 'work_status_display', 'directions', 'average_rating']

    def get_average_rating(self, obj):
        return obj.get_average_rating()


class TeamShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id', 'name', 'description']


class DetailUserProfileSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)
    work_status_display = serializers.CharField(source='get_work_status_display', read_only=True)
    directions = DirectionShortSerializer(many=True, read_only=True)
    direction_ids = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all(), source='directions', many=True, write_only=True, required=False)
    team = serializers.SerializerMethodField()
    projects = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'position', 'position_ky', 'bio', 'bio_ky', 'avatar', 'cv_file', 'user_role', 'role_display', 'work_status', 'work_status_display', 'directions', 'direction_ids', 'average_rating', 'team', 'projects']
        read_only_fields = ['id', 'username', 'email', 'user_role', 'role_display', 'work_status_display', 'directions', 'average_rating', 'team', 'projects']

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_team(self, obj):
        membership = getattr(obj, 'team_membership', None)
        if not membership:
            return None
        return TeamShortSerializer(membership.team).data

    def get_projects(self, obj):
        memberships = obj.project_memberships.select_related('project', 'project__team').all()
        return ListProjectSerializer([m.project for m in memberships], many=True, context=self.context).data


class PublicUserProfileSerializer(DetailUserProfileSerializer):
    """Публичный профиль сотрудника: без email, CV и служебных полей."""

    class Meta(DetailUserProfileSerializer.Meta):
        fields = ['id', 'username', 'first_name', 'last_name', 'position', 'bio', 'avatar', 'user_role', 'role_display', 'work_status', 'work_status_display', 'directions', 'average_rating', 'team', 'projects']
        read_only_fields = fields


class DirectionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Direction
        fields = ['id', 'slug', 'title', 'description', 'icon']


class DirectionManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = ['id', 'slug', 'title', 'title_ky', 'description', 'description_ky', 'icon']
        read_only_fields = ['id']


class TeamMemberSerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role__in=MEMBER_ROLES), source='user', write_only=True)

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
    projects = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'created_by', 'created_at', 'members', 'members_count', 'projects']
        read_only_fields = ['id', 'created_by', 'created_at', 'members', 'members_count', 'projects']

    def get_projects(self, obj):
        return ListProjectSerializer(obj.projects.all(), many=True).data


class ListProjectSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    members_count = serializers.IntegerField(source='participants.count', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True, default=None)
    directions = DirectionShortSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'icon', 'cover', 'category', 'category_display', 'status', 'status_display', 'directions', 'team', 'team_name', 'created_at', 'members_count']


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role__in=MEMBER_ROLES), source='user', write_only=True)

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
    directions = DirectionShortSerializer(many=True, read_only=True)
    participants = ProjectMemberSerializer(many=True, read_only=True)
    tasks_count = serializers.IntegerField(source='tasks.count', read_only=True)
    average_rating = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True, default=None)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'title_ky', 'description', 'description_ky', 'icon', 'cover', 'github_url', 'demo_url', 'category', 'category_display', 'status', 'status_display', 'directions', 'created_at', 'created_by', 'created_by_name', 'team', 'team_name', 'participants', 'tasks_count', 'average_rating']

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.email


class ProjectCreateSerializer(serializers.ModelSerializer):
    directions = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all(), many=True, required=False)

    class Meta:
        model = Project
        fields = ['id', 'title', 'title_ky', 'description', 'description_ky', 'icon', 'cover', 'github_url', 'demo_url', 'category', 'status', 'directions', 'team', 'created_at', 'created_by']
        read_only_fields = ['id', 'created_at', 'created_by']


class ListTaskSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to = ListUserProfileSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'priority', 'priority_display', 'status', 'status_display', 'project', 'project_title', 'assigned_to', 'github_url', 'submitted_at', 'created_at', 'updated_at']


class DetailTaskSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to = ListUserProfileSerializer(many=True, read_only=True)
    project_title = serializers.CharField(source='project.title', read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'priority_display', 'status', 'status_display', 'project', 'project_title', 'assigned_to', 'result_text', 'github_url', 'submitted_at', 'created_at', 'updated_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(user_role__in=MEMBER_ROLES), many=True, required=False)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'status', 'project', 'assigned_to', 'result_text', 'github_url', 'submitted_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'result_text', 'github_url', 'submitted_at', 'created_at', 'updated_at']

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


class TaskProgressSerializer(serializers.ModelSerializer):
    """Что может менять исполнитель: статус (по разрешённым переходам),
    результат работы и ссылку на GitHub. Простой workflow:
    new/hold -> in_progress -> review; из review можно вернуть в in_progress.
    Статус done ставит только админ или тимлид."""
    ALLOWED_TRANSITIONS = {
        'new': {'in_progress'},
        'hold': {'in_progress'},
        'in_progress': {'hold', 'review'},
        'review': {'in_progress'},
        'done': set(),
    }

    class Meta:
        model = Task
        fields = ['id', 'status', 'result_text', 'github_url', 'submitted_at']
        read_only_fields = ['id', 'submitted_at']

    def validate(self, attrs):
        current = self.instance.status
        if current == 'done':
            raise serializers.ValidationError({'status': 'Задача уже завершена, изменять её нельзя.'})

        new_status = attrs.get('status', current)
        if new_status != current and new_status not in self.ALLOWED_TRANSITIONS[current]:
            allowed = ', '.join(sorted(self.ALLOWED_TRANSITIONS[current])) or '—'
            raise serializers.ValidationError({'status': f'Переход «{current}» → «{new_status}» недоступен. Допустимо: {allowed}.'})

        if new_status == 'review' and current != 'review':
            result_text = attrs.get('result_text', self.instance.result_text)
            github_url = attrs.get('github_url', self.instance.github_url)
            if not (result_text or github_url):
                raise serializers.ValidationError({'result_text': 'Чтобы отправить задачу на проверку, укажите результат или ссылку на GitHub.'})
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get('status') == 'review' and instance.status != 'review':
            instance.submitted_at = timezone.now()
        return super().update(instance, validated_data)


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
        fields = ['id', 'about_text', 'contact_email', 'phone', 'instagram', 'telegram', 'linkedin', 'location', 'participants_count', 'projects_count', 'directions_count']
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


class SiteInfoManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteInfo
        fields = ['id', 'about_text', 'about_text_ky', 'contact_email', 'phone', 'instagram', 'telegram', 'linkedin', 'location', 'location_ky']
        read_only_fields = ['id']


class ContactsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SiteInfo
        fields = ['phone', 'contact_email', 'telegram', 'instagram', 'linkedin', 'location']


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = ['id', 'title', 'description', 'icon', 'order']


class ServiceManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'title', 'title_ky', 'description', 'description_ky', 'icon', 'order', 'is_active']
        read_only_fields = ['id']


class TranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translation
        fields = ['id', 'key', 'value_ru', 'value_ky']
        read_only_fields = ['id']


class UserManageSerializer(serializers.ModelSerializer):
    """Управление пользователями (только админ): создание, изменение, роли."""
    password = serializers.CharField(write_only=True, min_length=8, required=False)
    role_display = serializers.CharField(source='get_user_role_display', read_only=True)
    directions = serializers.PrimaryKeyRelatedField(queryset=Direction.objects.all(), many=True, required=False)

    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'position', 'position_ky', 'bio', 'bio_ky', 'avatar', 'cv_file', 'user_role', 'role_display', 'work_status', 'directions', 'is_active', 'date_joined']
        read_only_fields = ['id', 'role_display', 'date_joined']

    def validate(self, attrs):
        if not self.instance and 'password' not in attrs:
            raise serializers.ValidationError({'password': 'Обязательное поле.'})

        request = self.context.get('request')
        if self.instance and request and self.instance.pk == request.user.pk:
            if 'user_role' in attrs and attrs['user_role'] != self.instance.user_role:
                raise serializers.ValidationError({'user_role': 'Нельзя менять собственную роль.'})
            if attrs.get('is_active') is False:
                raise serializers.ValidationError({'is_active': 'Нельзя деактивировать самого себя.'})
        return attrs

    def create(self, validated_data):
        directions = validated_data.pop('directions', [])
        password = validated_data.pop('password')
        user = UserProfile.objects.create_user(password=password, **validated_data)
        user.directions.set(directions)
        return user

    def update(self, instance, validated_data):
        directions = validated_data.pop('directions', None)
        password = validated_data.pop('password', None)
        old_role = instance.user_role

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # при понижении админа снимаем доступ в Django-админку
        if old_role == 'admin' and instance.user_role != 'admin':
            instance.is_staff = False
            instance.is_superuser = False

        if password:
            instance.set_password(password)
        instance.save()

        if directions is not None:
            instance.directions.set(directions)
        return instance


MAX_CHAT_UPLOAD_SIZE = 10 * 1024 * 1024
ALLOWED_CHAT_UPLOAD_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.csv'}


def validate_chat_upload(upload):
    """Ограничиваем размер и тип загружаемых файлов (иначе через чат можно залить html/js/exe)."""
    if upload is None:
        return upload
    if upload.size > MAX_CHAT_UPLOAD_SIZE:
        raise serializers.ValidationError('Файл слишком большой (максимум 10 МБ).')
    extension = ('.' + upload.name.rsplit('.', 1)[-1].lower()) if '.' in upload.name else ''
    if extension not in ALLOWED_CHAT_UPLOAD_EXTENSIONS:
        raise serializers.ValidationError('Этот тип файла загружать нельзя.')
    return upload


class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'chat', 'text', 'sender_id', 'sender_name', 'image', 'file', 'send_time']
        read_only_fields = ['id', 'chat', 'sender_id', 'sender_name', 'send_time']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.email

    def validate_image(self, value):
        return validate_chat_upload(value)

    def validate_file(self, value):
        return validate_chat_upload(value)

    def validate(self, attrs):
        text = (attrs.get('text') or '').strip()
        image = attrs.get('image')
        file = attrs.get('file')
        if not text and not image and not file:
            raise serializers.ValidationError('Сообщение не может быть пустым.')
        return attrs

    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ChatSerializer(serializers.ModelSerializer):
    person = UserShortSerializer(many=True, read_only=True)
    person_ids = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.filter(is_active=True), many=True, source='person', write_only=True, required=False)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ['id', 'name', 'is_general', 'person', 'person_ids', 'created_date', 'last_message']
        read_only_fields = ['id', 'is_general', 'created_date']

    def get_last_message(self, obj):
        last = obj.messages.order_by('-send_time', '-id').first()
        return MessageSerializer(last).data if last else None