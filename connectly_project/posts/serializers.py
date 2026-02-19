from rest_framework import serializers
from .models import User, Post, Comment, Like


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']  # Exclude sensitive fields like password


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'post_type', 'metadata', 'author', 'author_username', 
                  'created_at', 'like_count', 'comment_count', 'comments']


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    text = serializers.CharField(required=True, allow_blank=True)  # Allow blank so custom validation runs

    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'author_username', 'post', 'post_title', 'created_at']
        read_only_fields = ['author', 'created_at']

    def validate_text(self, value):
        """Ensure comment text is not empty or only whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment text cannot be empty.")
        return value.strip()

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Post not found.")
        return value


class LikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'user_username', 'post', 'post_title', 'created_at']
        read_only_fields = ['user', 'created_at']
