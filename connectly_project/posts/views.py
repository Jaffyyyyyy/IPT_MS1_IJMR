from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib.auth import authenticate
from .models import User, Post, Comment, Task, Like
from .serializers import UserSerializer, PostSerializer, CommentSerializer, TaskSerializer, LikeSerializer
from .permissions import IsPostAuthor
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from rest_framework.pagination import PageNumberPagination
from factories.task_factory import TaskFactory

# Initialize logger singleton
logger = LoggerSingleton().get_logger()
# Initialize config manager singleton
config = ConfigManager()


class CommentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all users")
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        logger.info("Creating new user")
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User created successfully: {serializer.data.get('username')}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"User creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterUser(APIView):
    """Register a new user with encrypted password using Django's create_user."""
    def post(self, request):
        logger.info("User registration attempt")
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            logger.warning("Registration failed: missing username or password")
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if AuthUser.objects.filter(username=username).exists():
            logger.warning(f"Registration failed: username '{username}' already exists")
            return Response(
                {'error': 'Username already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = AuthUser.objects.create_user(
            username=username, password=password, email=email
        )
        logger.info(f"User registered successfully: {username}")
        return Response(
            {'message': 'User registered successfully.', 'username': user.username},
            status=status.HTTP_201_CREATED
        )


class LoginUser(APIView):
    """Authenticate a user and verify credentials."""
    def post(self, request):
        logger.info("Login attempt")
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            logger.warning("Login failed: missing credentials")
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if user is not None:
            logger.info(f"User logged in successfully: {username}")
            return Response(
                {'message': 'Authentication successful!', 'username': user.username},
                status=status.HTTP_200_OK
            )
        logger.warning(f"Login failed for user: {username}")
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class PostListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all posts")
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


    def post(self, request):
        logger.info("Creating new post")
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Post created successfully")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Post creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    """Retrieve a post with role-based access control."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsPostAuthor]


    def get(self, request, pk):
        logger.info(f"Fetching post with id: {pk}")
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Post not found: {pk}")
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        self.check_object_permissions(request, post)
        return Response({"content": post.content})


class PostLikeToggle(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        logger.info(f"User {request.user.username} attempting to like post {pk}")
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Like failed: Post {pk} not found.")
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            liking_user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            logger.error(f"Internal user model not found for authenticated user {request.user.username}")
            return Response(
                {'error': 'Internal server error: User not found.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        like, created = Like.objects.get_or_create(user=liking_user, post=post)

        if created:
            logger.info(f"User {request.user.username} liked post {pk}.")
            return Response(
                {'message': 'Post liked successfully.'},
                status=status.HTTP_201_CREATED
            )
        else:
            like.delete()
            logger.info(f"User {request.user.username} unliked post {pk}.")
            return Response(
                {'message': 'Post unliked successfully.'},
                status=status.HTTP_200_OK
            )


class PostCommentCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        logger.info(f"User {request.user.username} attempting to comment on post {pk}")
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Comment failed: Post {pk} not found.")
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            commenting_user = User.objects.get(username=request.user.username)
        except User.DoesNotExist:
            logger.error(f"Internal user model not found for authenticated user {request.user.username}")
            return Response(
                {'error': 'Internal server error: User not found.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        data = request.data.copy()
        data['post'] = post.id
        data['author'] = commenting_user.id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.username} commented on post {pk}.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Comment creation failed for post {pk}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostCommentList(APIView):
    pagination_class = CommentPagination # Assign the pagination class

    def get(self, request, pk):
        logger.info(f"Fetching comments for post {pk}")
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            logger.warning(f"Fetching comments failed: Post {pk} not found.")
            return Response(
                {'error': 'Post not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        comments = Comment.objects.filter(post=post).order_by('-created_at')

        # Apply pagination
        paginator = self.pagination_class()
        paginated_comments = paginator.paginate_queryset(comments, request, view=self)
        
        serializer = CommentSerializer(paginated_comments, many=True)
        return paginator.get_paginated_response(serializer.data) # Return paginated response


class ProtectedView(APIView):
    """A protected endpoint that requires token authentication."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


    def get(self, request):
        logger.info(f"Protected view accessed by: {request.user.username}")
        return Response({"message": "Authenticated!"})


class CommentListCreate(APIView):
    def get(self, request):
        logger.info("Fetching all comments")
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


    def post(self, request):
        logger.info("Creating new comment")
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info("Comment created successfully")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Comment creation failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskListView(APIView):
    """List all tasks or retrieve tasks by type."""
    
    def get(self, request):
        logger.info("Fetching all tasks")
        task_type = request.query_params.get('type', None)
        
        if task_type:
            tasks = Task.objects.filter(task_type=task_type)
            logger.info(f"Filtering tasks by type: {task_type}")
        else:
            tasks = Task.objects.all()
        
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)


class CreateTaskView(APIView):
    """Create tasks using the Factory pattern."""
    
    def post(self, request):
        logger.info("Creating new task via factory")
        data = request.data
        
        try:
            # Get the assigned user
            assigned_to_id = data.get('assigned_to')
            try:
                assigned_to = User.objects.get(pk=assigned_to_id)
            except User.DoesNotExist:
                logger.warning(f"Task creation failed: user {assigned_to_id} not found")
                return Response(
                    {'error': 'Assigned user not found.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use factory to create task
            task = TaskFactory.create_task(
                task_type=data.get('task_type', 'regular'),
                title=data.get('title'),
                description=data.get('description', ''),
                assigned_to=assigned_to,
                metadata=data.get('metadata', {})
            )
            
            # Get default priority from config if not specified
            default_priority = config.get_setting("DEFAULT_TASK_PRIORITY")
            logger.info(f"Task created successfully: {task.title} (ID: {task.id})")
            
            return Response({
                'message': 'Task created successfully!',
                'task_id': task.id,
                'task_type': task.task_type,
                'default_priority': default_priority
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            logger.warning(f"Task creation failed: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error during task creation: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskDetailView(APIView):
    """Retrieve, update, or delete a specific task."""
    
    def get(self, request, pk):
        logger.info(f"Fetching task with id: {pk}")
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            logger.warning(f"Task not found: {pk}")
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    
    def put(self, request, pk):
        logger.info(f"Updating task with id: {pk}")
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            logger.warning(f"Task not found for update: {pk}")
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Task updated successfully: {pk}")
            return Response(serializer.data)
        logger.warning(f"Task update failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        logger.info(f"Deleting task with id: {pk}")
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            logger.warning(f"Task not found for deletion: {pk}")
            return Response(
                {'error': 'Task not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        task.delete()
        logger.info(f"Task deleted successfully: {pk}")
        return Response(
            {'message': 'Task deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


