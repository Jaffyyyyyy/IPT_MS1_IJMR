from rest_framework import serializers
from .models import User, Post, Comment, Like


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'created_at']  # Exclude sensitive fields like password


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.StringRelatedField(many=True, read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'post_type', 'privacy', 'metadata', 'author',
                  'author_username', 'created_at', 'like_count', 'comment_count', 'comments']
        read_only_fields = ['author', 'created_at']

    def get_like_count(self, obj):
        # Prefer DB-level annotation (set by annotate() in list views) to avoid
        # per-object COUNT queries that bypass prefetch_related.
        if hasattr(obj, 'annotated_like_count'):
            return obj.annotated_like_count
        return obj.likes.count()

    def get_comment_count(self, obj):
        if hasattr(obj, 'annotated_comment_count'):
            return obj.annotated_comment_count
        return obj.comments.count()


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


class PostDetailSerializer(serializers.ModelSerializer):
    """
    Serializer used for the cached post detail endpoint.
    Counts are resolved from DB-level annotations (annotated_like_count /
    annotated_comment_count) to avoid extra per-post queries.
    """
    like_count = serializers.IntegerField(source='annotated_like_count', read_only=True)
    comment_count = serializers.IntegerField(source='annotated_comment_count', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'post_type', 'privacy', 'metadata',
            'author', 'author_username', 'created_at', 'like_count', 'comment_count',
        ]


class PostFeedSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the news feed.
    Excludes the nested comments list to avoid over-fetching; rely on
    DB-level annotated like_count / comment_count instead of model properties.
    """
    like_count = serializers.IntegerField(source='annotated_like_count', read_only=True)
    comment_count = serializers.IntegerField(source='annotated_comment_count', read_only=True)
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'post_type', 'privacy', 'metadata',
            'author', 'author_username', 'created_at', 'like_count', 'comment_count',
        ]


class LikeSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'user_username', 'post', 'post_title', 'created_at']
        read_only_fields = ['user', 'created_at']
