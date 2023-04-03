import base64

from django.contrib.auth.hashers import make_password
from django.core.files.base import ContentFile
from recipes.models import (Favourite, Follow, Ingredient, IngredientRecipe,
                            Recipe, ShoppingCart, Tag, TagRecipe)
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField
from users.models import User


class Base64ImageField(serializers.ImageField):
    """Сериализатор для декодирования картинок"""
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class IngridientGetSerializer(serializers.ModelSerializer):
    """Сериализатор для гет запросов по ингредиентам."""
    measurement_unit = serializers.CharField(source='units')

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit',)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    """
    Вспомогательный сериализатор для создания рецептов.
    В Post-запросе передается пара ingredient/amount.
    """
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id',
        queryset=Ingredient.objects.all()
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.units',
        read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class TagGetSerializer(serializers.ModelSerializer):
    """
    Сериализатор для получения списка тегов или информации
    по конкретному тегу.
    """
    color = serializers.CharField(source='hex_code')

    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')
        read_only_fields = ('name', 'color', 'slug',)


class RecipesGetSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания пользователя,
    просмотра списка или отдельного пользователя
    """
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipesGetSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password',
                  'is_subscribed',
                  'recipes')
        read_only_fields = ('id', 'is_subscribed', 'recipes')

    def get_is_subscribed(self, author):
        follower = self.context['view'].request.user
        if follower.is_anonymous:
            return False
        return Follow.objects.filter(author=author, follower=follower).exists()

    def create(self, validated_data):
        password = validated_data.pop('password')
        hash_password = make_password(password)
        user = User.objects.create(**validated_data, password=hash_password)
        return user

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response.pop('password', None)
        return response


class UserGetSerializer(serializers.ModelSerializer):
    """Вспомогательный сериализатор для гет запросов."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, object):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            author=object,
            follower=user
        ).exists()


class TokenCreateSerializer(serializers.Serializer):
    """
    Сериализатор для валидации данных, предоставленных пользователем
    для получения токена.
    """

    email = serializers.EmailField(
        required=True
    )

    password = serializers.CharField(
        max_length=150,
        required=True
    )

    class Meta:
        fields = ('email', 'password',)


class RecipeSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор рецептов.
    Создание и обновление рецепта,
    просмотр списка или конкретного рецепта.
    """
    author = UserGetSerializer(read_only=True)
    tags = SlugRelatedField(queryset=Tag.objects.all(),
                            slug_field='id',
                            many=True)
    ingredients = IngredientRecipeSerializer(
        source='ingredient_recipe',
        many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'is_favorited',
                  'is_in_shopping_cart',
                  'name',
                  'image',
                  'text',
                  'cooking_time')

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return Favourite.objects.filter(recipes=obj, user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(recipes=obj, user=user).exists()

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredient_recipe')
        recipe = Recipe.objects.create(**validated_data)
        for tag in tags:
            current_tag = Tag.objects.get(id=tag.id)
            TagRecipe.objects.create(
                tag=current_tag,
                recipe=recipe
            )
        for ingredient in ingredients:
            ingr_instance = ingredient['ingredient']['id']
            IngredientRecipe.objects.create(
                recipe=recipe,
                ingredient=ingr_instance,
                amount=ingredient.get('amount')
            )
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)

        if 'ingredient_recipe' in validated_data:
            instance.ingredient_recipe.all().delete()
            ingredients_data = validated_data.pop('ingredient_recipe')
            for ingedient in ingredients_data:
                ingedient_instance = ingedient['ingredient']['id']
                ingredient_amount = ingedient['amount']
                IngredientRecipe.objects.create(
                    recipe=instance,
                    ingredient=ingedient_instance,
                    amount=ingredient_amount
                )
        instance.save()
        return instance

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['tags'] = TagGetSerializer(
            instance.tags.all(),
            many=True
        ).data
        return response

    def validate_ingredients(self, ingredients):
        if not len(ingredients):
            raise serializers.ValidationError('Добавьте хотя бы 1 ингредиент!')
        ingr_set = set()
        for ingredient in ingredients:
            ingr_set.add(ingredient['ingredient']['id'])
        if len(ingredients) != len(ingr_set):
            raise serializers.ValidationError(
                'Все ингредиенты должны быть уникальны!'
            )
        return ingredients

    def validate_tags(self, tags):
        tags_set = set()
        for tag in tags:
            tags_set.add(tag)
        if len(tags) != len(tags_set):
            raise serializers.ValidationError(
                'Все теги должны быть уникальны!'
            )
        return tags


class SubscriptionsSerializer(serializers.ModelSerializer):
    """Сериализатор подписок."""

    DEFAULT_LIMIT = 3

    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipesGetSerializer(many=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count')

    def get_is_subscribed(self, obj):
        me = self.context['request'].user
        return Follow.objects.filter(author=obj, follower=me).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.all().count()

    def to_representation(self, instance):
        response = super().to_representation(instance)
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', self.DEFAULT_LIMIT)
        response['recipes'] = response['recipes'][:int(limit)]
        return response


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки."""
    email = serializers.EmailField(source='author.email',
                                   read_only=True)
    id = serializers.IntegerField(source='author.id',
                                  read_only=True)
    username = serializers.CharField(source='author.username',
                                     read_only=True)
    first_name = serializers.CharField(source='author.first_name',
                                       read_only=True)
    last_name = serializers.CharField(source='author.last_name',
                                      read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = RecipesGetSerializer(source='author.recipes',
                                   many=True,
                                   read_only=True)
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('author',
                  'follower',
                  'email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count'
                  )

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response.pop('author')
        response.pop('follower')
        return response

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            author=obj.author,
            follower=obj.follower
        ).exists()

    def get_recipes_count(self, obj):
        return len(obj.author.recipes.all())
