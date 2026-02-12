from django.urls import path
from .views import (
    UserListCreate, PostListCreate, PostDetailView,
    CommentListCreate, RegisterUser, LoginUser, ProtectedView,
    TaskListView, CreateTaskView, TaskDetailView,
    # New imports
    PostLikeToggle, PostCommentCreate, PostCommentList,
)


urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('posts/', PostListCreate.as_view(), name='post-list-create'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    # New URL patterns
    path('posts/<int:pk>/like/', PostLikeToggle.as_view(), name='post-like-toggle'),
    path('posts/<int:pk>/comment/', PostCommentCreate.as_view(), name='post-comment-create'),
    path('posts/<int:pk>/comments/', PostCommentList.as_view(), name='post-comment-list'),

    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('register/', RegisterUser.as_view(), name='register-user'),
    path('login/', LoginUser.as_view(), name='login-user'),
    path('protected/', ProtectedView.as_view(), name='protected-view'),
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/create/', CreateTaskView.as_view(), name='create-task'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]

