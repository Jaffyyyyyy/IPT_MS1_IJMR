from rest_framework import serializers
from django.contrib.auth.models import User as AuthUser
from .models import User, Post, Comment, Task, Like


class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['username', 'email']  # Exclude sensitive fields like password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'content', 'author', 'created_at', 'comments', 'like_count', 'comment_count']

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_comment_count(self, obj):
        return obj.comments.count()


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'text', 'author', 'post', 'created_at']


    def validate_post(self, value):
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Post not found.")
        return value


    def validate_author(self, value):
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Author not found.")
        return value


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'created_at']

    def validate_post(self, value):
        if not Post.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Post not found.")
        return value

    def validate_user(self, value):
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("User not found.")
        return value


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with validation for task types."""
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'task_type', 
                  'metadata', 'completed', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_assigned_to(self, value):
        """Ensure the assigned user exists."""
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Assigned user not found.")
        return value

    def validate(self, data):
        """Validate type-specific metadata requirements."""
        task_type = data.get('task_type', 'regular')
        metadata = data.get('metadata', {})

        if task_type == 'priority' and 'priority_level' not in metadata:
            raise serializers.ValidationError({
                'metadata': "Priority tasks require 'priority_level' in metadata."
            })
        if task_type == 'recurring' and 'frequency' not in metadata:
            raise serializers.ValidationError({
                'metadata': "Recurring tasks require 'frequency' in metadata."
            })
        
        return data
