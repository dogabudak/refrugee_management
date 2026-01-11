from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Game,
    WorldState,
    Player,
    HexTile,
    Character,
    MapItem,
    Interactable,
)


# ============================================================================
# User Serializers
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


# ============================================================================
# Game Serializers
# ============================================================================

class GameListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for game list views."""

    player_count = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'name', 'status', 'max_players', 'player_count',
            'current_tick', 'tick_duration_minutes', 'map_name',
            'started_at', 'next_tick_at', 'created_at'
        ]
        read_only_fields = ['id', 'current_tick', 'created_at']

    def get_player_count(self, obj):
        """Get current number of players in the game."""
        return obj.players.filter(is_active=True).count()


class GameDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for game detail views."""

    player_count = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'name', 'status', 'max_players', 'player_count',
            'current_tick', 'tick_duration_minutes', 'map_name',
            'map_width', 'map_height', 'settings',
            'started_at', 'next_tick_at', 'finished_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'current_tick', 'created_at', 'updated_at']

    def get_player_count(self, obj):
        """Get current number of players in the game."""
        return obj.players.filter(is_active=True).count()


class GameCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new games."""

    class Meta:
        model = Game
        fields = [
            'name', 'max_players', 'tick_duration_minutes',
            'map_name', 'map_width', 'map_height', 'settings'
        ]

    def validate_tick_duration_minutes(self, value):
        """Validate tick duration is reasonable."""
        if value < 1:
            raise serializers.ValidationError("Tick duration must be at least 1 minute")
        if value > 1440:  # 24 hours
            raise serializers.ValidationError("Tick duration cannot exceed 1440 minutes (24 hours)")
        return value

    def validate_map_width(self, value):
        """Validate map width."""
        if value < 10 or value > 200:
            raise serializers.ValidationError("Map width must be between 10 and 200")
        return value

    def validate_map_height(self, value):
        """Validate map height."""
        if value < 10 or value > 200:
            raise serializers.ValidationError("Map height must be between 10 and 200")
        return value


# ============================================================================
# WorldState Serializers
# ============================================================================

class WorldStateSerializer(serializers.ModelSerializer):
    """Serializer for WorldState snapshots."""

    class Meta:
        model = WorldState
        fields = [
            'id', 'game', 'tick', 'state_snapshot', 'is_current',
            'active_players', 'total_characters', 'commands_processed',
            'state_hash', 'events', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'state_hash', 'is_current'
        ]


class WorldStateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for world state list views."""

    class Meta:
        model = WorldState
        fields = [
            'id', 'game', 'tick', 'is_current',
            'active_players', 'total_characters', 'commands_processed',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================================
# Player Serializers
# ============================================================================

class PlayerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for player list views."""

    user = UserSerializer(read_only=True)
    character_count = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'game', 'user', 'player_name', 'color', 'avatar',
            'is_active', 'is_ai', 'score', 'character_count',
            'joined_at', 'last_active_at'
        ]
        read_only_fields = ['id', 'joined_at', 'last_active_at']

    def get_character_count(self, obj):
        """Get number of characters owned by player."""
        return obj.characters.exclude(status='dead').count()


class PlayerDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for player detail views."""

    user = UserSerializer(read_only=True)
    character_count = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = [
            'id', 'game', 'user', 'player_name', 'color', 'avatar',
            'is_active', 'is_ai', 'defeated_at', 'score',
            'resources', 'researched_technologies', 'current_research',
            'diplomacy', 'character_count',
            'joined_at', 'last_active_at'
        ]
        read_only_fields = ['id', 'joined_at', 'last_active_at']

    def get_character_count(self, obj):
        """Get number of characters owned by player."""
        return obj.characters.exclude(status='dead').count()


class PlayerCreateSerializer(serializers.ModelSerializer):
    """Serializer for joining a game as a player."""

    class Meta:
        model = Player
        fields = ['game', 'player_name', 'color', 'avatar']

    def validate_color(self, value):
        """Validate hex color format."""
        if not value.startswith('#') or len(value) != 7:
            raise serializers.ValidationError("Color must be in hex format (#RRGGBB)")
        return value

    def validate(self, data):
        """Validate player can join the game."""
        game = data.get('game')
        if game.status not in ['waiting', 'active']:
            raise serializers.ValidationError("Cannot join a finished or paused game")

        if game.players.filter(is_active=True).count() >= game.max_players:
            raise serializers.ValidationError("Game is full")

        return data


# ============================================================================
# HexTile Serializers
# ============================================================================

class HexTileSerializer(serializers.ModelSerializer):
    """Serializer for hex tiles."""

    class Meta:
        model = HexTile
        fields = [
            'id', 'game', 'q', 'r', 'terrain_type', 'elevation',
            'is_passable', 'visibility', 'structure', 'effects',
            'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']

    def validate(self, data):
        """Validate hex coordinates are unique within game."""
        game = data.get('game')
        q = data.get('q')
        r = data.get('r')

        if self.instance:
            # Update - check for duplicates excluding current instance
            if HexTile.objects.filter(game=game, q=q, r=r).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A tile already exists at these coordinates")
        else:
            # Create - check for duplicates
            if HexTile.objects.filter(game=game, q=q, r=r).exists():
                raise serializers.ValidationError("A tile already exists at these coordinates")

        return data


class HexTileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for hex tile list views."""

    has_structure = serializers.SerializerMethodField()

    class Meta:
        model = HexTile
        fields = [
            'id', 'q', 'r', 'terrain_type', 'elevation',
            'is_passable', 'has_structure'
        ]
        read_only_fields = ['id']

    def get_has_structure(self, obj):
        """Check if tile has a structure."""
        return bool(obj.structure)


# ============================================================================
# Character Serializers
# ============================================================================

class CharacterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for character list views."""

    owner_name = serializers.CharField(source='owner.player_name', read_only=True)

    class Meta:
        model = Character
        fields = [
            'id', 'game', 'owner', 'owner_name', 'character_type',
            'name', 'is_hero', 'health', 'max_health',
            'position_q', 'position_r', 'status', 'level',
            'in_combat'
        ]
        read_only_fields = ['id']


class CharacterDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for character detail views."""

    owner_name = serializers.CharField(source='owner.player_name', read_only=True)
    inventory_count = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = [
            'id', 'game', 'owner', 'owner_name', 'character_type',
            'name', 'is_hero',
            'health', 'max_health', 'stamina', 'max_stamina',
            'experience', 'level',
            'position_q', 'position_r',
            'status', 'movement_path', 'movement_points', 'max_movement_points',
            'inventory', 'inventory_capacity', 'inventory_count',
            'current_orders', 'in_combat', 'combat_id',
            'attributes', 'skills',
            'created_at', 'updated_at', 'died_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'died_at']

    def get_inventory_count(self, obj):
        """Get total number of items in inventory."""
        return len(obj.inventory)


class CharacterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new characters."""

    class Meta:
        model = Character
        fields = [
            'game', 'owner', 'character_type', 'name', 'is_hero',
            'position_q', 'position_r',
            'max_health', 'max_stamina', 'max_movement_points',
            'inventory_capacity', 'attributes'
        ]

    def validate(self, data):
        """Validate character creation."""
        game = data.get('game')
        owner = data.get('owner')

        # Validate owner belongs to game
        if owner.game != game:
            raise serializers.ValidationError("Owner must belong to the same game")

        # Validate position is within map bounds
        q = data.get('position_q')
        r = data.get('position_r')

        if not HexTile.objects.filter(game=game, q=q, r=r).exists():
            raise serializers.ValidationError("Starting position must be a valid tile")

        return data

    def create(self, validated_data):
        """Create character with default values."""
        # Set current health/stamina to max values
        validated_data['health'] = validated_data.get('max_health', 100)
        validated_data['stamina'] = validated_data.get('max_stamina', 100)
        validated_data['movement_points'] = validated_data.get('max_movement_points', 3)

        return super().create(validated_data)


class CharacterUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating character state."""

    class Meta:
        model = Character
        fields = [
            'health', 'stamina', 'experience', 'level',
            'position_q', 'position_r',
            'status', 'movement_path', 'movement_points',
            'inventory', 'current_orders',
            'in_combat', 'combat_id', 'attributes', 'skills'
        ]

    def validate_health(self, value):
        """Ensure health doesn't exceed max_health."""
        if self.instance and value > self.instance.max_health:
            raise serializers.ValidationError("Health cannot exceed max_health")
        return value

    def validate_stamina(self, value):
        """Ensure stamina doesn't exceed max_stamina."""
        if self.instance and value > self.instance.max_stamina:
            raise serializers.ValidationError("Stamina cannot exceed max_stamina")
        return value


# ============================================================================
# MapItem Serializers
# ============================================================================

class MapItemSerializer(serializers.ModelSerializer):
    """Serializer for map items (loot)."""

    collected_by_name = serializers.CharField(
        source='collected_by.name',
        read_only=True,
        allow_null=True
    )

    class Meta:
        model = MapItem
        fields = [
            'id', 'game', 'item_type', 'item_id',
            'position_q', 'position_r',
            'quantity', 'rarity', 'is_available', 'is_locked',
            'spawned_at_tick', 'despawn_at_tick',
            'source_type', 'source_id', 'item_data',
            'created_at', 'collected_at', 'collected_by', 'collected_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'collected_at', 'collected_by']


class MapItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for spawning map items."""

    class Meta:
        model = MapItem
        fields = [
            'game', 'item_type', 'item_id',
            'position_q', 'position_r',
            'quantity', 'rarity', 'is_locked',
            'spawned_at_tick', 'despawn_at_tick',
            'source_type', 'source_id', 'item_data'
        ]

    def validate(self, data):
        """Validate item spawn position."""
        game = data.get('game')
        q = data.get('position_q')
        r = data.get('position_r')

        if not HexTile.objects.filter(game=game, q=q, r=r).exists():
            raise serializers.ValidationError("Item must be placed on a valid tile")

        return data


class MapItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for map item list views."""

    class Meta:
        model = MapItem
        fields = [
            'id', 'item_type', 'position_q', 'position_r',
            'quantity', 'rarity', 'is_available', 'is_locked'
        ]
        read_only_fields = ['id']


# ============================================================================
# Interactable Serializers
# ============================================================================

class InteractableSerializer(serializers.ModelSerializer):
    """Serializer for interactable objects."""

    can_use = serializers.SerializerMethodField()

    class Meta:
        model = Interactable
        fields = [
            'id', 'game', 'interactable_type', 'interactable_id', 'name',
            'position_q', 'position_r',
            'state', 'is_active',
            'required_items', 'required_level',
            'loot_table', 'max_uses', 'current_uses',
            'cooldown_ticks', 'last_used_tick',
            'data', 'interactions', 'can_use',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'current_uses', 'last_used_tick']

    def get_can_use(self, obj):
        """Check if interactable can be used (not on cooldown)."""
        if obj.max_uses > 0 and obj.current_uses >= obj.max_uses:
            return False

        # Check cooldown (would need current tick from context)
        game = obj.game
        if obj.last_used_tick and obj.cooldown_ticks > 0:
            if game.current_tick - obj.last_used_tick < obj.cooldown_ticks:
                return False

        return obj.is_active


class InteractableCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating interactable objects."""

    class Meta:
        model = Interactable
        fields = [
            'game', 'interactable_type', 'interactable_id', 'name',
            'position_q', 'position_r',
            'state', 'required_items', 'required_level',
            'loot_table', 'max_uses', 'cooldown_ticks', 'data'
        ]

    def validate(self, data):
        """Validate interactable creation."""
        game = data.get('game')
        q = data.get('position_q')
        r = data.get('position_r')

        if not HexTile.objects.filter(game=game, q=q, r=r).exists():
            raise serializers.ValidationError("Interactable must be placed on a valid tile")

        return data


class InteractableListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for interactable list views."""

    class Meta:
        model = Interactable
        fields = [
            'id', 'interactable_type', 'name',
            'position_q', 'position_r',
            'state', 'is_active'
        ]
        read_only_fields = ['id']
