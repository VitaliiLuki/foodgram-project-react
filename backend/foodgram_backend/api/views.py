import io

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_str
from djoser.serializers import SetPasswordSerializer
from recipes.models import (Favourite, Follow, Ingredient, Recipe,
                            RecipeFavourite, RecipeShoppingCart, ShoppingCart,
                            Tag)
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User

from .filters import IngredientFilter, RecipeFilter
from .pagination import SubscriptionPagination
from .permissions import AuthorOrReadOnly
from .serializers import (FollowSerializer, IngridientGetSerializer,
                          RecipeSerializer, RecipesGetSerializer,
                          SubscriptionsSerializer, TagGetSerializer,
                          TokenCreateSerializer, UserGetSerializer,
                          UserSerializer)


class GetRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    pass


class CreateListRetrieveViewSet(
    GetRetrieveViewSet,
    mixins.CreateModelMixin
):
    pass


def add_subscription(author, follower, follow_instance):
    """
    Создает экземпляр модели Follow с атрибутами author и follower.
    """
    if author == follower:
        return Response(
            'Подписка на себя невозможна.',
            status=status.HTTP_400_BAD_REQUEST
        )
    if follow_instance.exists():
        return Response(
            f'Вы уже подписаны на автора с username {author}.',
            status=status.HTTP_400_BAD_REQUEST
        )
    follow_obj = Follow.objects.create(author=author,
                                       follower=follower)
    follow_obj.save()
    serializer = FollowSerializer(follow_obj)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


def destroy_subscription(author, follow_instance):
    """Удаляет экземпрял модели Follow."""
    if follow_instance.exists():
        follow_instance.delete()
        message = f'Вы отписались от пользователя {author}'
        return Response(
            message,
            status=status.HTTP_204_NO_CONTENT
        )
    return Response(
        {'errors': 'Отписка невозможна.'
                   f'Вы не были подписаны на пользователя {author}'},
        status=status.HTTP_400_BAD_REQUEST
    )


def get_follow_objcs(request, author):
    """
    Возвращает follower - экземпляр модели User
    и экземпляр модели Follow.
    """
    follower = request.user
    follow_instance = Follow.objects.filter(author=author,
                                            follower=follower)
    return follower, follow_instance


