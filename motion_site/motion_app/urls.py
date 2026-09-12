from django.urls import include, path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (ActivityListAPIView, CustomLoginView,DetailUserProfileAPIView,
                    DirectionListAPIView, LogoutView,MyPermissionsView, MyPortfolioView,
                    MyProfileView, ProjectDetailAPIView, ProjectListAPIView,
                    ProjectMemberViewSet, ProjectViewSet, RegisterView, ReviewViewSet, SiteInfoView,
                    TaskDetailAPIView, TaskListAPIView, TaskViewSet, TeamMemberViewSet, TeamViewSet,
                    UserPortfolioView, UserProfileListAPIView)


router = routers.SimpleRouter()

router.register(r'projects_manage', ProjectViewSet, basename='projects_manage')
router.register(r'project_members', ProjectMemberViewSet, basename='project_members')
router.register(r'tasks_manage', TaskViewSet, basename='tasks_manage')
router.register(r'teams', TeamViewSet, basename='teams')
router.register(r'team_members', TeamMemberViewSet, basename='team_members')
router.register(r'reviews', ReviewViewSet, basename='reviews')


urlpatterns = [
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('profile/', MyProfileView.as_view(), name='my_profile'),
    path('portfolio/', MyPortfolioView.as_view(), name='my_portfolio'),
    path('permissions/', MyPermissionsView.as_view(), name='my_permissions'),

    path('team/', UserProfileListAPIView.as_view(), name='team_list'),
    path('team/<int:pk>/', DetailUserProfileAPIView.as_view(), name='team_detail'),
    path('team/<int:pk>/portfolio/', UserPortfolioView.as_view(), name='user_portfolio'),

    path('directions/', DirectionListAPIView.as_view(), name='direction_list'),

    path('site-info/', SiteInfoView.as_view(), name='site_info'),

    path('projects/', ProjectListAPIView.as_view(), name='project_list'),
    path('projects/<int:pk>/', ProjectDetailAPIView.as_view(), name='project_detail'),

    path('tasks/', TaskListAPIView.as_view(), name='task_list'),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view(), name='task_detail'),

    path('activity/', ActivityListAPIView.as_view(), name='activity_list'),

    path('', include(router.urls)),
]