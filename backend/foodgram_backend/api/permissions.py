from rest_framework import permissions


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    """
    Permissions: 
    Get list, retrieve for all users, create for authenticated, 
    patch or delete for author.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated
        else:
            return True

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)