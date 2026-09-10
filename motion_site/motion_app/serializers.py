from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, Direction, Project, ProjectMember, Task, Activity, SiteInfo



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'position', 'bio', 'user_role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserProfile.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if user and user.is_active:
            return user
        raise serializers.ValidationError('Неверные учетные данные')

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'id': instance.id,
                'username': instance.username,
                'email': instance.email,
                'user_role': instance.user_role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }



class ListUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'first_name', 'last_name', 'position', 'avatar']


class DetailUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'position', 'bio', 'avatar', 'cv_file', 'user_role']



class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = '__all__'



class ProjectMemberSerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(), source='user', write_only=True
    )

    class Meta:
        model = ProjectMember
        fields = ['id', 'project', 'user', 'user_id', 'role_in_project']



class ListProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'title', 'icon', 'category', 'status']


class DetailProjectSerializer(serializers.ModelSerializer):
    participants = ProjectMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'icon', 'category', 'status',
                  'created_at', 'participants']


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'



class ListTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'priority', 'status', 'project']


class DetailTaskSerializer(serializers.ModelSerializer):
    assigned_to = ListUserProfileSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'



class ActivitySerializer(serializers.ModelSerializer):
    user = ListUserProfileSerializer(read_only=True)

    class Meta:
        model = Activity
        fields = ['id', 'user', 'description', 'created_at']



class SiteInfoSerializer(serializers.ModelSerializer):
    participants_count = serializers.SerializerMethodField()
    projects_count = serializers.SerializerMethodField()
    directions_count = serializers.SerializerMethodField()

    class Meta:
        model = SiteInfo
        fields = ['about_text', 'contact_email', 'instagram', 'telegram', 'location',
                  'participants_count', 'projects_count', 'directions_count']

    def get_participants_count(self, obj):
        return UserProfile.objects.count()

    def get_projects_count(self, obj):
        return Project.objects.count()

    def get_directions_count(self, obj):
        return Direction.objects.count()
