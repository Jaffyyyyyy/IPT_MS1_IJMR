from rest_framework.permissions import BasePermission


class IsPostAuthor(BasePermission):
    """
    Custom permission to only allow authors of a post to access it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
