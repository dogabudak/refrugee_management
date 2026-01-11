from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GameViewSet,
    WorldStateViewSet,
    PlayerViewSet,
    HexTileViewSet,
    CharacterViewSet,
    MapItemViewSet,
    InteractableViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'games', GameViewSet, basename='game')
router.register(r'world-states', WorldStateViewSet, basename='worldstate')
router.register(r'players', PlayerViewSet, basename='player')
router.register(r'hex-tiles', HexTileViewSet, basename='hextile')
router.register(r'characters', CharacterViewSet, basename='character')
router.register(r'map-items', MapItemViewSet, basename='mapitem')
router.register(r'interactables', InteractableViewSet, basename='interactable')

urlpatterns = [
    path('', include(router.urls)),
]
