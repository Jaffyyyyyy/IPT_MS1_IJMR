from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # AbstractUser already provides: username, password, email, first_name, last_name, is_staff, is_active, date_joined
    # We keep created_at for compatibility with existing code
    created_at = models.DateTimeField(auto_now_add=True)

    ROLE_ADMIN = 'admin'
    ROLE_USER  = 'user'
    ROLE_GUEST = 'guest'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER,  'User'),
        (ROLE_GUEST, 'Guest'),
    ]
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        help_text='Application-level role: admin > user > guest',
    )

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_guest_role(self):
        return self.role == self.ROLE_GUEST

    def __str__(self):
        return f'{self.username} ({self.role})'


class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]

    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    title = models.CharField(max_length=255, default='Untitled')
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='text')
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    metadata = models.JSONField(default=dict, blank=True)
    author = models.ForeignKey(User, related_name='posts', on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author.username if self.author else 'Unknown'} at {self.created_at}"

    @property
    def like_count(self):
        """Returns the total number of likes for this post"""
        return self.likes.count()

    @property
    def comment_count(self):
        """Returns the total number of comments for this post"""
        return self.comments.count()


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Newest comments first

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"


class Like(models.Model):
    """Model to track user likes on posts"""
    user = models.ForeignKey(User, related_name='likes', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure a user can only like a post once
        unique_together = ('user', 'post')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.post.title}"
