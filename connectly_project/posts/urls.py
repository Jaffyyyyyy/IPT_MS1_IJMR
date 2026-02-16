from django.urls import path
from . import views
from .views import UserListCreate, PostListCreate, CommentListCreate, PostDetailView, CreatePostView

urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('', PostListCreate.as_view(), name='post-list-create'),
    path('create/', CreatePostView.as_view(), name='post-create-factory'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('authenticate/', views.authenticate_user, name='authenticate-user'),
]
