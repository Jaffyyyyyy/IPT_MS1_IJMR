from django.urls import path
from .views import (
    UserListCreate, PostListCreate, PostDetailView,
    CommentListCreate, RegisterUser, LoginUser, ProtectedView,
)


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('register/', RegisterUser.as_view(), name='register-user'),
    path('login/', LoginUser.as_view(), name='login-user'),
    path('protected/', ProtectedView.as_view(), name='protected-view'),
]

