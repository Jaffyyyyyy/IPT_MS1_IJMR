from posts.models import Post

class PostFactory:
    @staticmethod
    def create_post(post_type, title, content='', metadata=None, author=None):
        # Initialize metadata safely
        if metadata is None:
            metadata = {}
    
        valid_post_types = [choice[0] for choice in Post.POST_TYPES]
        if post_type not in valid_post_types:
            allowed = ", ".join(valid_post_types)
            raise ValueError(f"Invalid post type: {post_type}. Valid types are {', '.join(valid_post_types)}")
        
        if post_type == 'image' and 'file_size' not in metadata:
            raise ValueError("Image posts require 'file_size' in metadata")
        
        if post_type == 'video' and 'duration' not in metadata:
            raise ValueError("Video posts require 'duration' in metadata")
        
        return Post.objects.create( # type: ignore
            post_type=post_type,
            title=title,
            content=content,
            metadata=metadata,
            author=author
        )