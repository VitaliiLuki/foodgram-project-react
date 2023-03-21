from django.db import models
from users.models import User


class Recipe(models.Model):
    """Creates and save recipe data."""

    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='recipes')
    ingredients = models.ManyToManyField('Ingredient',
                                         through='IngredientRecipe',
                                         db_index=True)
    tags = models.ManyToManyField('Tag', through='TagRecipe')
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None
    )
    name = models.CharField(max_length=200)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField()
    publication_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-publication_date']

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Create and saves ingridient's data."""
    name = models.CharField(max_length=200)
    units = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    """Contains information btw recipe and ingredient."""
    ingredient = models.ForeignKey(Ingredient, related_name='ingredient_recipe', on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, related_name='ingredient_recipe', on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()

    def __str__(self):
        return f'{self.amount}'


class Tag(models.Model):
    """Tags for recipes."""
    name = models.CharField(max_length=200)
    hex_code = models.CharField(max_length=10)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['slug']


class TagRecipe(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)


class Follow(models.Model):
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='following')
    follower = models.ForeignKey(User,
                                 on_delete=models.CASCADE,
                                 related_name='follower')


class Favourite(models.Model):
    recipes = models.ManyToManyField(Recipe, through='RecipeFavourite')
    user = models.ForeignKey(User,
                             related_name='favourites',
                             on_delete=models.CASCADE)


class RecipeFavourite(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    favourite = models.ForeignKey(Favourite, on_delete=models.CASCADE)


class ShoppingCart(models.Model):
    recipes = models.ManyToManyField(Recipe, through='RecipeShoppingCart')
    user = models.ForeignKey(User,
                             related_name='ingredients',
                             on_delete=models.CASCADE)


class RecipeShoppingCart(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    shopping_cart = models.ForeignKey(ShoppingCart,
                                         on_delete=models.CASCADE)
