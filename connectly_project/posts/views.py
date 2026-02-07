from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions, status
from rest_framework_simplejwt.authentication import JWTAuthentication # Use JWT Authentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group # Group might be used for RBAC, keeping for completeness
from django.contrib.auth import authenticate # Needed for custom Register/Login if not using TokenObtainPairView for /login/
from django.shortcuts import get_object_or_404 # For robust error handling

from .models import User, Post, Comment
from .serializers import UserSerializer, PostSerializer, CommentSerializer
from .permissions import IsPostAuthor # Custom permission for post ownership

from singletons.logger_singleton import LoggerSingleton # Singleton Logger
from factories.post_factory import PostFactory # Factory Pattern for Post creation

# Initialize logger singleton
logger = LoggerSingleton().get_logger()


# --- User Management Views ---
class RegisterUser(APIView):
    """
    Register a new user with encrypted password using custom User model.
    No authentication required for registration.
    """
    permission_classes = [permissions.AllowAny] # Allow unauthenticated access

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            logger.warning("Registration attempt failed: Username or password missing.")
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            logger.warning(f"Registration attempt failed: Username '{username}' already exists.")
            return Response(
                {'error': 'Username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.create_user(
                username=username, password=password, email=email
            )
            logger.info(f"User '{username}' registered successfully.")
            return Response(
                {'message': 'User registered successfully.', 'username': user.username},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error during user registration for '{username}': {e}", exc_info=True)
            return Response(
                {'error': f"An unexpected error occurred during registration: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserListCreateView(generics.ListCreateAPIView):
    """
    API view for listing and creating users.
    Only authenticated users can create. Read-only for others.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication] # Explicitly use JWT


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, or deleting a specific user.
    Only authenticated users can update/delete. Read-only for others.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication] # Explicitly use JWT
    # Further custom permission (e.g., IsOwnerOrAdmin) would be needed to
    # restrict users to only edit their own profile or allow admins.


# --- Post Management Views ---
class PostListCreate(APIView):
    """
    API view for listing all posts or creating a new post.
    Authenticated users can create posts.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] # Allow anyone to read, only authenticated to create
    authentication_classes = [JWTAuthentication] # Explicitly use JWT

    def get(self, request):
        logger.info(f"Retrieving all posts. User: {request.user.username if request.user.is_authenticated else 'anonymous'}")
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

    def post(self, request):
        logger.info(f"Post creation attempt by user: {request.user.username if request.user.is_authenticated else 'anonymous'}")
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            # Assign author here directly from the authenticated user
            serializer.save(author=request.user)
            logger.info(f"Post created successfully by {request.user.username}: {serializer.data.get('title')}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Post creation failed for user {request.user.username if request.user.is_authenticated else 'anonymous'}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """
    Retrieve, update or delete a post with role-based access control and ownership check.
    Uses IsPostAuthor custom permission.
    """
    permission_classes = [IsAuthenticated, IsPostAuthor] # Authenticated and must be author
    authentication_classes = [JWTAuthentication] # Explicitly use JWT

    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        logger.info(f"Retrieving post ID {pk}. User: {request.user.username if request.user.is_authenticated else 'anonymous'}")
        # Check object-level permissions
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    def put(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        logger.info(f"Attempting to update post ID {pk}. User: {request.user.username}")
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post ID {pk} updated successfully by {request.user.username}.")
            return Response(serializer.data)
        logger.warning(f"Update failed for post ID {pk} by {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        logger.info(f"Attempting to partially update post ID {pk}. User: {request.user.username}")
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data, partial=True) # partial=True for PATCH
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post ID {pk} partially updated successfully by {request.user.username}.")
            return Response(serializer.data)
        logger.warning(f"Partial update failed for post ID {pk} by {request.user.username}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        logger.info(f"Attempting to delete post ID {pk}. User: {request.user.username}")
        self.check_object_permissions(request, post)
        post.delete()
        logger.info(f"Post ID {pk} deleted successfully by {request.user.username}.")
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Factory Pattern Integration View ---
class CreatePostWithFactoryView(APIView):
    """
    API view to create a post using the PostFactory pattern.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated] # Requires authentication to create posts
    authentication_classes = [JWTAuthentication] # Explicitly use JWT

    def post(self, request):
        data = request.data
        logger.info(f"Factory post creation attempt by user: {request.user.username}")
        try:
            post = PostFactory.create_post(
                post_type=data.get('post_type'),
                title=data.get('title'),
                content=data.get('content', ''),
                metadata=data.get('metadata', {}),
                author=request.user # Assign the authenticated user as author
            )
            logger.info(f"Factory post created successfully with ID: {post.id} by {request.user.username}")
            return Response(
                {'message': 'Post created successfully using Factory!', 'post_id': post.id},
                status=status.HTTP_201_CREATED
            )
        except ValueError as e:
            logger.warning(f"Factory post creation failed for {request.user.username}: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during factory post creation for {request.user.username}: {e}", exc_info=True)
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Comment Management Views ---
class CommentListCreate(generics.ListCreateAPIView):
    """
    API view for listing all comments or creating a new comment.
    Authenticated users can create comments.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    authentication_classes = [JWTAuthentication] # Explicitly use JWT

    def perform_create(self, serializer):
        # Optionally, you might want to link the comment to the authenticated user
        # serializer.save(author=self.request.user)
        logger.info(f"Comment created by {self.request.user.username if self.request.user.is_authenticated else 'anonymous'}")
        serializer.save() # Saves without specific author from request for now


# --- Simple Protected View ---
class ProtectedView(APIView):
    """
    A protected endpoint that requires JWT authentication.
    Returns a simple message upon successful authentication.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication] # Explicitly use JWT

    def get(self, request):
        logger.info(f"Accessed Protected View. User: {request.user.username}")
        return Response({"message": f"Hello {request.user.username}, you are authenticated with JWT!"})