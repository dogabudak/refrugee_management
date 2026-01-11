from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import (
    Game,
    WorldState,
    Player,
    HexTile,
    Character,
    MapItem,
    Interactable,
)
from .serializers import (
    GameListSerializer,
    GameDetailSerializer,
    GameCreateSerializer,
    WorldStateSerializer,
    WorldStateListSerializer,
    PlayerListSerializer,
    PlayerDetailSerializer,
    PlayerCreateSerializer,
    HexTileSerializer,
    HexTileListSerializer,
    CharacterListSerializer,
    CharacterDetailSerializer,
    CharacterCreateSerializer,
    CharacterUpdateSerializer,
    MapItemSerializer,
    MapItemCreateSerializer,
    MapItemListSerializer,
    InteractableSerializer,
    InteractableCreateSerializer,
    InteractableListSerializer,
)


# ============================================================================
# Game ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List all games", tags=["Games"]),
    retrieve=extend_schema(description="Get game details", tags=["Games"]),
    create=extend_schema(description="Create a new game", tags=["Games"]),
    update=extend_schema(description="Update a game", tags=["Games"]),
    partial_update=extend_schema(description="Partially update a game", tags=["Games"]),
    destroy=extend_schema(description="Delete a game", tags=["Games"]),
)
class GameViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing games.
    """
    queryset = Game.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return GameListSerializer
        elif self.action == 'create':
            return GameCreateSerializer
        return GameDetailSerializer

    @extend_schema(
        description="Get current world state for a game",
        tags=["Games"],
        responses={200: WorldStateSerializer}
    )
    @action(detail=True, methods=['get'])
    def current_state(self, request, pk=None):
        """Get the current world state for this game."""
        game = self.get_object()
        world_state = game.world_states.filter(is_current=True).first()
        if not world_state:
            return Response(
                {"error": "No current world state found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = WorldStateSerializer(world_state)
        return Response(serializer.data)

    @extend_schema(
        description="Start a game",
        tags=["Games"],
        responses={200: GameDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start a game."""
        game = self.get_object()
        if game.status != 'waiting':
            return Response(
                {"error": "Game must be in 'waiting' status to start"},
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils.timezone import now
        game.status = 'active'
        game.started_at = now()
        game.save()

        serializer = self.get_serializer(game)
        return Response(serializer.data)


# ============================================================================
# WorldState ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List world states", tags=["World States"]),
    retrieve=extend_schema(description="Get world state details", tags=["World States"]),
)
class WorldStateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing world state snapshots.
    Read-only as world states should be created by game logic.
    """
    queryset = WorldState.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return WorldStateListSerializer
        return WorldStateSerializer

    def get_queryset(self):
        queryset = WorldState.objects.all()
        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)
        return queryset.order_by('-tick')


# ============================================================================
# Player ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List players", tags=["Players"]),
    retrieve=extend_schema(description="Get player details", tags=["Players"]),
    create=extend_schema(description="Join a game as a player", tags=["Players"]),
    update=extend_schema(description="Update player info", tags=["Players"]),
    partial_update=extend_schema(description="Partially update player info", tags=["Players"]),
)
class PlayerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing players.
    """
    queryset = Player.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return PlayerListSerializer
        elif self.action == 'create':
            return PlayerCreateSerializer
        return PlayerDetailSerializer

    def get_queryset(self):
        queryset = Player.objects.all()
        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)
        return queryset

    def perform_create(self, serializer):
        """Set the current user as the player's user."""
        serializer.save(user=self.request.user)


