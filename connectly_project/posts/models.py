from django.db import models


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
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


class Comment(models.Model):
    text = models.TextField()
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on Post {self.post.id}"
