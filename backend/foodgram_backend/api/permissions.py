from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешения:
    Просмотр списка и детальной информации рецептов -
    для всех пользовательских ролей,
    Создание рецепта для аутентифицированных пользователей,
    удаление и обновление - только для атора.
    """

    def has_permission(self, request, view):
        print(view)
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)
