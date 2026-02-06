from rest_framework import serializers
<<<<<<< HEAD
from .models import User, Post
=======
from django.contrib.auth.models import User as AuthUser
from .models import User, Post, Comment

>>>>>>> mainrepo/master

class AuthUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['username', 'email']  # Exclude sensitive fields like password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']
        read_only_fields = ['created_at'] # created_at should be read-only

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username') # Add author's username for display

    class Meta:
        model = Post
        fields = ['id', 'content', 'author_username', 'created_at'] # Removed 'author'
        read_only_fields = ['created_at', 'author_username'] # created_at and author_username should be read-only
