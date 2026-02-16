from django.test import TestCase
from django.contrib.auth.models import User as DjangoUser
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Post, User
from factories.post_factory import PostFactory


class PostFactoryTestCase(TestCase):
    """Test cases for the PostFactory class"""
    
    def setUp(self):
        """Set up test user"""
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com'
        )
    
    def test_create_text_post(self):
        """Test creating a text post"""
        post = PostFactory.create_post(
            post_type='text',
            title='Test Text Post',
            content='This is a test text post',
            author=self.user
        )
        self.assertEqual(post.post_type, 'text')
        self.assertEqual(post.title, 'Test Text Post')
        self.assertEqual(post.content, 'This is a test text post')
        self.assertEqual(post.author, self.user)
        self.assertIsNotNone(post.id)
    
    def test_create_image_post_with_metadata(self):
        """Test creating an image post with required metadata"""
        post = PostFactory.create_post(
            post_type='image',
            title='Test Image Post',
            content='Image description',
            metadata={'file_size': 1024000, 'dimensions': '1920x1080'},
            author=self.user
        )
        self.assertEqual(post.post_type, 'image')
        self.assertEqual(post.metadata['file_size'], 1024000)
        self.assertEqual(post.metadata['dimensions'], '1920x1080')
    
    def test_create_image_post_without_file_size_fails(self):
        """Test that creating an image post without file_size raises ValueError"""
        with self.assertRaises(ValueError) as context:
            PostFactory.create_post(
                post_type='image',
                title='Invalid Image Post',
                content='Missing file_size',
                metadata={},
                author=self.user
            )
        self.assertIn('file_size', str(context.exception))
    
    def test_create_video_post_with_metadata(self):
        """Test creating a video post with required metadata"""
        post = PostFactory.create_post(
            post_type='video',
            title='Test Video Post',
            content='Video description',
            metadata={'duration': 120, 'resolution': '1080p'},
            author=self.user
        )
        self.assertEqual(post.post_type, 'video')
        self.assertEqual(post.metadata['duration'], 120)
        self.assertEqual(post.metadata['resolution'], '1080p')
    
    def test_create_video_post_without_duration_fails(self):
        """Test that creating a video post without duration raises ValueError"""
        with self.assertRaises(ValueError) as context:
            PostFactory.create_post(
                post_type='video',
                title='Invalid Video Post',
                content='Missing duration',
                metadata={},
                author=self.user
            )
        self.assertIn('duration', str(context.exception))
    
    def test_invalid_post_type_fails(self):
        """Test that creating a post with invalid type raises ValueError"""
        with self.assertRaises(ValueError) as context:
            PostFactory.create_post(
                post_type='invalid_type',
                title='Invalid Post',
                content='This should fail',
                author=self.user
            )
        self.assertIn('Invalid post type', str(context.exception))
    
    def test_create_post_with_default_content(self):
        """Test creating a post with default empty content"""
        post = PostFactory.create_post(
            post_type='text',
            title='Post Without Content',
            author=self.user
        )
        self.assertEqual(post.content, '')
    
    def test_create_post_without_author(self):
        """Test creating a post without an author"""
        post = PostFactory.create_post(
            post_type='text',
            title='Authorless Post',
            content='Post without author'
        )
        self.assertIsNone(post.author)


class CreatePostViewTestCase(APITestCase):
    """Test cases for the CreatePostView API endpoint"""
    
    def setUp(self):
        """Set up test client and user with authentication"""
        self.client = APIClient()
        self.django_user = DjangoUser.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        self.token = Token.objects.create(user=self.django_user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
    
    def test_create_text_post_via_api(self):
        """Test creating a text post through the API"""
        data = {
            'post_type': 'text',
            'title': 'API Text Post',
            'content': 'Created via API'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('post_id', response.data)
        self.assertEqual(response.data['post_type'], 'text')
        self.assertEqual(response.data['title'], 'API Text Post')
        
        # Verify post was created in database
        post = Post.objects.get(id=response.data['post_id'])
        self.assertEqual(post.author, self.django_user)
        self.assertEqual(post.content, 'Created via API')
    
    def test_create_image_post_via_api(self):
        """Test creating an image post through the API"""
        data = {
            'post_type': 'image',
            'title': 'API Image Post',
            'content': 'Image content',
            'metadata': {'file_size': 2048000, 'format': 'jpg'}
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['post_type'], 'image')
    
    def test_create_video_post_via_api(self):
        """Test creating a video post through the API"""
        data = {
            'post_type': 'video',
            'title': 'API Video Post',
            'content': 'Video content',
            'metadata': {'duration': 180, 'codec': 'h264'}
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['post_type'], 'video')
    
    def test_create_post_without_title_fails(self):
        """Test that creating a post without title returns 400"""
        data = {
            'post_type': 'text',
            'content': 'Missing title'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_create_image_post_without_file_size_fails(self):
        """Test that creating an image post without file_size returns 400"""
        data = {
            'post_type': 'image',
            'title': 'Invalid Image',
            'content': 'Missing file_size'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file_size', response.data['error'])
    
    def test_create_video_post_without_duration_fails(self):
        """Test that creating a video post without duration returns 400"""
        data = {
            'post_type': 'video',
            'title': 'Invalid Video',
            'content': 'Missing duration'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data['error'])
    
    def test_create_post_with_invalid_type_fails(self):
        """Test that creating a post with invalid type returns 400"""
        data = {
            'post_type': 'invalid',
            'title': 'Invalid Type Post',
            'content': 'Should fail'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid post type', response.data['error'])
    
    def test_create_post_without_authentication_fails(self):
        """Test that creating a post without authentication returns 401"""
        self.client.credentials()  # Remove authentication
        data = {
            'post_type': 'text',
            'title': 'Unauthenticated Post',
            'content': 'Should fail'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_post_defaults_to_text_type(self):
        """Test that post_type defaults to 'text' if not provided"""
        data = {
            'title': 'Default Type Post',
            'content': 'Should default to text'
        }
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['post_type'], 'text')

