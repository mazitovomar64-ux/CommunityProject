from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    UserSerializer,
    LoginSerializer,
    ListUserProfileSerializer,
    DetailUserProfileSerializer,
    DirectionSerializer,
    ListProjectSerializer,
    DetailProjectSerializer,
    ProjectCreateSerializer,
    ProjectMemberSerializer,
    ListTaskSerializer,
    DetailTaskSerializer,
    TaskCreateSerializer,
    ActivitySerializer,
    SiteInfoSerializer,
)
from .models import UserProfile, Direction, Project, ProjectMember, Task, Activity, SiteInfo



class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomLoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({'detail': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = DetailUserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user



class UserProfileListAPIView(generics.ListAPIView):
    serializer_class = ListUserProfileSerializer
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.all()


class DetailUserProfileAPIView(generics.RetrieveAPIView):
    serializer_class = DetailUserProfileSerializer
    permission_classes = [AllowAny]
    queryset = UserProfile.objects.all()



class DirectionListAPIView(generics.ListAPIView):
    serializer_class = DirectionSerializer
    permission_classes = [AllowAny]
    queryset = Direction.objects.all()



class ProjectListAPIView(generics.ListAPIView):
    serializer_class = ListProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all()


class ProjectDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DetailProjectSerializer
    permission_classes = [AllowAny]
    queryset = Project.objects.all()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectCreateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]



class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all()
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]



class TaskListAPIView(generics.ListAPIView):
    serializer_class = ListTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)


class TaskDetailAPIView(generics.RetrieveAPIView):
    serializer_class = DetailTaskSerializer
    permission_classes = [IsAuthenticated]
    queryset = Task.objects.all()


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]



class ActivityListAPIView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    queryset = Activity.objects.all().order_by('-created_at')



class SiteInfoView(generics.RetrieveAPIView):
    serializer_class = SiteInfoSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        return SiteInfo.objects.first()
