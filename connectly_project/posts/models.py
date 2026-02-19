from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # AbstractUser already provides: username, password, email, first_name, last_name, is_staff, is_active, date_joined
    # We keep created_at for compatibility with existing code
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username


class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    title = models.CharField(max_length=255, default='Untitled')
    content = models.TextField()
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='text')
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