class UserViewSet(CreateListRetrieveViewSet):
    """
    Создание пользователя, просмотр списка или
    информации об отдельном пользователе.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def get_own_information(self, request):
        """Профиль пользователя."""
        serializer = UserGetSerializer(request.user,
                                       context={'request': request})
        return Response(serializer.data,
                        status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        """Смена пароля."""
        serializer = SetPasswordSerializer(
            context={'request': request},
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(username=request.user)
        user.set_password(serializer.validated_data.get('new_password'))
        user.save()
        return Response(data='Пароль успешно изменен',
                        status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """Создание подписки на пользователя."""
        author = get_object_or_404(User, id=self.kwargs['pk'])
        follower, follow_instance = get_follow_objcs(request, author)
        return add_subscription(author, follower, follow_instance)

    @subscribe.mapping.delete
    def del_subscribe(self, request, pk):
        """Удаляет подписку на пользователя."""
        author = get_object_or_404(User, id=self.kwargs['pk'])
        _, follow_instance = get_follow_objcs(request, author)
        return destroy_subscription(author, follow_instance)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Просмотр личных подписок."""
        authors = User.objects.filter(following__follower=request.user)
        context = {"request": request}
        paginator = SubscriptionPagination()
        page = paginator.paginate_queryset(authors, request)
        serializer = SubscriptionsSerializer(page, context=context, many=True)
        return paginator.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Создание рецепта, просмотр списка или отдельного рецепта."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [AuthorOrReadOnly]
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def add_obj(self, request, model, through_model):
        """
        Создание экземпляра Favorite или ShoppinCart.
        Атрибуты:
        request - объект запроса;
        model - экземпляр модели Favorite или ShoppingCart
                в зависимости от view-функции;
        through_model - промежуточная модель RecipeFavourite или
                        RecipeShoppingCart в зависимости от view-функции.
        """
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])

        if model.objects.filter(user=request.user,
                                recipes=recipe).exists():
            return Response(
                {'error': 'Данный рецепт уже добавлен.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_instance = model.objects.create(user=request.user)
        model_instance.recipes.add(recipe)
        model_instance.save()

        instance_data = (
            {'shopping_cart': model_instance} if model is ShoppingCart
            else {'favourite': model_instance}
        )
        if through_model.objects.filter(
            recipe=recipe,
            **instance_data
        ).exists():
            return Response(
                RecipesGetSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            {'error': 'Рецепт не удалось добавить.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    def del_obj(self, request, model):
        """Удаляет экземляр модели Favorite или ShoppinCart."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        model_instance = model.objects.filter(user=request.user,
                                              recipes=recipe)
        model_dependent_words = (
            ['корзины', 'корзине'] if model is ShoppingCart else
            ['избранного', 'избранном']
        )
        if model_instance.exists():
            model_instance.delete()
            return Response(
                {
                    'message': (
                        f'Рецепт успешно удален из {model_dependent_words[0]}.'
                    )
                },
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'error': f'Данного рецепта нет в {model_dependent_words[-1]}. '
                      'Удаление невозможно.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавление рецепта в избранное."""
        return self.add_obj(request, Favourite, RecipeFavourite)

    @favorite.mapping.delete
    def del_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        return self.del_obj(request, Favourite)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        return self.add_obj(request, ShoppingCart, RecipeShoppingCart)

    @shopping_cart.mapping.delete
    def del_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        return self.del_obj(request, ShoppingCart)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        """Выгрузка списка ингредиентов из добавленных в корзину рецептов."""
        recipes_query = Recipe.objects.filter(
            shoppingcart__user=self.request.user
        ).all()
        ingredients_query = (
            recipes_query.values(
                "ingredient_recipe__ingredient__name",
                "ingredient_recipe__ingredient__units",
            )
            .annotate(amount=Sum("ingredient_recipe__amount"))
            .order_by()
        )
        text = "\n".join(
            [
                f"{item['ingredient_recipe__ingredient__name']}: "
                f"({item['ingredient_recipe__ingredient__units']})"
                f" - {item['amount']}, "
                for item in ingredients_query
            ]
        )
        buffer = io.BytesIO()
        buffer.write(text.encode())
        response = HttpResponse(buffer.getvalue(), content_type="text/plain")
        filename = 'shopping_cart.txt'
        response['Content-Disposition'] = (
            f'attachment; filename={smart_str(filename)}'
        )
        return response

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk):
        """Создание подписки на пользователя по id рецепта."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        author = recipe.author
        follower, follow_instance = get_follow_objcs(request, author)
        return add_subscription(author, follower, follow_instance)

    @subscribe.mapping.delete
    def del_subscribe(self, request, pk):
        """Удаление подписки на пользователя по id рецепта."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        author = recipe.author
        _, follow_instance = get_follow_objcs(request, author)
        return destroy_subscription(author, follow_instance)


class IngredientViewSet(GetRetrieveViewSet):
    """Получение списка ингредиентов или отдельного ингредиента."""
    queryset = Ingredient.objects.all()
    serializer_class = IngridientGetSerializer
    pagination_class = None
    filterset_class = IngredientFilter


class TagViewSet(GetRetrieveViewSet):
    """Получение списка тегов или отдельного тега."""
    queryset = Tag.objects.all()
    serializer_class = TagGetSerializer
    pagination_class = None


@api_view(["POST"])
def create_token(request):
    """Создание токена для зарегистрированного пользователя."""
    serializer = TokenCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = User.objects.get(
            email=serializer.data['email']
        )
        if user.check_password(serializer.data['password']):
            token = Token.objects.get_or_create(user=user)
            tocken_resp = list(map(str, token))[0]
            return Response(
                {'auth_token': tocken_resp},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': 'Неверный пароль.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'Пользователь с указанными данными не зарегистрирован.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(["POST"])
def detele_token(request):
    """Удаление токена."""
    try:
        auth_token = request.auth
        token = Token.objects.get(key=auth_token)
        if auth_token == token:
            token.delete()
            return Response(data='null', status=status.HTTP_204_NO_CONTENT)
        response = {"detail": "Невалидный токен"}
        return Response(data=response, status=status.HTTP_400_BAD_REQUEST)
    except Token.DoesNotExist:
        response = {"detail": "Учетные данные не были предоставлены."}
        return Response(
            data=response,
            status=status.HTTP_401_UNAUTHORIZED
        )
