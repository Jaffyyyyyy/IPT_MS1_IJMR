<<<<<<< HEAD
from rest_framework import permissions

class IsPostAuthor(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the author of the post.
        return obj.author == request.user
=======
from rest_framework.permissions import BasePermission


class IsPostAuthor(BasePermission):
    """
    Permission check that compares post author username with authenticated user.
    Note: Post.author is posts.User model, request.user is auth.User model.
    """
    def has_object_permission(self, request, view, obj):
        # Compare usernames since Post.author is custom User model
        # and request.user is Django's auth User model
        return obj.author.username == request.user.username
>>>>>>> mainrepo/master
