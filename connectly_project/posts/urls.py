from django.urls import path
from .views import (
    UserListCreate, PostListCreate, CommentListCreate, PostDetailView,
    CreatePostView, LikePostView, CommentOnPostView, PostCommentsView,
    AuthenticatedUserProfileView, NewsFeedView, AuthenticateUserView,
)

urlpatterns = [
    path('users/', UserListCreate.as_view(), name='user-list-create'),
    path('users/me/', AuthenticatedUserProfileView.as_view(), name='user-profile'),
    path('feed/', NewsFeedView.as_view(), name='news-feed'),
    path('', PostListCreate.as_view(), name='post-list-create'),
    path('create/', CreatePostView.as_view(), name='post-create-factory'),
    path('<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('<int:pk>/like/', LikePostView.as_view(), name='post-like'),
    path('<int:pk>/comment/', CommentOnPostView.as_view(), name='post-comment'),
    path('<int:pk>/comments/', PostCommentsView.as_view(), name='post-comments-list'),
    path('comments/', CommentListCreate.as_view(), name='comment-list-create'),
    path('authenticate/', AuthenticateUserView.as_view(), name='authenticate-user'),
]
