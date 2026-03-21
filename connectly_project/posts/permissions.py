from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPostAuthor(BasePermission):
    """
    Object-level: only the post author may write/delete.
    Any authenticated user may read.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user


class IsAdminRole(BasePermission):
    """
    Permits all methods only to users whose role == 'admin'.
    Non-admin authenticated users → 403.
    Unauthenticated users → 401.
    """
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsAdminOrAuthor(BasePermission):
    """
    Object-level: admins may perform any action.
    Non-admins may only act on objects they authored.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.role == 'admin':
            return True
        return obj.author == request.user


class IsNotGuest(BasePermission):
    """
    Blocks write actions for guest users.
    Guests may still read (GET/HEAD/OPTIONS).
    """
    message = 'Guest users do not have write access.'

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role != 'guest'


class IsAdminOrReadOnly(BasePermission):
    """
    Allows full access to admin-role users.
    Regular authenticated users get read-only access.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')



