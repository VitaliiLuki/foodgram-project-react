from django.contrib import admin
from recipes.models import (Favourite, Follow, Ingredient, IngredientRecipe,
                            Recipe, RecipeFavourite, RecipeShoppingCart,
                            ShoppingCart, Tag, TagRecipe)
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name')
    list_filter = ('email', 'username')
    empty_value_display = '-пусто-'


class IngredientInline(admin.TabularInline):
    model = Recipe.ingredients.through


class TagInline(admin.TabularInline):
    model = Recipe.tags.through


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name', 'favorite_count')
    list_filter = ('author', 'name', 'tags')
    empty_value_display = '-пусто-'
    inlines = [
        IngredientInline,
        TagInline,
    ]
    exclude = ('ingredients',)

    def favorite_count(self, obj):
        return RecipeFavourite.objects.filter(recipe=obj).count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'units')
    search_fields = ('name',)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ingredient_id', 'recipe_id', 'amount')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'hex_code', 'slug')


@admin.register(TagRecipe)
class TagRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag_id', 'recipe_id')


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'follower')


class RecipesInCartInline(admin.TabularInline):
    model = ShoppingCart.recipes.through


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user',)
    inlines = [
        RecipesInCartInline,
    ]


@admin.register(RecipeShoppingCart)
class RecipeShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('recipe_id', 'shopping_cart_id')


@admin.register(RecipeFavourite)
class RecipeFavouriteAdmin(admin.ModelAdmin):
    list_display = ('recipe_id', 'recipe', 'favourite_id', 'favourite')


class RecipesInline(admin.TabularInline):
    model = Favourite.recipes.through


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user', )
    inlines = [
        RecipesInline,
    ]
