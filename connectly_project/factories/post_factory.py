from posts.models import Post


class PostFactory:
    @staticmethod
    def create_post(post_type, title, content='', metadata=None, author=None):
        """
        Factory method to create posts with validation.
        
        Args:
            post_type: Type of post (text, image, video)
            title: Title of the post
            content: Content of the post (optional)
            metadata: Dictionary containing post metadata (optional)
            author: User instance who is creating the post (optional)
            
        Returns:
            Post: Created Post instance
            
        Raises:
            ValueError: If post_type is invalid or required metadata is missing
        """
        if metadata is None:
            metadata = {}
        
        # Validate metadata is a dictionary
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a JSON object (dictionary)")
        
        # Validate title length (max_length=255 in model)
        if len(title) > 255:
            raise ValueError("Title cannot exceed 255 characters")
            
        if post_type not in dict(Post.POST_TYPES):
            raise ValueError("Invalid post type")

        # Validate type-specific requirements
        if post_type == 'image' and 'file_size' not in metadata:
            raise ValueError("Image posts require 'file_size' in metadata")
        if post_type == 'video' and 'duration' not in metadata:
            raise ValueError("Video posts require 'duration' in metadata")

        return Post.objects.create(
            title=title,
            content=content,
            post_type=post_type,
            metadata=metadata,
            author=author
        )
