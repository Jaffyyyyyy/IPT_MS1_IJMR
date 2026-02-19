import json
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
from .serializers import UserSerializer, PostSerializer, CommentSerializer, LikeSerializer
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
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email', '')
        password = request.data.get('password', 'secure_pass123')
        
        if not username:
            logger.warning("User creation attempt without username")
            return Response({'error': 'Username is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create user with password hashing
            user = User.objects.create_user(username=username, email=email, password=password)
            logger.info(f"User created via API: {user.username}")
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating user via API: {str(e)}")
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
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            # Now author can be set properly since we use a single custom User model
            post = PostFactory.create_post(
                post_type=data.get('post_type', 'text'),
                title=data['title'],
                content=data.get('content', ''),
                metadata=data.get('metadata', {}),
                author=request.user
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
    API View to comment on a post.
    POST /posts/{id}/comment: Allows authenticated users to add a comment to a post.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
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

        comments = Comment.objects.filter(post=post)
        
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
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
            logger.info(f"User {request.user.username} accessed post {pk}")
            
            # Return detailed post information with counts
            return Response({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'post_type': post.post_type,
                'metadata': post.metadata,
                'author': post.author.id,
                'author_username': post.author.username if post.author else None,
                'created_at': post.created_at,
                'like_count': post.like_count,
                'comment_count': post.comment_count
            })
        except Post.DoesNotExist:
            logger.error(f"Post not found with ID: {pk}")
            return Response({"error": "Post not found"}, status=status.HTTP_404_NOT_FOUND)


