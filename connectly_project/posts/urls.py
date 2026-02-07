from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    UserListCreateView, PostListCreate, PostDetailView,
    CommentListCreate, RegisterUser, ProtectedView,
    CreatePostWithFactoryView # Added CreatePostWithFactoryView import
)


urlpatterns = [
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/create-with-factory/', CreatePostWithFactoryView.as_view(), name='post-create-factory'), # Added new URL
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('register/', RegisterUser.as_view(), name='register-user'),
    # JWT Authentication Endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('protected/', ProtectedView.as_view(), name='protected-view'),
]