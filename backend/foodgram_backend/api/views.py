from rest_framework import mixins, status, viewsets
from recipes.models import (Recipe, Ingredient, Tag,
                            RecipeShoppingCart, ShoppingCart,
                            Follow, RecipeFavourite, Favourite)
from users.models import User
from .serializers import (IngridientGetSerializer, RecipeSerializer,
                          TagGetSerializer, TokenCreateSerializer,
                          UserSerializer, UserGetSerializer, FollowSerializer,
                          SubscriptionsSerializer, RecipesGetSerializer)
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework.decorators import action, api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from djoser.serializers import SetPasswordSerializer
from django.contrib.auth.hashers import make_password
from .permissions import UserPermission, IsAuthorOrReadOnlyPermission
from django.db.models import Sum
from .filters import RecipeFilter, IngredientFilter
import io
from django.utils.encoding import smart_str


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


class CreateDestroyViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass


class DestroyViewSet(
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    pass

# Создание пользователя, просмотр списка пользователей,
# просмотр личного профиля, смена пароля
class UserViewSet(CreateListRetrieveViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [UserPermission, ]


    @action(
        detail=False,
        methods=['GET',],
        permission_classes=[IsAuthenticated, ],
        url_path='me',
        url_name='my_profile'
    )
    def get_own_information(self, request):
        """Профиль пользователя."""
        serializer = UserGetSerializer(request.user,
                                            data=request.data)
        serializer.is_valid(raise_exception=True)
        # user = User.objects.get(username=request.user)
        return Response(serializer.data,
                            status=status.HTTP_200_OK)


    @action(
        detail=False,
        methods=['POST',],
        permission_classes=[IsAuthenticated, ],
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
        methods=['POST', 'DELETE',],
        permission_classes=[IsAuthenticated, ],
        url_path='subscribe',
        url_name='subscribe_or_unsubscribe'
    )
    def subscribe_or_unsubscribe(self, request, pk):
        """Подписывает на пользователя или удаляет подписку."""
        author = get_object_or_404(User, id=self.kwargs['pk'])
        follower = self.request.user
        if request.method == 'POST':
            data = {
                "author": author.id,
                "follower": follower.id
            }
            context = {
                "request": request,
            }
            serializer = FollowSerializer(
                data=data,
                context=context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            instance = Follow.objects.filter(author=author, follower=follower)
            if instance.exists():
                instance.delete()
                message = {'message': f'Вы отписались от пользователя {author}'}
                return Response(
                    message,
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'errors': f'Отписка невозможно, т.к. Вы не были подписаны на пользователя {author}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['GET',],
        permission_classes=[IsAuthenticated, ],
        url_path='subscriptions',
        url_name='my_subscriptions'
    )
    def my_subscriptions(self, request):
        """Просмотр личных подписок."""
        user = request.user
        get_path_to_media = request.build_absolute_uri('/media/')
        authors = User.objects.filter(following__follower=user)
        context = {"request": request, "get_path_to_media": get_path_to_media}
        print('type(authors) from view: ', type(authors))
        serializer = SubscriptionsSerializer(data=authors, context=context, many=True)
        serializer.is_valid()
        return Response(data=serializer.data,
                        status=status.HTTP_200_OK)


# Основной вьюсет по операциям с рецептами
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnlyPermission,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    
    @action(
        detail=True,
        methods=['POST', 'DELETE',],
        permission_classes=[IsAuthenticated, ],
        url_path='favorite',
        url_name='add_or_delete_favorite'
    )
    def add_or_delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        if request.method == 'POST':
            if Favourite.objects.filter(user=request.user, recipes=recipe).exists():
                return Response(
                    {'error': 'Данный рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            own_posted_recipes = request.user.recipes.all()
            if recipe in own_posted_recipes:
                return Response(
                    {'error': 'Зачем добавлять в избранное свой же рецепт? Отклонено.'},
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
            recipe_favorite = Favourite.objects.filter(user=request.user, recipes=recipe)
            if recipe_favorite.exists():
                recipe_favorite.delete()
                return Response(
                    {'message': 'Рецепт удален из избранного.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Данного рецепта нет в избранном. Удаление невозможно.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated, ],
        url_path='shopping_cart',
        url_name='add_or_delete_recipe_from_shopping_cart'
    )
    def add_or_delete_recipe_from_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipes=recipe).exists():
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
                user=request.user,recipes=recipe
            )
            if recipe_in_shopping_cart.exists():
                recipe_in_shopping_cart.delete()
                return Response(
                    {'message': 'Рецепт удален из корзины.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            return Response(
                {'error': 'Данного рецепта нет в корзине. Удаление невозможно.'},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action( 
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated, ],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart' 
    ) 
    def download_shopping_cart(self, request): 
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
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str('shopping_cart.txt')
        return response


# Получение списка или отдельного ингредиента
class IngredientViewSet(GetRetrieveViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngridientGetSerializer
    # filter_backends = (filters.SearchFilter, )
    # search_fields = ('^name',)
    filterset_class = IngredientFilter


# Получение списка или отдельного тега
class TagViewSet(GetRetrieveViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagGetSerializer


# НЕ ИСПОЛЬЗУЕТСЯ
# class ShoppingCartViewSet(viewsets.ModelViewSet):
#     serializer_class = ShoppingCartSerializer
#     queryset = ShoppingCart.objects.all()

#     def perform_create(self, serializer):
#         queryset = ShoppingCart.objects.filter(user=self.request.user)
#         recipe = get_object_or_404(Recipe, pk=self.kwargs['recipe_id'])
#         if queryset.exists():
#             return serializer.instance.queryset.add(recipes=recipe)
#         return serializer.save(recipes=recipe, user=self.request.user)


# Создание токена для пользователя
@api_view(["POST"])
def create_token(request):
    """Sending a token to verified user."""
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


# Удаление токена пользователя
@api_view(["POST"])
def detele_token(request):
    """Deleting a token for authenticated user."""
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
