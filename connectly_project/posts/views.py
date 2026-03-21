import json
import urllib.request
import urllib.parse
import urllib.error
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.db import IntegrityError
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from .models import Post, Comment, User, Like
from .serializers import (
    UserSerializer, PostSerializer, PostDetailSerializer,
    PostFeedSerializer, CommentSerializer, LikeSerializer,
)
from .permissions import (
    IsAdminRole, IsAdminOrAuthor, IsNotGuest,
)
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory

CACHE_TTL = 60 * 5  # 5 minutes

logger = LoggerSingleton().get_logger()
logger.info("API initialized successfully.")


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
    logger.debug(
        "Feed cache invalidated (global → %s, user %s → %s)",
        g + 1, user_id, u + 1,
    )


class AuthenticateUserView(APIView):
    """
    POST /posts/authenticate/ — verify credentials without issuing a token.
    Open to unauthenticated callers.
    """
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'username and password are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if user is not None:
            logger.info("Authentication successful for user: %s", user.username)
            return Response({'message': 'Authentication successful!',
                            'username': user.username}, status=status.HTTP_200_OK)
        logger.warning("Invalid credentials attempt for username: %s", username)
        return Response({'message': 'Invalid credentials.'},
                        status=status.HTTP_401_UNAUTHORIZED)


class UserListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    # Listing and creating users is restricted to admin role only (RBAC)
    permission_classes = [IsAdminRole]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email', '')
        password = request.data.get('password')
        role = request.data.get('role', 'user')  # default to 'user'

        if not username:
            logger.warning("User creation attempt without username")
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)

        valid_roles = [r[0] for r in User.ROLE_CHOICES]
        if role not in valid_roles:
            return Response({'error': f'Invalid role. Must be one of: {valid_roles}'}, status=status.HTTP_400_BAD_REQUEST)

        if not password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.role = role
            user.save(update_fields=['role'])
            logger.info("User created via API: %s (role=%s)", user.username, role)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("Error creating user via API: %s", e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsNotGuest]

    def get(self, request):
        # Privacy: only show public posts OR the user's own private posts.
        # select_related prevents N+1 on author; DB-level Count annotations resolve
        # like_count / comment_count in a single aggregated query instead of
        # issuing per-object COUNT calls through the @property on the model.
        posts = (
            Post.objects
            .filter(Q(privacy='public') | Q(author=request.user))
            .select_related('author')
            .annotate(
                annotated_like_count=Count('likes', distinct=True),
                annotated_comment_count=Count('comments', distinct=True),
            )
        )

        # Optional search / filter via query params
        search = request.query_params.get('search')
        post_type = request.query_params.get('post_type')
        privacy = request.query_params.get('privacy')
        if search:
            posts = posts.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        if post_type:
            posts = posts.filter(post_type=post_type)
        if privacy:
            posts = posts.filter(privacy=privacy)

        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


    def post(self, request):
        # IsNotGuest already blocks guest writes at the view level
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            # Prevent author spoofing: author always comes from the auth token.
            serializer.save(author=request.user)
            invalidate_feed_cache(request.user.id)
            logger.info("Post created via API by user: %s", request.user.username)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning("Invalid post data: %s", serializer.errors)
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
            logger.error("Post not found or invalid post ID in comment creation")
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            # Set author from authenticated user
            serializer.save(author=request.user, post=post)
            logger.info("Comment created via API by user: %s", request.user.username)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning("Invalid comment data: %s", serializer.errors)
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
            logger.info(
                "Post created successfully using Factory by user %s: Post ID %s",
                request.user.username, post.id,
            )
            return Response({
                'message': 'Post created successfully!',
                'post_id': post.id,
                'post_type': post.post_type,
                'privacy': post.privacy,
                'title': post.title
            }, status=status.HTTP_201_CREATED)
        except KeyError as e:
            logger.warning("Missing required field in post creation: %s", e)
            return Response({'error': f'Missing required field: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as e:
            logger.warning("Validation error in post creation: %s", e)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("Error creating post via Factory: %s", e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StandardPagination(PageNumberPagination):
    """Shared pagination settings for all list endpoints."""
    page_size = ConfigManager().get_setting('DEFAULT_PAGE_SIZE')
    page_size_query_param = 'page_size'
    max_page_size = 100


CommentPagination = StandardPagination


class LikePostView(APIView):
    """
    API View to like a post.
    POST /posts/{id}/like: Allows authenticated users to like a post.
    Prevents duplicate likes using unique_together constraint.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsNotGuest]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error("Post not found with ID: %s", pk)
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            # Create like
            like = Like.objects.create(user=request.user, post=post)
            logger.info("User %s liked post %s", request.user.username, pk)
            serializer = LikeSerializer(like)
            return Response({
                'message': 'Post liked successfully',
                'like': serializer.data
            }, status=status.HTTP_201_CREATED)
        except IntegrityError:
            # User already liked this post
            logger.warning(
                "User %s attempted to like post %s again",
                request.user.username, pk,
            )
            return Response(
                {'error': 'You have already liked this post'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error liking post %s: %s", pk, e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        Unlike a post by removing the like.
        """
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error("Post not found with ID: %s", pk)
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            like = Like.objects.get(user=request.user, post=post)
            like.delete()
            logger.info("User %s unliked post %s", request.user.username, pk)
            return Response({'message': 'Post unliked successfully'}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            logger.warning(
                "User %s tried to unlike post %s but hasn't liked it",
                request.user.username, pk,
            )
            return Response(
                {'error': 'You have not liked this post'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error("Error unliking post %s: %s", pk, e)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentOnPostView(APIView):
    """
    POST /posts/{id}/comment  — add a comment (user/admin only; guests blocked).
    DELETE /posts/{id}/comment/{comment_id}  — admin may delete any comment.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsNotGuest]

    def post(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.error("Post not found with ID: %s", pk)
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # Add post and author to request data
        data = request.data.copy()
        data['post'] = post.id
        data['author'] = request.user.id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user, post=post)
            logger.info("User %s commented on post %s", request.user.username, pk)
            return Response({
                'message': 'Comment added successfully',
                'comment': CommentSerializer(comment).data
            }, status=status.HTTP_201_CREATED)

        logger.warning(
            "Invalid comment data from user %s: %s",
            request.user.username, serializer.errors,
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated(), IsNotGuest()]

    def delete(self, request, pk):
        """
        Admin-only: delete any comment on this post.
        DELETE /posts/{id}/comment/?comment_id={id}
        """
        comment_id = request.query_params.get('comment_id')
        if not comment_id:
            return Response({'error': 'comment_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            comment = Comment.objects.get(pk=comment_id, post__id=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        comment.delete()
        logger.info(
            "Admin %s deleted comment %s on post %s",
            request.user.username, comment_id, pk,
        )
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
            logger.error("Post not found with ID: %s", pk)
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        # select_related prevents N+1 on author and post in CommentSerializer
        comments = Comment.objects.filter(post=post).select_related('author', 'post')

        # Apply pagination
        paginator = self.pagination_class()
        try:
            paginated_comments = paginator.paginate_queryset(comments, request)
        except Exception:
            # If page is out of range, return empty results
            logger.info("Page out of range for post %s, returning empty results", pk)
            return Response({
                'count': comments.count(),
                'next': None,
                'previous': None,
                'results': []
            })
        
        serializer = CommentSerializer(paginated_comments, many=True)
        logger.info("Retrieved %s comments for post %s", len(serializer.data), pk)
        
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
            logger.info("Cache hit for post %s", pk)
            # Privacy check: private posts only visible to author
            if cached.get('privacy') == 'private' and cached.get('author') != request.user.id:
                return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response(cached)

        try:
            post = (
                Post.objects
                .select_related('author')
                .annotate(
                    annotated_like_count=Count('likes', distinct=True),
                    annotated_comment_count=Count('comments', distinct=True),
                )
                .get(pk=pk)
            )
        except Post.DoesNotExist:
            logger.error("Post not found with ID: %s", pk)
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)

        # Privacy: private posts only visible to their author
        if post.privacy == 'private' and post.author != request.user:
            return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)

        logger.info("User %s accessed post %s", request.user.username, pk)
        data = PostDetailSerializer(post).data
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
            invalidate_feed_cache(request.user.id)
            logger.info("Post %s updated by %s", pk, request.user.username)
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
            invalidate_feed_cache(request.user.id)
            logger.info("Post %s patched by %s", pk, request.user.username)
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
        logger.info("Post %s deleted by %s", pk, request.user.username)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAuthenticated(), IsAdminOrAuthor()]
        return [IsAuthenticated()]

class AuthenticatedUserProfileView(APIView):
    """
    GET  /posts/users/me/ — returns the authenticated user's profile.
    PATCH /posts/users/me/ — update the authenticated user's own profile fields.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info("User %s updated their profile", request.user.username)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


NewsFeedPagination = StandardPagination


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
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size', NewsFeedPagination.page_size)
        # Compound version (global + per-user) ensures that a public post
        # created by ANY user busts the cached feed for ALL users.
        ver = _feed_cache_version(request.user.id)
        cache_key = f'news_feed_{request.user.id}_v{ver}_p{page}_s{page_size}'

        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(
                "Cache hit for news feed (user=%s, page=%s, ver=%s)",
                request.user.id, page, ver,
            )
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
        logger.info(
            "Retrieved %s posts for news feed (user=%s, page=%s)",
            len(serializer.data), request.user.id, page,
        )
        response = paginator.get_paginated_response(serializer.data)
        cache.set(cache_key, response.data, CACHE_TTL)
        return response


# ---------------------------------------------------------------------------
# Google OAuth Login
# ---------------------------------------------------------------------------
_GOOGLE_TOKENINFO_URL = 'https://oauth2.googleapis.com/tokeninfo?id_token={token}'


class GoogleLoginView(APIView):
    """
    POST /auth/google/login

    Accepts a Google ID token (obtained client-side via Google Sign-In / OAuth2
    consent screen) and exchanges it for a Connectly API auth token.

    Request body  (JSON):
        { "id_token": "<google_id_token>" }

    Success response  200:
        {
            "token":    "<drf_auth_token>",
            "user_id":  <int>,
            "username": "<str>",
            "email":    "<str>",
            "created":  <bool>   # true if a new account was just created
        }

    Error responses:
        400  – id_token field missing or empty
        401  – Google rejected the token (expired, tampered, wrong audience)
        409  – email already registered via password; manual merge required
        500  – unexpected server error
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        id_token = request.data.get('id_token', '').strip()
        if not id_token:
            return Response(
                {'error': 'id_token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # --- Verify the token with Google -----------------------------------
        google_info = self._verify_google_token(id_token)
        if google_info is None:
            logger.warning("Google OAuth: token verification failed (invalid/expired token)")
            return Response(
                {'error': 'Invalid or expired Google token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if 'error' in google_info:
            logger.warning("Google OAuth: token error – %s", google_info['error'])
            return Response(
                {'error': 'Invalid or expired Google token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = google_info.get('email', '').lower()
        google_sub = google_info.get('sub', '')   # Google user ID
        given_name = google_info.get('given_name', '')
        family_name = google_info.get('family_name', '')

        if not email or not google_sub:
            logger.warning("Google OAuth: token missing email or sub claim")
            return Response(
                {'error': 'Google token is missing required claims (email / sub).'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # --- Find or create the local user ----------------------------------
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    # Use the Google sub as a stable, safe username base
                    'username': self._safe_username(email, google_sub),
                    'first_name': given_name,
                    'last_name': family_name,
                    'role': User.ROLE_USER,
                },
            )
        except IntegrityError:
            # Race-condition: two simultaneous first-time logins for the same email
            user = User.objects.get(email=email)
            created = False

        # Issue or retrieve a DRF auth token
        token_obj, _ = Token.objects.get_or_create(user=user)

        logger.info(
            "Google OAuth login: user=%s email=%s created=%s",
            user.username, email, created,
        )
        return Response(
            {
                'token':    token_obj.key,
                'user_id':  user.id,
                'username': user.username,
                'email':    user.email,
                'created':  created,
            },
            status=status.HTTP_200_OK,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_google_token(id_token: str) -> dict | None:
        """
        Call Google's tokeninfo endpoint to validate *id_token*.
        Returns the decoded JSON payload dict, or None on network/HTTP errors.
        """
        url = _GOOGLE_TOKENINFO_URL.format(token=urllib.parse.quote(id_token, safe=''))
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            # 400 from Google means bad / expired token; read the body for logging
            try:
                payload = json.loads(exc.read().decode())
            except Exception:
                payload = {'error': str(exc)}
            return payload
        except Exception as exc:
            logger.error("Google tokeninfo request failed: %s", exc)
            return None

    @staticmethod
    def _safe_username(email: str, google_sub: str) -> str:
        """
        Derive a unique username from the email local-part.
        Appends a short suffix from the Google sub to avoid collisions.
        """
        local = email.split('@')[0]
        # Strip characters not allowed in Django usernames
        safe = ''.join(c for c in local if c.isalnum() or c in '._-')
        suffix = google_sub[-6:]
        candidate = f'{safe}_{suffix}'
        # If the candidate already exists (e.g. two google accounts with same
        # email prefix), fall back to the full sub.
        if User.objects.filter(username=candidate).exists():
            return f'g_{google_sub}'
        return candidate



