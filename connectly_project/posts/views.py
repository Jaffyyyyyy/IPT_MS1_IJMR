import json
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Post, Comment, User, Like
from .serializers import UserSerializer, PostSerializer, PostFeedSerializer, CommentSerializer, LikeSerializer
from .permissions import (
    IsPostAuthor, IsAdminOrReadOnly, IsStaffUser,
    IsAdminRole, IsAdminOrAuthor, IsNotGuest,
)
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory

CACHE_TTL = 60 * 5  # 5 minutes


# ---------------------------------------------------------------------------
# Cache-invalidation helpers for the news feed
# ---------------------------------------------------------------------------
_GLOBAL_FEED_VER_KEY = 'global_feed_ver'


def _feed_cache_version(user_id: int) -> str:
    """
    Return a compound version token for *user_id* that combines:
    - A global counter incremented on every public-post write (busts ALL users)
    - A per-user counter for private-post writes (busts only that user)
    """
    g = cache.get(_GLOBAL_FEED_VER_KEY, 0)
    u = cache.get(f'feed_ver_{user_id}', 0)
    return f'{g}_{u}'


def invalidate_feed_cache(user_id: int) -> None:
    """
    Bump both the global feed version and the per-user version so that
    previously cached pages are superseded for ALL users on the next request.
    Using a global key means that when user A creates a public post, user B's
    cached feed is also invalidated automatically.
    """
    g = cache.get(_GLOBAL_FEED_VER_KEY, 0)
    cache.set(_GLOBAL_FEED_VER_KEY, g + 1, CACHE_TTL * 288)  # 24 h
    u_key = f'feed_ver_{user_id}'
    u = cache.get(u_key, 0)
    cache.set(u_key, u + 1, CACHE_TTL * 288)
    logger.debug(f"Feed cache invalidated (global → {g + 1}, user {user_id} → {u + 1})")


logger = LoggerSingleton().get_logger()
logger.info("API initialized successfully.")

