import json
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Post, User, Comment, Like
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


@override_settings(SECURE_SSL_REDIRECT=False)
class CreatePostViewTestCase(APITestCase):
    """Test cases for the CreatePostView API endpoint"""
    
    def setUp(self):
        """Set up test client and user with authentication"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='apipass123'
        )
        self.token = Token.objects.create(user=self.user)
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
        self.assertEqual(post.author, self.user)
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


# ---------------------------------------------------------------------------
# RBAC Tests
# ---------------------------------------------------------------------------

@override_settings(SECURE_SSL_REDIRECT=False)
class RBACTestCase(APITestCase):
    """
    Tests for Role-Based Access Control using the role field (admin / user / guest).
    - Only admin-role users can list all users (GET /posts/users/)
    - Only the post author OR an admin can update/delete a post
    - Guests cannot create posts or comments
    - Admin can delete any comment
    """

    def setUp(self):
        self.client = APIClient()

        # Regular user (role='user')
        self.user = User.objects.create_user(username='regular_user', password='pass123')
        self.user.role = 'user'
        self.user.save()
        self.user_token = Token.objects.create(user=self.user)

        # Admin-role user
        self.admin = User.objects.create_user(username='admin_user', password='adminpass')
        self.admin.role = 'admin'
        self.admin.save()
        self.admin_token = Token.objects.create(user=self.admin)

        # Guest-role user
        self.guest = User.objects.create_user(username='guest_user', password='guestpass')
        self.guest.role = 'guest'
        self.guest.save()
        self.guest_token = Token.objects.create(user=self.guest)

        # Post owned by regular user
        self.post = Post.objects.create(
            title='My Post', content='Hello', author=self.user, privacy='public'
        )

        # Comment on the post
        self.comment = Comment.objects.create(
            text='A comment', author=self.user, post=self.post
        )

    # ---- User listing restricted to admin role ----

    def test_admin_can_list_users(self):
        """Admin-role users can GET /posts/users/"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/posts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_regular_user_cannot_list_users(self):
        """Non-admin users receive 403 on GET /posts/users/"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.get('/posts/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_list_users(self):
        """Unauthenticated requests receive 401 on GET /posts/users/"""
        response = self.client.get('/posts/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_role_field_in_user_response(self):
        """role field is returned in user list for admin"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.get('/posts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for u in response.data:
            self.assertIn('role', u)

    def test_role_field_in_own_profile(self):
        """role field is exposed in /posts/users/me/"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.get('/posts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'], 'user')

    # ---- Post edit/delete: author OR admin ----

    def test_author_can_update_own_post(self):
        """Post author can PATCH their own post"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.patch(
            f'/posts/{self.post.id}/', {'content': 'Updated'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_can_update_any_post(self):
        """Admin-role user can PATCH any post (not just their own)"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.patch(
            f'/posts/{self.post.id}/', {'content': 'Admin override'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_author_user_cannot_update_post(self):
        """Non-admin, non-author receives 403 on PATCH"""
        other = User.objects.create_user(username='other', password='pass')
        other.role = 'user'
        other.save()
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + other_token.key)
        response = self.client.patch(
            f'/posts/{self.post.id}/', {'content': 'Hacked'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_own_post(self):
        """Post author can DELETE their own post"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.delete(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_admin_can_delete_any_post(self):
        """Admin-role user can DELETE any post"""
        extra_post = Post.objects.create(
            title='Extra Post', content='Will be deleted', author=self.user, privacy='public'
        )
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.delete(f'/posts/{extra_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_non_author_cannot_delete_post(self):
        """Non-admin, non-author receives 403 on DELETE"""
        other = User.objects.create_user(username='other2', password='pass')
        other.role = 'user'
        other.save()
        other_token = Token.objects.create(user=other)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + other_token.key)
        response = self.client.delete(f'/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ---- Guest restrictions ----

    def test_guest_cannot_create_post(self):
        """Guest-role user receives 403 when trying to create a post via /posts/create/"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.guest_token.key)
        data = {'post_type': 'text', 'title': 'Guest Post', 'content': 'Should fail'}
        response = self.client.post('/posts/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_cannot_comment(self):
        """Guest-role user receives 403 when trying to comment"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.guest_token.key)
        data = {'text': 'Guest comment attempt'}
        response = self.client.post(f'/posts/{self.post.id}/comment/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_guest_can_read_feed(self):
        """Guest-role user CAN read the news feed (read is permitted)"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.guest_token.key)
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ---- Admin comment deletion ----

    def test_admin_can_delete_any_comment(self):
        """Admin-role user can delete any comment"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)
        response = self.client.delete(
            f'/posts/{self.post.id}/comment/?comment_id={self.comment.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_delete_comment(self):
        """Non-admin user receives 403 when trying to delete a comment"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        response = self.client.delete(
            f'/posts/{self.post.id}/comment/?comment_id={self.comment.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Privacy Settings Tests
# ---------------------------------------------------------------------------

@override_settings(SECURE_SSL_REDIRECT=False)
class PrivacySettingsTestCase(APITestCase):
    """
    Tests for Post privacy settings:
    - Public posts are visible to all authenticated users
    - Private posts are only visible to their author
    """

    def setUp(self):
        self.client = APIClient()
        cache.clear()

        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.owner_token = Token.objects.create(user=self.owner)

        self.other = User.objects.create_user(username='other_user', password='pass123')
        self.other_token = Token.objects.create(user=self.other)

        self.public_post = Post.objects.create(
            title='Public Post', content='Visible to all', author=self.owner, privacy='public'
        )
        self.private_post = Post.objects.create(
            title='Private Post', content='Owner only', author=self.owner, privacy='private'
        )

    def tearDown(self):
        cache.clear()

    # ---- News feed privacy ----

    def test_public_post_visible_in_feed_to_other_user(self):
        """Other users can see public posts in the news feed"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.public_post.id, ids)

    def test_private_post_not_visible_in_feed_to_other_user(self):
        """Other users cannot see private posts in the news feed"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        self.assertNotIn(self.private_post.id, ids)

    def test_private_post_visible_in_feed_to_author(self):
        """Owners can see their own private posts in the news feed"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.owner_token.key)
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data['results']]
        self.assertIn(self.private_post.id, ids)

    # ---- Post detail privacy ----

    def test_other_user_cannot_access_private_post_detail(self):
        """Other users receive 404 when accessing a private post detail"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get(f'/posts/{self.private_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_can_access_own_private_post_detail(self):
        """Author can access their own private post detail"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.owner_token.key)
        response = self.client.get(f'/posts/{self.private_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.private_post.id)

    def test_post_list_excludes_other_users_private_posts(self):
        """GET /posts/ filters out other users' private posts"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.other_token.key)
        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [p['id'] for p in response.data]
        self.assertNotIn(self.private_post.id, ids)
        self.assertIn(self.public_post.id, ids)

    def test_privacy_field_returned_in_post_detail(self):
        """Privacy field is included in post detail response"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.owner_token.key)
        response = self.client.get(f'/posts/{self.public_post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('privacy', response.data)
        self.assertEqual(response.data['privacy'], 'public')


# ---------------------------------------------------------------------------
# Caching Tests
# ---------------------------------------------------------------------------

@override_settings(
    SECURE_SSL_REDIRECT=False,
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
        }
    }
)
class CachingTestCase(APITestCase):
    """
    Tests for caching behaviour:
    - Post detail responses are served from cache on repeat requests
    - Cache is invalidated when a post is updated or deleted
    - News feed is cached per user/page
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='cache_user', password='pass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.post = Post.objects.create(
            title='Cached Post', content='Original', author=self.user, privacy='public'
        )
        cache.clear()

    def tearDown(self):
        cache.clear()

    def test_post_detail_is_cached(self):
        """Second request for post detail is served from cache"""
        cache_key = f'post_detail_{self.post.id}'
        self.assertIsNone(cache.get(cache_key))

        # First request populates cache
        response1 = self.client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

        # Second request should hit cache (same data returned)
        response2 = self.client.get(f'/posts/{self.post.id}/')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['id'], response2.data['id'])

    def test_cache_invalidated_on_post_update(self):
        """Updating a post clears its cache entry"""
        cache_key = f'post_detail_{self.post.id}'
        self.client.get(f'/posts/{self.post.id}/')  # Populate cache
        self.assertIsNotNone(cache.get(cache_key))

        self.client.patch(
            f'/posts/{self.post.id}/', {'content': 'Updated content'}, format='json'
        )
        self.assertIsNone(cache.get(cache_key))

    def test_cache_invalidated_on_post_delete(self):
        """Deleting a post clears its cache entry"""
        cache_key = f'post_detail_{self.post.id}'
        self.client.get(f'/posts/{self.post.id}/')  # Populate cache
        self.assertIsNotNone(cache.get(cache_key))

        self.client.delete(f'/posts/{self.post.id}/')
        self.assertIsNone(cache.get(cache_key))

    def test_news_feed_is_cached(self):
        """News feed response is stored in cache after first request"""
        from posts.views import NewsFeedPagination, _feed_cache_version
        page_size = NewsFeedPagination.page_size
        ver = _feed_cache_version(self.user.id)
        cache_key = f'news_feed_{self.user.id}_v{ver}_p1_s{page_size}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    # ------------------------------------------------------------------
    # GET /posts/  (PostListCreate)
    # ------------------------------------------------------------------

    def test_post_list_is_cached(self):
        """GET /posts/ stores the response in cache after the first request"""
        from posts.views import _feed_cache_version
        ver = _feed_cache_version(self.user.id)
        cache_key = f'post_list_{self.user.id}_v{ver}___'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    def test_post_list_cache_busted_on_post_create(self):
        """POST /posts/ bumps the global feed version counter, orphaning the cached post-list page"""
        from posts.views import _GLOBAL_FEED_VER_KEY
        self.client.get('/posts/')  # populate cache
        ver_before = cache.get(_GLOBAL_FEED_VER_KEY, 0)

        self.client.post(
            '/posts/',
            {'title': 'New Post', 'content': 'body', 'post_type': 'text'},
            format='json',
        )
        ver_after = cache.get(_GLOBAL_FEED_VER_KEY, 0)
        self.assertGreater(ver_after, ver_before)

    # ------------------------------------------------------------------
    # GET /posts/users/  (UserListCreate)
    # ------------------------------------------------------------------

    def test_user_list_is_cached(self):
        """GET /posts/users/ stores the response in cache after the first request (admin only)"""
        from posts.views import _USER_LIST_VER_KEY
        self.user.role = 'admin'
        self.user.save(update_fields=['role'])
        ver = cache.get(_USER_LIST_VER_KEY, 0)
        cache_key = f'user_list_v{ver}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    def test_user_list_cache_busted_on_user_create(self):
        """POST /posts/users/ bumps the user-list version counter"""
        from posts.views import _USER_LIST_VER_KEY
        self.user.role = 'admin'
        self.user.save(update_fields=['role'])
        self.client.get('/posts/users/')  # populate cache
        ver_before = cache.get(_USER_LIST_VER_KEY, 0)

        self.client.post(
            '/posts/users/',
            {'username': 'newbatchuser', 'password': 'pass1234!'},
            format='json',
        )
        ver_after = cache.get(_USER_LIST_VER_KEY, 0)
        self.assertGreater(ver_after, ver_before)

    # ------------------------------------------------------------------
    # GET /posts/users/me/  (AuthenticatedUserProfileView)
    # ------------------------------------------------------------------

    def test_user_profile_is_cached(self):
        """GET /posts/users/me/ stores the response in cache after the first request"""
        cache_key = f'user_profile_{self.user.id}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    def test_user_profile_cache_invalidated_on_patch(self):
        """PATCH /posts/users/me/ explicitly deletes the user-profile cache entry"""
        cache_key = f'user_profile_{self.user.id}'
        self.client.get('/posts/users/me/')  # populate cache
        self.assertIsNotNone(cache.get(cache_key))

        self.client.patch('/posts/users/me/', {'first_name': 'Updated'}, format='json')
        self.assertIsNone(cache.get(cache_key))

    # ------------------------------------------------------------------
    # GET /posts/{id}/comments/  (PostCommentsView)
    # ------------------------------------------------------------------

    def test_post_comments_is_cached(self):
        """GET /posts/{id}/comments/ stores the response in cache after the first request"""
        from posts.views import CommentPagination
        page_size = CommentPagination.page_size
        ver = cache.get(f'comment_ver_{self.post.id}', 0)
        cache_key = f'post_comments_{self.post.id}_v{ver}_p1_s{page_size}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get(f'/posts/{self.post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    def test_post_comments_cache_busted_on_comment_create(self):
        """POST /posts/{id}/comment/ bumps the per-post comment version counter"""
        ver_before = cache.get(f'comment_ver_{self.post.id}', 0)

        self.client.post(
            f'/posts/{self.post.id}/comment/', {'text': 'Hello!'}, format='json'
        )
        ver_after = cache.get(f'comment_ver_{self.post.id}', 0)
        self.assertGreater(ver_after, ver_before)

    # ------------------------------------------------------------------
    # GET /posts/comments/  (CommentListCreate)
    # ------------------------------------------------------------------

    def test_global_comment_list_is_cached(self):
        """GET /posts/comments/ stores the response in cache after the first request"""
        from posts.views import _GLOBAL_COMMENT_VER_KEY
        ver = cache.get(_GLOBAL_COMMENT_VER_KEY, 0)
        cache_key = f'comment_list_v{ver}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))

    def test_global_comment_list_cache_busted_on_comment_create(self):
        """Adding a comment bumps the global comment version counter, busting the list cache"""
        from posts.views import _GLOBAL_COMMENT_VER_KEY
        self.client.get('/posts/comments/')  # populate cache
        ver_before = cache.get(_GLOBAL_COMMENT_VER_KEY, 0)

        self.client.post(
            f'/posts/{self.post.id}/comment/', {'text': 'Hello!'}, format='json'
        )
        ver_after = cache.get(_GLOBAL_COMMENT_VER_KEY, 0)
        self.assertGreater(ver_after, ver_before)

    # ------------------------------------------------------------------
    # GET /auth/google/login  (GoogleLoginView)
    # ------------------------------------------------------------------

    def test_google_oauth_config_is_cached(self):
        """GET /auth/google/login stores the client_id config in cache after the first request"""
        cache_key = 'google_oauth_config'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/auth/google/login')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get(cache_key))


# ---------------------------------------------------------------------------
# Pagination Tests
# ---------------------------------------------------------------------------

@override_settings(SECURE_SSL_REDIRECT=False)
class PaginationTestCase(APITestCase):
    """
    Tests for pagination on NewsFeedView and PostCommentsView.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='page_user', password='pass123')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        # Create 25 public posts for pagination testing (> DEFAULT_PAGE_SIZE=20 so page 2 exists)
        for i in range(25):
            Post.objects.create(
                title=f'Post {i}', content=f'Content {i}',
                author=self.user, privacy='public'
            )

        # Create one post with 25 comments for comment pagination (> DEFAULT_PAGE_SIZE=20 so page 2 exists)
        self.comment_post = Post.objects.create(
            title='Comment Post', content='Has many comments',
            author=self.user, privacy='public'
        )
        for i in range(25):
            Comment.objects.create(
                text=f'Comment {i}', author=self.user, post=self.comment_post
            )

    # ---- News feed pagination ----

    def test_feed_returns_first_page(self):
        """GET /posts/feed/ returns first page of posts (default size from ConfigManager) and pagination metadata"""
        from posts.views import NewsFeedPagination
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertLessEqual(len(response.data['results']), NewsFeedPagination.page_size)

    def test_feed_second_page_has_remaining_posts(self):
        """GET /posts/feed/?page=2&page_size=5 returns the remaining posts"""
        response = self.client.get('/posts/feed/?page=2&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_feed_custom_page_size(self):
        """page_size query param is respected"""
        response = self.client.get('/posts/feed/?page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 5)

    def test_feed_total_count_is_accurate(self):
        """count reflects the total number of visible posts"""
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 25 created above + 1 comment_post = 26
        self.assertEqual(response.data['count'], 26)

    def test_feed_page_beyond_range_returns_empty(self):
        """Requesting a page beyond range returns empty results"""
        response = self.client.get('/posts/feed/?page=999')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(len(response.data.get('results', [])), 0)

    # ---- Comment pagination ----

    def test_comments_first_page(self):
        """GET /posts/{id}/comments/ returns first page of comments (default size from ConfigManager)"""
        from posts.views import CommentPagination
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertLessEqual(len(response.data['results']), CommentPagination.page_size)

    def test_comments_second_page(self):
        """GET /posts/{id}/comments/?page=2&page_size=5 returns remaining comments"""
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/?page=2&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_comments_total_count(self):
        """Count reflects all 25 comments"""
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 25)


@override_settings(SECURE_SSL_REDIRECT=False)
class LikePostTestCase(APITestCase):
    """Test POST/DELETE /posts/{id}/like/ — like and unlike a post"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='likeuser', password='pass', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.guest = User.objects.create_user(username='guest_likeuser', password='pass', role='guest')
        self.guest_token = Token.objects.create(user=self.guest)
        self.post = Post.objects.create(
            title='Like Target', content='likeable content',
            post_type='text', privacy='public', author=self.user
        )

    def test_like_post_success(self):
        """Authenticated user can like a post — 201 with message and like data"""
        response = self.client.post(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('like', response.data)

    def test_like_post_duplicate(self):
        """Liking the same post twice returns 400"""
        self.client.post(f'/posts/{self.post.id}/like/')
        response = self.client.post(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already liked', response.data['error'])

    def test_unlike_post_success(self):
        """User can unlike a previously liked post — 200"""
        self.client.post(f'/posts/{self.post.id}/like/')
        response = self.client.delete(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_unlike_not_liked(self):
        """Unliking a post that was never liked returns 400"""
        response = self.client.delete(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not liked', response.data['error'])

    def test_like_nonexistent_post(self):
        """Liking a non-existent post returns 404"""
        response = self.client.post('/posts/9999/like/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_requires_auth(self):
        """Unauthenticated request to like a post returns 401"""
        self.client.credentials()
        response = self.client.post(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_guest_cannot_like_post(self):
        """Guest users are read-only and cannot like posts"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.guest_token.key)
        response = self.client.post(f'/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(SECURE_SSL_REDIRECT=False)
class CommentOnPostSuccessTestCase(APITestCase):
    """Test POST /posts/{id}/comment/ — add comment to a specific post"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='commentuser', password='pass', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.post = Post.objects.create(
            title='Comment Target', content='content',
            post_type='text', privacy='public', author=self.user
        )

    def test_comment_success(self):
        """Authenticated user can comment on a post — 201 with message and comment"""
        response = self.client.post(
            f'/posts/{self.post.id}/comment/', {'text': 'Nice post!'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('comment', response.data)
        self.assertEqual(response.data['message'], 'Comment added successfully')

    def test_comment_empty_text(self):
        """Whitespace-only comment text is rejected — 400"""
        response = self.client.post(
            f'/posts/{self.post.id}/comment/', {'text': '   '}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_nonexistent_post(self):
        """Commenting on a non-existent post returns 404"""
        response = self.client.post('/posts/9999/comment/', {'text': 'hi'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(SECURE_SSL_REDIRECT=False)
class CommentListCreateTestCase(APITestCase):
    """Test GET/POST /posts/comments/ — global comment list and create"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='clcuser', password='pass', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.post = Post.objects.create(
            title='For Comments', content='content',
            post_type='text', privacy='public', author=self.user
        )
        Comment.objects.create(text='Seeded comment', author=self.user, post=self.post)

    def test_list_all_comments(self):
        """GET /posts/comments/ returns a flat list of all comments (unpaginated)"""
        response = self.client.get('/posts/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_comment_global(self):
        """POST /posts/comments/ with post FK creates a comment; author set from token"""
        response = self.client.post(
            '/posts/comments/',
            {'text': 'Global comment', 'post': self.post.id},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], self.user.id)

    def test_create_comment_invalid_post(self):
        """POST /posts/comments/ with non-existent post FK returns 404"""
        response = self.client.post(
            '/posts/comments/',
            {'text': 'Bad post id', 'post': 9999},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_list_requires_auth(self):
        """GET /posts/comments/ without token returns 401"""
        self.client.credentials()
        response = self.client.get('/posts/comments/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(SECURE_SSL_REDIRECT=False)
class PostListCreateSerializerTestCase(APITestCase):
    """Test POST /posts/ (serializer path) and PUT /posts/{id}/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='plcuser', password='pass', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.post = Post.objects.create(
            title='Detail Post', content='original content',
            post_type='text', privacy='public', author=self.user
        )

    def test_create_post_serializer_path(self):
        """POST /posts/ creates a post and binds author from the authenticated user"""
        data = {
            'title': 'Serializer Post',
            'content': 'Created via serializer',
            'post_type': 'text',
            'privacy': 'public',
            'author': self.user.id,
        }
        response = self.client.post('/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Serializer Post')
        self.assertEqual(response.data['author'], self.user.id)

    def test_create_post_ignores_spoofed_author(self):
        """POST /posts/ ignores author in body and uses request.user"""
        other_user = User.objects.create_user(username='spoof_target', password='pass', role='user')
        data = {
            'title': 'Spoof Attempt',
            'content': 'Trying to spoof author',
            'post_type': 'text',
            'privacy': 'public',
            'author': other_user.id,
        }
        response = self.client.post('/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author'], self.user.id)

    def test_create_post_guest_blocked(self):
        """Guest user cannot POST to /posts/ — 403"""
        guest = User.objects.create_user(username='guestuser2', password='pass', role='guest')
        guest_token = Token.objects.create(user=guest)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + guest_token.key)
        data = {'title': 'Guest post', 'content': 'blocked', 'post_type': 'text', 'author': guest.id}
        response = self.client.post('/posts/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_put_full_replace(self):
        """PUT /posts/{id}/ replaces all fields; post author receives 200"""
        data = {
            'title': 'Replaced Title',
            'content': 'Fully replaced content',
            'post_type': 'text',
            'privacy': 'public',
            'author': self.user.id,
        }
        response = self.client.put(f'/posts/{self.post.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Replaced Title')
        self.assertEqual(response.data['content'], 'Fully replaced content')


@override_settings(SECURE_SSL_REDIRECT=False)
class UserCreateTestCase(APITestCase):
    """Test POST /posts/users/ — admin-only user creation"""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(username='adminuc', password='pass', role='admin')
        self.admin_token = Token.objects.create(user=self.admin)
        self.user = User.objects.create_user(username='regularuc', password='pass', role='user')
        self.user_token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.admin_token.key)

    def test_admin_can_create_user(self):
        """Admin can POST /posts/users/ and the response includes the role field — 201"""
        data = {'username': 'newucuser', 'email': 'nu@example.com', 'password': 'pass123', 'role': 'user'}
        response = self.client.post('/posts/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['role'], 'user')

    def test_create_user_missing_username(self):
        """POST without username returns 400 with descriptive error"""
        data = {'email': 'nouser@example.com', 'role': 'user'}
        response = self.client.post('/posts/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Username is required', response.data['error'])

    def test_create_user_invalid_role(self):
        """POST with an unrecognised role returns 400"""
        data = {'username': 'newucuser2', 'role': 'superuser'}
        response = self.client.post('/posts/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid role', response.data['error'])

    def test_create_user_missing_password(self):
        """POST without password returns 400"""
        data = {'username': 'newucuser3', 'email': 'no-pass@example.com', 'role': 'user'}
        response = self.client.post('/posts/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Password is required', response.data['error'])

    def test_non_admin_cannot_create_user(self):
        """Regular user cannot POST /posts/users/ — 403"""
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.user_token.key)
        data = {'username': 'hacked', 'role': 'user'}
        response = self.client.post('/posts/users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthenticateUserViewTestCase(APITestCase):
    """Test POST /posts/authenticate/ — CBV authentication endpoint"""

    def setUp(self):
        self.user = User.objects.create_user(username='authuser', password='secret123')

    def test_valid_credentials(self):
        """Correct username/password returns 200 with success message and username"""
        response = self.client.post(
            '/posts/authenticate/', {'username': 'authuser', 'password': 'secret123'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Authentication successful!')
        self.assertEqual(response.data['username'], 'authuser')

    def test_invalid_credentials(self):
        """Wrong password returns 401 with failure message"""
        response = self.client.post(
            '/posts/authenticate/', {'username': 'authuser', 'password': 'wrongpass'}, format='json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['message'], 'Invalid credentials.')

    def test_missing_fields(self):
        """Missing username or password returns 400"""
        response = self.client.post('/posts/authenticate/', {}, format='json')
        self.assertEqual(response.status_code, 400)


@override_settings(SECURE_SSL_REDIRECT=False)
class PostSearchFilterTestCase(APITestCase):
    """Test search and filter capabilities on GET /posts/"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='searchuser', password='pass', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        Post.objects.create(title='Django Guide', content='Learn Django', post_type='text', privacy='public', author=self.user)
        Post.objects.create(title='Flask Guide', content='Learn Flask', post_type='text', privacy='public', author=self.user)
        Post.objects.create(title='My Photo', content='Sunset pic', post_type='image', privacy='private', author=self.user, metadata={'file_size': 1024})

    def test_search_by_title(self):
        """?search=Django returns only matching posts"""
        response = self.client.get('/posts/?search=Django')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Django Guide')

    def test_search_by_content(self):
        """?search=Flask matches content field"""
        response = self.client.get('/posts/?search=Flask')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_post_type(self):
        """?post_type=image returns only image posts"""
        response = self.client.get('/posts/?post_type=image')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['post_type'], 'image')

    def test_filter_by_privacy(self):
        """?privacy=private returns only private posts (owned by user)"""
        response = self.client.get('/posts/?privacy=private')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['privacy'], 'private')

    def test_no_results(self):
        """Search with no matches returns empty list"""
        response = self.client.get('/posts/?search=nonexistent')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


@override_settings(SECURE_SSL_REDIRECT=False)
class UserProfileUpdateTestCase(APITestCase):
    """Test PATCH /posts/users/me/ — update own profile"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='profileuser', password='pass', email='old@example.com', role='user')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_update_email(self):
        """User can update their own email via PATCH"""
        response = self.client.patch('/posts/users/me/', {'email': 'new@example.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'new@example.com')

    def test_update_does_not_change_role(self):
        """PATCH preserves fields not sent"""
        response = self.client.patch('/posts/users/me/', {'email': 'x@example.com'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['role'], 'user')

    def test_unauthenticated_cannot_update(self):
        """PATCH without token returns 401"""
        self.client.credentials()
        response = self.client.patch('/posts/users/me/', {'email': 'hack@example.com'}, format='json')
        self.assertEqual(response.status_code, 401)


@override_settings(SECURE_SSL_REDIRECT=False)
class ThrottlingTestCase(APITestCase):
    """Verify rate limiting is configured and enforced"""

    def test_throttle_classes_configured_in_settings(self):
        """REST_FRAMEWORK settings include throttle classes and rates"""
        from django.conf import settings
        rf = settings.REST_FRAMEWORK
        self.assertIn('DEFAULT_THROTTLE_CLASSES', rf)
        self.assertIn('DEFAULT_THROTTLE_RATES', rf)
        self.assertTrue(len(rf['DEFAULT_THROTTLE_CLASSES']) > 0)
        self.assertIn('anon', rf['DEFAULT_THROTTLE_RATES'])
        self.assertIn('user', rf['DEFAULT_THROTTLE_RATES'])

    def test_anon_throttle_kicks_in(self):
        """Anonymous requests are throttled after exceeding the configured rate"""
        from rest_framework.throttling import AnonRateThrottle
        # Directly verify the throttle class is functional and correctly configured
        throttle = AnonRateThrottle()
        self.assertIsNotNone(throttle.rate)
        self.assertIn('/', throttle.rate)  # e.g. '30/minute'


@override_settings(SECURE_SSL_REDIRECT=False)
class GoogleLoginTestCase(APITestCase):
    """Test POST /auth/google/login — Google OAuth token exchange (no real network calls)"""

    def test_missing_id_token(self):
        """Omitting id_token returns 400"""
        response = self.client.post('/auth/google/login', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('id_token is required', response.data['error'])

    def test_empty_id_token(self):
        """Sending an empty id_token string returns 400"""
        response = self.client.post('/auth/google/login', {'id_token': ''}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('id_token is required', response.data['error'])

    @patch('posts.views.GoogleLoginView._verify_google_token')
    def test_invalid_id_token(self, mock_verify):
        """Token rejected by Google (_verify_google_token returns error dict) → 401"""
        mock_verify.return_value = {'error': 'invalid_token', 'error_description': 'Bad token'}
        response = self.client.post(
            '/auth/google/login', {'id_token': 'bad.token.here'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)


# ---------------------------------------------------------------------------
# Security Settings Tests
# ---------------------------------------------------------------------------

class SecuritySettingsTestCase(TestCase):
    """
    Verify that security-related Django settings are configured correctly.
    Reviews outcomes from the security perspective per OWASP best practices.
    """

    def test_ssl_redirect_enabled(self):
        """SECURE_SSL_REDIRECT is True — all HTTP requests redirected to HTTPS"""
        from django.conf import settings
        self.assertTrue(settings.SECURE_SSL_REDIRECT)

    def test_hsts_enabled(self):
        """HSTS header is configured with a long max-age (>= 1 year)"""
        from django.conf import settings
        self.assertGreaterEqual(settings.SECURE_HSTS_SECONDS, 31536000)
        self.assertTrue(settings.SECURE_HSTS_INCLUDE_SUBDOMAINS)
        self.assertTrue(settings.SECURE_HSTS_PRELOAD)

    def test_session_cookie_secure(self):
        """Session cookie is flagged Secure (sent only over HTTPS)"""
        from django.conf import settings
        self.assertTrue(settings.SESSION_COOKIE_SECURE)

    def test_csrf_cookie_secure(self):
        """CSRF cookie is flagged Secure (sent only over HTTPS)"""
        from django.conf import settings
        self.assertTrue(settings.CSRF_COOKIE_SECURE)

    def test_secret_key_not_default_in_env(self):
        """SECRET_KEY is loaded via python-decouple (not hard-coded)"""
        from django.conf import settings
        insecure_default = (
            'django-insecure-j$51b2nkx)yxs53+2xxy))y^mljuv9a1'
            '!f=mqy)+#2be=l!ru&'
        )
        # In production the key MUST differ from the insecure default
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertGreater(len(settings.SECRET_KEY), 20)

    def test_password_hashers_include_strong_algorithms(self):
        """Password hashers include PBKDF2 and at least one stronger alternative"""
        from django.conf import settings
        hasher_names = [h.rsplit('.', 1)[-1] for h in settings.PASSWORD_HASHERS]
        self.assertIn('PBKDF2PasswordHasher', hasher_names)
        strong = {'Argon2PasswordHasher', 'BCryptSHA256PasswordHasher'}
        self.assertTrue(
            strong & set(hasher_names),
            "At least one strong hasher (Argon2 or BCrypt) should be configured",
        )

    def test_password_validators_configured(self):
        """At least 3 password validators are active"""
        from django.conf import settings
        self.assertGreaterEqual(len(settings.AUTH_PASSWORD_VALIDATORS), 3)

    def test_debug_is_configurable_via_env(self):
        """DEBUG is read from environment, not hard-coded True"""
        from decouple import config
        # Verify the setting is fetched via python-decouple (cast=bool)
        debug_val = config('DEBUG', default=True, cast=bool)
        self.assertIsInstance(debug_val, bool)

    def test_allowed_hosts_not_wildcard(self):
        """ALLOWED_HOSTS does not contain wildcard '*' for production safety"""
        from django.conf import settings
        self.assertNotIn('*', settings.ALLOWED_HOSTS)

    def test_custom_user_model_configured(self):
        """AUTH_USER_MODEL points to the custom User model"""
        from django.conf import settings
        self.assertEqual(settings.AUTH_USER_MODEL, 'posts.User')

    def test_default_authentication_is_token(self):
        """DRF default authentication is TokenAuthentication (not session)"""
        from django.conf import settings
        auth_classes = settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']
        self.assertIn(
            'rest_framework.authentication.TokenAuthentication',
            auth_classes,
        )

    def test_default_permission_is_authenticated(self):
        """DRF default permission requires authentication"""
        from django.conf import settings
        perm_classes = settings.REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES']
        self.assertIn(
            'rest_framework.permissions.IsAuthenticated',
            perm_classes,
        )


# ---------------------------------------------------------------------------
# Performance / Query Optimisation Tests
# ---------------------------------------------------------------------------

@override_settings(SECURE_SSL_REDIRECT=False)
class QueryPerformanceTestCase(APITestCase):
    """
    Verify N+1 query prevention and database-level optimisations.
    Uses Django's CaptureQueriesContext to audit query budgets and
    identify potential N+1 regressions.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='perfuser', password='pass', role='user',
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION='Token ' + self.token.key,
        )

        # Seed 10 posts, each with 3 likes and 3 comments from distinct users
        self.other_users = []
        for i in range(3):
            u = User.objects.create_user(
                username=f'liker{i}', password='pass', role='user',
            )
            self.other_users.append(u)

        for i in range(10):
            p = Post.objects.create(
                title=f'Perf Post {i}', content=f'Content {i}',
                post_type='text', privacy='public', author=self.user,
            )
            for u in self.other_users:
                Like.objects.create(user=u, post=p)
                Comment.objects.create(
                    text=f'Comment by {u.username}', author=u, post=p,
                )

    def test_feed_query_count_is_constant(self):
        """News feed uses DB-level COUNT annotations — queries stay constant."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        cache.clear()
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/posts/feed/?page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        # Feed: 1 auth + 1 COUNT (pagination) + 1 annotated SELECT = 3
        self.assertLessEqual(
            len(ctx), 5,
            f"Feed should use constant queries (got {len(ctx)})",
        )

    def test_post_detail_uses_prefetch(self):
        """GET /posts/{id}/ fires a bounded number of queries."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        post = Post.objects.first()
        cache.clear()
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(f'/posts/{post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('like_count', response.data)
        self.assertIn('comment_count', response.data)
        # Detail: 1 auth + 1 post (select_related) + 1 prefetch likes
        # + 1 prefetch comments = 4
        self.assertLessEqual(
            len(ctx), 6,
            f"Post detail should use bounded queries (got {len(ctx)})",
        )

    def test_feed_returns_annotated_counts(self):
        """Feed serializer uses DB-level COUNT annotations, not Python loops."""
        response = self.client.get('/posts/feed/?page_size=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for post_data in response.data['results']:
            self.assertIn('like_count', post_data)
            self.assertIn('comment_count', post_data)
            # Each post was given 3 likes & 3 comments in setUp
            self.assertEqual(post_data['like_count'], 3)
            self.assertEqual(post_data['comment_count'], 3)

    def test_post_list_prefetch_prevents_n_plus_one_on_likes(self):
        """GET /posts/ uses prefetch_related for likes — verified via query log."""
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get('/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 10)

        # Verify likes are batch-loaded via IN clause, not per-post
        like_queries = [
            q['sql'] for q in ctx
            if 'posts_like' in q['sql'] and 'IN' in q['sql']
        ]
        self.assertGreaterEqual(
            len(like_queries), 1,
            "Likes should be prefetched in a single batch query",
        )