# ============================================================================
# HexTile ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List hex tiles", tags=["Map"]),
    retrieve=extend_schema(description="Get hex tile details", tags=["Map"]),
    create=extend_schema(description="Create a hex tile", tags=["Map"]),
    update=extend_schema(description="Update a hex tile", tags=["Map"]),
    partial_update=extend_schema(description="Partially update a hex tile", tags=["Map"]),
)
class HexTileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing hex tiles on the game map.
    """
    queryset = HexTile.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return HexTileListSerializer
        return HexTileSerializer

    def get_queryset(self):
        queryset = HexTile.objects.all()
        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)

        # Filter by terrain type
        terrain = self.request.query_params.get('terrain', None)
        if terrain:
            queryset = queryset.filter(terrain_type=terrain)

        # Filter by coordinates (for nearby tiles)
        q = self.request.query_params.get('q', None)
        r = self.request.query_params.get('r', None)
        if q is not None and r is not None:
            # Return exact tile
            queryset = queryset.filter(q=q, r=r)

        return queryset

    @extend_schema(
        description="Get tiles in a radius around a coordinate",
        tags=["Map"],
        responses={200: HexTileListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get tiles within a certain radius of a coordinate."""
        game_id = request.query_params.get('game')
        q = request.query_params.get('q')
        r = request.query_params.get('r')
        radius = int(request.query_params.get('radius', 1))

        if not all([game_id, q is not None, r is not None]):
            return Response(
                {"error": "game, q, and r parameters are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        q, r = int(q), int(r)

        # Simple radius filter (could be optimized with proper hex distance calculation)
        tiles = HexTile.objects.filter(
            game_id=game_id,
            q__gte=q - radius,
            q__lte=q + radius,
            r__gte=r - radius,
            r__lte=r + radius
        )

        serializer = HexTileListSerializer(tiles, many=True)
        return Response(serializer.data)


# ============================================================================
# Character ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List characters", tags=["Characters"]),
    retrieve=extend_schema(description="Get character details", tags=["Characters"]),
    create=extend_schema(description="Create a new character", tags=["Characters"]),
    update=extend_schema(description="Update a character", tags=["Characters"]),
    partial_update=extend_schema(description="Partially update a character", tags=["Characters"]),
)
class CharacterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing characters.
    """
    queryset = Character.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CharacterListSerializer
        elif self.action == 'create':
            return CharacterCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CharacterUpdateSerializer
        return CharacterDetailSerializer

    def get_queryset(self):
        queryset = Character.objects.exclude(status='dead')

        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)

        owner_id = self.request.query_params.get('owner', None)
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        # Filter by position
        q = self.request.query_params.get('q', None)
        r = self.request.query_params.get('r', None)
        if q is not None and r is not None:
            queryset = queryset.filter(position_q=q, position_r=r)

        return queryset

    @extend_schema(
        description="Move character to a new position",
        tags=["Characters"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'q': {'type': 'integer'},
                    'r': {'type': 'integer'}
                },
                'required': ['q', 'r']
            }
        },
        responses={200: CharacterDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move a character to a new position."""
        character = self.get_object()
        q = request.data.get('q')
        r = request.data.get('r')

        if q is None or r is None:
            return Response(
                {"error": "q and r coordinates are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate tile exists and is passable
        tile = HexTile.objects.filter(
            game=character.game,
            q=q,
            r=r
        ).first()

        if not tile:
            return Response(
                {"error": "Invalid tile coordinates"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not tile.is_passable:
            return Response(
                {"error": "Tile is not passable"},
                status=status.HTTP_400_BAD_REQUEST
            )

        character.position_q = q
        character.position_r = r
        character.status = 'idle'
        character.save()

        serializer = CharacterDetailSerializer(character)
        return Response(serializer.data)

    @extend_schema(
        description="Loot an item at character's position",
        tags=["Characters"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'item_id': {'type': 'integer'}
                },
                'required': ['item_id']
            }
        },
        responses={200: CharacterDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def loot(self, request, pk=None):
        """Loot an item from the map."""
        character = self.get_object()
        item_id = request.data.get('item_id')

        if not item_id:
            return Response(
                {"error": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find item at character's position
        map_item = MapItem.objects.filter(
            id=item_id,
            game=character.game,
            position_q=character.position_q,
            position_r=character.position_r,
            is_available=True
        ).first()

        if not map_item:
            return Response(
                {"error": "Item not found at this position"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Add to inventory (simplified - should check capacity)
        from django.utils.timezone import now
        character.inventory.append({
            'item_id': map_item.item_id,
            'item_type': map_item.item_type,
            'quantity': map_item.quantity,
            'looted_at': now().isoformat()
        })
        character.save()

        # Mark item as collected
        map_item.is_available = False
        map_item.collected_at = now()
        map_item.collected_by = character
        map_item.save()

        serializer = CharacterDetailSerializer(character)
        return Response(serializer.data)


# ============================================================================
# MapItem ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List map items", tags=["Map Items"]),
    retrieve=extend_schema(description="Get map item details", tags=["Map Items"]),
    create=extend_schema(description="Spawn a map item", tags=["Map Items"]),
    update=extend_schema(description="Update a map item", tags=["Map Items"]),
    partial_update=extend_schema(description="Partially update a map item", tags=["Map Items"]),
)
class MapItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing map items (loot).
    """
    queryset = MapItem.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return MapItemListSerializer
        elif self.action == 'create':
            return MapItemCreateSerializer
        return MapItemSerializer

    def get_queryset(self):
        queryset = MapItem.objects.all()

        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)

        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available is not None:
            queryset = queryset.filter(is_available=available.lower() == 'true')

        # Filter by position
        q = self.request.query_params.get('q', None)
        r = self.request.query_params.get('r', None)
        if q is not None and r is not None:
            queryset = queryset.filter(position_q=q, position_r=r)

        return queryset


# ============================================================================
# Interactable ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List interactable objects", tags=["Interactables"]),
    retrieve=extend_schema(description="Get interactable details", tags=["Interactables"]),
    create=extend_schema(description="Create an interactable object", tags=["Interactables"]),
    update=extend_schema(description="Update an interactable object", tags=["Interactables"]),
    partial_update=extend_schema(description="Partially update an interactable object", tags=["Interactables"]),
)
class InteractableViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing interactable objects.
    """
    queryset = Interactable.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return InteractableListSerializer
        elif self.action == 'create':
            return InteractableCreateSerializer
        return InteractableSerializer

    def get_queryset(self):
        queryset = Interactable.objects.all()

        game_id = self.request.query_params.get('game', None)
        if game_id:
            queryset = queryset.filter(game_id=game_id)

        # Filter by active status
        active = self.request.query_params.get('active', None)
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() == 'true')

        # Filter by position
        q = self.request.query_params.get('q', None)
        r = self.request.query_params.get('r', None)
        if q is not None and r is not None:
            queryset = queryset.filter(position_q=q, position_r=r)

        return queryset

    @extend_schema(
        description="Interact with an object",
        tags=["Interactables"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'character_id': {'type': 'integer'}
                },
                'required': ['character_id']
            }
        },
        responses={200: InteractableSerializer}
    )
    @action(detail=True, methods=['post'])
    def interact(self, request, pk=None):
        """Interact with this object using a character."""
        interactable = self.get_object()
        character_id = request.data.get('character_id')

        if not character_id:
            return Response(
                {"error": "character_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        character = get_object_or_404(Character, id=character_id, game=interactable.game)

        # Check if character is at the same position
        if character.position_q != interactable.position_q or character.position_r != interactable.position_r:
            return Response(
                {"error": "Character must be at the same position as the interactable"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if can use
        if not interactable.is_active:
            return Response(
                {"error": "Interactable is not active"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if interactable.max_uses > 0 and interactable.current_uses >= interactable.max_uses:
            return Response(
                {"error": "Interactable has been used maximum times"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Process interaction (simplified)
        interactable.current_uses += 1
        interactable.last_used_tick = interactable.game.current_tick

        # Add interaction to history
        from django.utils.timezone import now
        interactable.interactions.append({
            'character_id': character.id,
            'character_name': character.name,
            'tick': interactable.game.current_tick,
            'timestamp': now().isoformat(),
            'result': 'success'
        })

        interactable.save()

        serializer = InteractableSerializer(interactable)
        return Response(serializer.data)
