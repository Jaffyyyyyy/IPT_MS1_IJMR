from django.test import TestCase, override_settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from .models import Post, User, Comment
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
        # Cache key for page 1, default page_size
        from posts.views import NewsFeedPagination
        page_size = NewsFeedPagination.page_size
        cache_key = f'news_feed_{self.user.id}_p1_s{page_size}'
        self.assertIsNone(cache.get(cache_key))

        response = self.client.get('/posts/feed/')
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

        # Create 15 public posts for pagination testing
        for i in range(15):
            Post.objects.create(
                title=f'Post {i}', content=f'Content {i}',
                author=self.user, privacy='public'
            )

        # Create one post with 12 comments for comment pagination
        self.comment_post = Post.objects.create(
            title='Comment Post', content='Has many comments',
            author=self.user, privacy='public'
        )
        for i in range(12):
            Comment.objects.create(
                text=f'Comment {i}', author=self.user, post=self.comment_post
            )

    # ---- News feed pagination ----

    def test_feed_returns_first_page(self):
        """GET /posts/feed/ returns first 10 posts and pagination metadata"""
        response = self.client.get('/posts/feed/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertLessEqual(len(response.data['results']), 10)

    def test_feed_second_page_has_remaining_posts(self):
        """GET /posts/feed/?page=2 returns the remaining posts"""
        response = self.client.get('/posts/feed/?page=2')
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
        # 15 created above + 1 comment_post = 16
        self.assertEqual(response.data['count'], 16)

    def test_feed_page_beyond_range_returns_empty(self):
        """Requesting a page beyond range returns empty results"""
        response = self.client.get('/posts/feed/?page=999')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
        if response.status_code == status.HTTP_200_OK:
            self.assertEqual(len(response.data.get('results', [])), 0)

    # ---- Comment pagination ----

    def test_comments_first_page(self):
        """GET /posts/{id}/comments/ returns first 10 comments"""
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertLessEqual(len(response.data['results']), 10)

    def test_comments_second_page(self):
        """GET /posts/{id}/comments/?page=2 returns remaining comments"""
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/?page=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_comments_total_count(self):
        """Count reflects all 12 comments"""
        response = self.client.get(f'/posts/{self.comment_post.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 12)

