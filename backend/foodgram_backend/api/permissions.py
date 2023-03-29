from rest_framework import permissions


class IsAuthorOrReadOnlyPermission(permissions.BasePermission):
    """
    Разрешения:
    Просмотр списка и детальной информации рецептов -
    для всех пользовательских ролей,
    Создание рецепта для аутентифицированных пользователей,
    удаление и обновление - только для атора.
    """

    def has_permission(self, request, view):
        if view.action == 'create':
            return request.user.is_authenticated
        else:
            return True

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
