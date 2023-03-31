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
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    pass


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
        url_path='me',
        url_name='my_profile'
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
        permission_classes=[IsAuthenticated],
        url_path='set_password',
        url_name='change_password'
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
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe_or_unsubscribe'
    )
    def subscribe_or_unsubscribe(self, request, pk):
        """Создание и удаление подписки на пользователя."""
        author = get_object_or_404(User, id=self.kwargs['pk'])
        follower = self.request.user
        follow_instance = Follow.objects.filter(author=author,
                                                follower=follower)
        if request.method == 'POST':
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
        else:
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

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions',
        url_name='my_subscriptions'
    )
    def my_subscriptions(self, request):
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

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='add_or_delete_favorite'
    )
    def add_or_delete_favorite(self, request, pk=None):
        """Добавление и удаление рецепта из избранного."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        favorite_instance = Favourite.objects.filter(user=request.user,
                                                     recipes=recipe)
        if request.method == 'POST':
            if favorite_instance.exists():
                return Response(
                    {'error': 'Данный рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite = Favourite.objects.create(user=request.user)
            favorite.recipes.add(recipe)
            favorite.save()
            if RecipeFavourite.objects.filter(recipe=recipe,
                                              favourite=favorite).exists():
                return Response(
                    RecipesGetSerializer(recipe).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Рецепт не удалось добавить в избранное.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            if favorite_instance.exists():
                favorite_instance.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Данного рецепта нет в избранном.'
                          'Удаление невозможно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='add_or_delete_recipe_from_shopping_cart'
    )
    def add_or_delete_recipe_from_shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта из корзины."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user,
                                           recipes=recipe).exists():
                return Response(
                    {'error': 'Данный рецепт уже добавлен в корзину.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_cart = ShoppingCart.objects.create(user=request.user)
            shopping_cart.recipes.add(recipe)
            shopping_cart.save()
            if RecipeShoppingCart.objects.filter(
                recipe=recipe,
                shopping_cart=shopping_cart
            ).exists():
                return Response(
                    RecipesGetSerializer(recipe).data,
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'error': 'Рецепт не удалось добавить в корзину.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        else:
            recipe_in_shopping_cart = ShoppingCart.objects.filter(
                user=request.user,
                recipes=recipe
            )
            if recipe_in_shopping_cart.exists():
                recipe_in_shopping_cart.delete()
                return Response(
                    {'message': 'Рецепт удален из корзины.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Данного рецепта нет в корзине.'
                          'Удаление невозможно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated],
        url_path='subscribe',
        url_name='subscribe_or_unsubscribe'
    )
    def subscribe_or_unsubscribe(self, request, pk):
        """Создание и удаление подписки на пользователя по id рецепта."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        author = recipe.author
        follower = self.request.user
        follow_instance = Follow.objects.filter(author=author,
                                                follower=follower)
        if request.method == 'POST':
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

        elif request.method == 'DELETE':
            if follow_instance.exists():
                follow_instance.delete()
                message = {
                    'message': f'Вы отписались от пользователя {author}'
                }
                return Response(
                    message,
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'errors': 'Отписка невозможна. '
                           f'Вы не были подписаны на пользователя {author}'},
                status=status.HTTP_400_BAD_REQUEST
            )


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