def get_users(request):
    try:
        users = list(User.objects.values('id', 'username', 'email', 'created_at'))
        logger.info(f"Retrieved {len(users)} users")
        return JsonResponse(users, safe=False)
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def create_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = User.objects.create_user(username=data['username'], password=data.get('password', 'secure_pass123'), email=data.get('email', ''))
            logger.info(f"User created successfully: {user.username}")
            return JsonResponse({'id': user.id, 'username': user.username, 'message': 'User created successfully'}, status=201)
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def authenticate_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = authenticate(username=data['username'], password=data['password'])
            if user is not None:
                logger.info(f"Authentication successful for user: {user.username}")
                return JsonResponse({'message': 'Authentication successful!', 'username': user.username}, status=200)
            else:
                logger.warning(f"Invalid credentials attempt for username: {data.get('username', 'unknown')}")
                return JsonResponse({'message': 'Invalid credentials.'}, status=401)
        except Exception as e:
            logger.error(f"Error during authentication: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

def get_posts(request):
    try:
        posts = list(Post.objects.values('id', 'content', 'author', 'created_at'))
        logger.info(f"Retrieved {len(posts)} posts")
        return JsonResponse(posts, safe=False)
    except Exception as e:
        logger.error(f"Error retrieving posts: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def create_post(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            author = User.objects.get(id=data['author'])
            post = Post.objects.create(content=data['content'], author=author)
            logger.info(f"Post created successfully by user {author.username}: Post ID {post.id}")
            return JsonResponse({'id': post.id, 'message': 'Post created successfully'}, status=201)
        except User.DoesNotExist:
            logger.error(f"Author not found with ID: {data.get('author', 'unknown')}")
            return JsonResponse({'error': 'Author not found'}, status=404)
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)


class UserListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    # Listing and creating users is restricted to staff only (RBAC)
    permission_classes = [IsStaffUser]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email', '')
        password = request.data.get('password', 'secure_pass123')
        role = request.data.get('role', 'user')  # default to 'user'

        if not username:
            logger.warning("User creation attempt without username")
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if role not in valid_roles:
            return Response({'error': f'Invalid role. Must be one of: {valid_roles}'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.role = role
            user.save(update_fields=['role'])
            logger.info(f"User created via API: {user.username} (role={role})")
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating user via API: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsNotGuest]

    def get(self, request):
        # Privacy: only show public posts OR the user's own private posts.
        # select_related prevents N+1 on author; prefetch_related on likes/comments
        # avoids extra queries when rendering like_count / comment_count.
        from django.db.models import Q
        posts = (
            Post.objects
            .filter(Q(privacy='public') | Q(author=request.user))
            .select_related('author')
            .prefetch_related('likes', 'comments')
        )
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


    def post(self, request):
        # IsNotGuest already blocks guest writes at the view level
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            invalidate_feed_cache(request.user.id)
            logger.info(f"Post created via API by user: {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid post data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # select_related prevents N+1 on author and post lookups in the serializer
        comments = Comment.objects.select_related('author', 'post').all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


    def post(self, request):
        # Get the post from request data
        try:
            post_id = request.data.get('post')
            post = Post.objects.get(pk=post_id)
        except (Post.DoesNotExist, TypeError):
            logger.error(f"Post not found or invalid post ID in comment creation")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            # Set author from authenticated user
            serializer.save(author=request.user, post=post)
            logger.info(f"Comment created via API by user: {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid comment data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePostView(APIView):
    """
    API View to create posts using the Factory Pattern.
    Supports authentication and uses PostFactory for standardized post creation.
    Guests are not permitted to create posts.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsNotGuest]

    def post(self, request):
        data = request.data
        try:
            # Now author can be set properly since we use a single custom User model
            # invalidate before building the response so callers always get fresh feed
            invalidate_feed_cache(request.user.id)
            post = PostFactory.create_post(
                post_type=data.get('post_type', 'text'),
                title=data['title'],
                content=data.get('content', ''),
                metadata=data.get('metadata', {}),
                author=request.user,
                privacy=data.get('privacy', 'public')
            )
            logger.info(f"Post created successfully using Factory by user {request.user.username}: Post ID {post.id}")
            return Response({
                'message': 'Post created successfully!',
                'post_id': post.id,
                'post_type': post.post_type,
                'privacy': post.privacy,
                'title': post.title
            }, status=status.HTTP_201_CREATED)
        except KeyError as e:
            logger.warning(f"Missing required field in post creation: {str(e)}")
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.warning(f"Validation error in post creation: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating post via Factory: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentPagination(PageNumberPagination):
    """Custom pagination class for comments"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LikePostView(APIView):
    """
    API View to like a post.
    POST /posts/{id}/like: Allows authenticated users to like a post.
    Prevents duplicate likes using unique_together constraint.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create like
            like = Like.objects.create(user=request.user, post=post)
            logger.info(f"User {request.user.username} liked post {pk}")
            serializer = LikeSerializer(like)
            return Response({
                'message': 'Post liked successfully',
                'like': serializer.data
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            # User already liked this post
            logger.warning(f"User {request.user.username} attempted to like post {pk} again")
            return Response(
                {'error': 'You have already liked this post'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error liking post {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        Unlike a post by removing the like.
        """
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            logger.info(f"User {request.user.username} unliked post {pk}")
            return Response({'message': 'Post unliked successfully'}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            logger.warning(f"User {request.user.username} tried to unlike post {pk} but hasn't liked it")
            return Response(
                {'error': 'You have not liked this post'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error unliking post {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentOnPostView(APIView):
    """
    POST /posts/{id}/comment  — add a comment (user/admin only; guests blocked).
    DELETE /posts/{id}/comment/{comment_id}  — admin may delete any comment.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        # Guests cannot write comments
        if request.user.role == 'guest':
            return Response(
                {'error': 'Guest users do not have write access.'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Add post and author to request data
        data = request.data.copy()
        data['post'] = post.id
        data['author'] = request.user.id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user, post=post)
            logger.info(f"User {request.user.username} commented on post {pk}")
            return Response({
                'message': 'Comment added successfully',
                'comment': CommentSerializer(comment).data
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"Invalid comment data from user {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Admin-only: delete any comment on this post.
        DELETE /posts/{id}/comment/?comment_id={id}
        """
        if request.user.role != 'admin':
            return Response(
                {'error': 'Only admin users can delete comments.'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment_id = request.query_params.get('comment_id')
        if not comment_id:
            return Response({'error': 'comment_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            comment = Comment.objects.get(pk=comment_id, post__id=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        comment.delete()
        logger.info(f"Admin {request.user.username} deleted comment {comment_id} on post {pk}")
        return Response({'message': 'Comment deleted successfully.'}, status=status.HTTP_200_OK)


class PostCommentsView(APIView):
    """
    API View to retrieve all comments for a specific post.
    GET /posts/{id}/comments: Returns paginated comments for the post.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = CommentPagination

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # select_related prevents N+1 on author and post in CommentSerializer
        comments = Comment.objects.filter(post=post).select_related('author', 'post')

        # Apply pagination
        paginator = self.pagination_class()
        try:
            paginated_comments = paginator.paginate_queryset(comments, request)
        except Exception:
            # If page is out of range, return empty results
            logger.info(f"Page out of range for post {pk}, returning empty results")
            return Response({
                'count': comments.count(),
                'next': None,
                'previous': None,
                'results': []
            })
        
        serializer = CommentSerializer(paginated_comments, many=True)
        logger.info(f"Retrieved {len(serializer.data)} comments for post {pk}")
        
        return paginator.get_paginated_response(serializer.data)


class PostDetailView(APIView):
    """
    Enhanced Post Detail View with like_count and comment_count.
    GET: cached, respects privacy.
    PUT/PATCH: author-only (RBAC via IsPostAuthor).
    DELETE: author-only (RBAC via IsPostAuthor).
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Check cache first
        cache_key = f'post_detail_{pk}'
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for post {pk}")
            # Privacy check: private posts only visible to author
            if cached.get('privacy') == 'private' and cached.get('author') != request.user.id:
                return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response(cached)

        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # Privacy: private posts only visible to their author
        if post.privacy == 'private' and post.author != request.user:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        logger.info(f"User {request.user.username} accessed post {pk}")
        data = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'post_type': post.post_type,
            'privacy': post.privacy,
            'metadata': post.metadata,
            'author': post.author.id if post.author else None,
            'author_username': post.author.username if post.author else None,
            'created_at': str(post.created_at),
            'like_count': post.like_count,
            'comment_count': post.comment_count
        }
        cache.set(cache_key, data, CACHE_TTL)
        return Response(data)

    def put(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # RBAC: only the author may update
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            cache.delete(f'post_detail_{pk}')
            logger.info(f"Post {pk} updated by {request.user.username}")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # RBAC: only the author may update
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            cache.delete(f'post_detail_{pk}')
            logger.info(f"Post {pk} patched by {request.user.username}")
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # RBAC: only the author may delete
        self.check_object_permissions(request, post)
        post.delete()
        cache.delete(f'post_detail_{pk}')
        invalidate_feed_cache(request.user.id)
        logger.info(f"Post {pk} deleted by {request.user.username}")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), IsAdminOrAuthor()]
        return [IsAuthenticated()]

class AuthenticatedUserProfileView(APIView):
    """
    GET /posts/users/me/  — returns the authenticated user's profile including their role.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class NewsFeedPagination(PageNumberPagination):
    """Custom pagination for the news feed"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class NewsFeedView(APIView):
    """
    API View to retrieve a paginated list of posts for the news feed.
    Only shows public posts + the authenticated user's own private posts.
    Posts are sorted by creation date (newest first).
    Results are cached per-user.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = NewsFeedPagination

    def get(self, request):
        from django.db.models import Q, Count

        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', NewsFeedPagination.page_size)
        # Compound version (global + per-user) ensures that a public post
        # created by ANY user busts the cached feed for ALL users.
        ver = _feed_cache_version(request.user.id)
        cache_key = f'news_feed_{request.user.id}_v{ver}_p{page}_s{page_size}'

        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for news feed (user={request.user.id}, page={page}, ver={ver})")
            return Response(cached)

        # Privacy: public posts + own private posts.
        # select_related('author') prevents one query per post for the author name.
        # DB-level Count annotations replace the Python-side model properties so
        # like_count / comment_count are resolved in a single aggregated query.
        posts = (
            Post.objects
            .filter(Q(privacy='public') | Q(author=request.user))
            .select_related('author')
            .annotate(
                annotated_like_count=Count('likes', distinct=True),
                annotated_comment_count=Count('comments', distinct=True),
            )
            .order_by('-created_at')
        )

        paginator = self.pagination_class()
        try:
            paginated_posts = paginator.paginate_queryset(posts, request)
        except Exception:
            logger.info("Page out of range for news feed, returning empty results")
            return Response({
                'count': posts.count(),
                'next': None,
                'previous': None,
                'results': []
            })

        # PostFeedSerializer omits the nested comments list — only counts are served,
        # which avoids serialising potentially hundreds of comments per post.
        serializer = PostFeedSerializer(paginated_posts, many=True)
        logger.info(f"Retrieved {len(serializer.data)} posts for news feed (user={request.user.id}, page={page})")
        response = paginator.get_paginated_response(serializer.data)
        cache.set(cache_key, response.data, CACHE_TTL)
        return response



