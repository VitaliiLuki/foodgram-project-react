# from django_filters import rest_framework as filters
import django_filters

from recipes.models import Recipe, Tag, Ingredient

class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        return Ingredient.objects.filter(name__icontains=value)

    @classmethod
    def get_search_fields(cls, request):
        return ['name']


class RecipeFilter(django_filters.FilterSet):
    """
    Gives an option to filtrate the fields below when you make a get-request 
    to find a recipe which matches to your search.
    """
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = django_filters.CharFilter(field_name='author__username')
    is_favorited = django_filters.CharFilter(method='get_is_favorited')
    is_in_shopping_cart = django_filters.CharFilter(method='get_is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
        # fields = ['tags', 'author']


    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(favourite__user=user)
        return Recipe.objects.all()

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value:
            return Recipe.objects.filter(shoppingcart__user=user)
        return Recipe.objects.all()
