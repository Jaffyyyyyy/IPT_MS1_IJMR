import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import Post, Comment, User as CustomUser
from .serializers import UserSerializer, PostSerializer, CommentSerializer
from singletons.logger_singleton import LoggerSingleton
from singletons.config_manager import ConfigManager
from factories.post_factory import PostFactory

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
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email', '')
        
        if not username:
            logger.warning("User creation attempt without username")
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create custom user (posts.models.User)
            user = CustomUser.objects.create(username=username, email=email)
            logger.info(f"Custom user created via API: {user.username}")
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating custom user via API: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PostListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Post created via API by user: {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid post data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreate(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        comments = Comment.objects.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            logger.info(f"Comment created via API by user: {request.user.username}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        logger.warning(f"Invalid comment data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            logger.info(f"User {request.user.username} accessed post {pk}")
            return Response({"content": post.content})
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


class CreatePostView(APIView):
    """
    API View to create posts using the Factory Pattern.
    Supports authentication and uses PostFactory for standardized post creation.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            # Note: author is not set here because Post.author expects posts.User,
            # while request.user is django.contrib.auth.models.User
            
            post = PostFactory.create_post(
                post_type=data.get('post_type', 'text'),
                title=data['title'],
                content=data.get('content', ''),
                metadata=data.get('metadata', {}),
                author=None  # Set to None since author field is nullable
            )
            logger.info(f"Post created successfully using Factory by user {request.user.username}: Post ID {post.id}")
            return Response({
                'message': 'Post created successfully!',
                'post_id': post.id,
                'post_type': post.post_type,
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


