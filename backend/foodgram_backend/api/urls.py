from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (RecipeViewSet, IngredientViewSet,
                    TagViewSet, create_token,
                    detele_token, UserViewSet)


app_name = 'api'

router_v1 = DefaultRouter()

router_v1.register('recipes', RecipeViewSet, basename='recipe')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('users', UserViewSet, basename='user')


urlpatterns = [
    path('', include(router_v1.urls)),
    path('auth/token/login/', create_token),
    path('auth/token/logout/', detele_token),
]
