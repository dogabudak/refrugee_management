from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class Game(models.Model):
    """
    Represents a single game instance.
    Multiple players participate in one game.
    """
    STATUS_CHOICES = [
        ('waiting', 'Waiting for Players'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('finished', 'Finished'),
    ]

    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    max_players = models.IntegerField(default=32)
    current_tick = models.IntegerField(default=0)
    tick_duration_minutes = models.IntegerField(default=15)  # Real-time minutes per tick
    map_name = models.CharField(max_length=100)  # Reference to map in content service

    # Map dimensions (for hex grid)
    map_width = models.IntegerField(default=50)
    map_height = models.IntegerField(default=50)

    # Game timing
    started_at = models.DateTimeField(null=True, blank=True)
    next_tick_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    # Game settings
    settings = models.JSONField(default=dict, blank=True)  # Custom game rules/settings

    def __str__(self):
        return f"{self.name} (Tick {self.current_tick})"

    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"
        ordering = ['-created_at']


class WorldState(models.Model):
    """
    Immutable snapshot of the entire game world at a specific tick.
    Stores denormalized game state for efficient querying and historical replay.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='world_states')
    tick = models.IntegerField()

    # Complete game state as JSON for fast serialization
    # This is denormalized for performance - individual models exist for querying
    state_snapshot = models.JSONField(default=dict, help_text="Complete denormalized game state")

    # State metadata
    created_at = models.DateTimeField(default=now, editable=False)
    is_current = models.BooleanField(default=False, db_index=True)

    # Statistics for this tick
    active_players = models.IntegerField(default=0)
    total_characters = models.IntegerField(default=0)
    commands_processed = models.IntegerField(default=0)

    # State hash for integrity verification
    state_hash = models.CharField(max_length=64, blank=True, help_text="SHA256 hash of state_snapshot")

    # Global game events for this tick
    events = models.JSONField(default=list, blank=True, help_text="List of events that occurred this tick")

    class Meta:
        verbose_name = "World State"
        verbose_name_plural = "World States"
        ordering = ['-tick']
        unique_together = [['game', 'tick']]
        indexes = [
            models.Index(fields=['game', 'tick']),
            models.Index(fields=['game', 'is_current']),
        ]

    def __str__(self):
        return f"{self.game.name} - Tick {self.tick}"


class Player(models.Model):
    """
    Represents a player in a specific game.
    One User can have multiple Players across different games.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_players')

    # Player info
    player_name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#FF0000')  # Hex color
    avatar = models.CharField(max_length=255, blank=True)  # Reference to avatar asset

    # Game status
    is_active = models.BooleanField(default=True)
    is_ai = models.BooleanField(default=False)
    defeated_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)

    # Resources (current state - also stored in WorldState)
    resources = models.JSONField(default=dict, help_text="Current resources: {resource_type: amount}")

    # Research/Technology
    researched_technologies = models.JSONField(default=list, help_text="List of researched tech IDs")
    current_research = models.JSONField(default=dict, blank=True, help_text="Current research progress")

    # Diplomacy
    diplomacy = models.JSONField(
        default=dict,
        help_text="Diplomatic relations: {player_id: {status, since_tick}}"
    )

    # Timestamps
    joined_at = models.DateTimeField(default=now)
    last_active_at = models.DateTimeField(default=now)

    class Meta:
        verbose_name = "Player"
        verbose_name_plural = "Players"
        unique_together = [['game', 'user']]
        ordering = ['player_name']
        indexes = [
            models.Index(fields=['game', 'is_active']),
        ]

    def __str__(self):
        return f"{self.player_name} ({self.user.username}) in {self.game.name}"


class HexTile(models.Model):
    """
    Represents a hexagonal tile on the game map.
    Uses axial coordinates (q, r) for hexagon positioning.
    """
    TERRAIN_CHOICES = [
        ('plains', 'Plains'),
        ('forest', 'Forest'),
        ('mountain', 'Mountain'),
        ('water', 'Water'),
        ('desert', 'Desert'),
        ('swamp', 'Swamp'),
        ('snow', 'Snow'),
        ('urban', 'Urban'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='hex_tiles')

    # Axial coordinates (q, r) - standard hex coordinate system
    # See: https://www.redblobgames.com/grids/hexagons/
    q = models.IntegerField(help_text="Axial coordinate Q")
    r = models.IntegerField(help_text="Axial coordinate R")

    # Tile properties
    terrain_type = models.CharField(max_length=50, choices=TERRAIN_CHOICES, default='plains')
    elevation = models.IntegerField(default=0)
    is_passable = models.BooleanField(default=True)

    # Visibility/Fog of War (per player)
    visibility = models.JSONField(
        default=dict,
        help_text="Visibility state per player: {player_id: {visible, last_seen_tick}}"
    )

    # Structure/Building on this tile (if any)
    structure = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structure data: {type, owner_id, health, level, etc.}"
    )

    # Environmental effects
    effects = models.JSONField(
        default=list,
        blank=True,
        help_text="Active effects on tile: [{effect_type, duration, parameters}]"
    )

    # Metadata
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hex Tile"
        verbose_name_plural = "Hex Tiles"
        unique_together = [['game', 'q', 'r']]
        indexes = [
            models.Index(fields=['game', 'q', 'r']),
            models.Index(fields=['game', 'terrain_type']),
        ]

    def __str__(self):
        return f"Tile ({self.q}, {self.r}) - {self.terrain_type}"


class Character(models.Model):
    """
    Represents a character/unit in the game.
    Characters can move on hex tiles, loot items, and interact with the world.
    """
    CHARACTER_STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('moving', 'Moving'),
        ('looting', 'Looting'),
        ('interacting', 'Interacting'),
        ('in_combat', 'In Combat'),
        ('dead', 'Dead'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='characters')
    owner = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='characters')

    # Character type and identity
    character_type = models.CharField(max_length=50, help_text="Reference to character definition in content service")
    name = models.CharField(max_length=100)
    is_hero = models.BooleanField(default=False)  # Hero/main character vs regular unit

    # Stats (current values)
    health = models.IntegerField(default=100)
    max_health = models.IntegerField(default=100)
    stamina = models.IntegerField(default=100)
    max_stamina = models.IntegerField(default=100)
    experience = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    # Position (hex coordinates)
    position_q = models.IntegerField(help_text="Current Q coordinate")
    position_r = models.IntegerField(help_text="Current R coordinate")

    # Movement
    status = models.CharField(max_length=20, choices=CHARACTER_STATUS_CHOICES, default='idle')
    movement_path = models.JSONField(
        default=list,
        help_text="Queue of hex coordinates for movement: [{q, r}, ...]"
    )
    movement_points = models.IntegerField(default=0)  # Remaining movement this turn
    max_movement_points = models.IntegerField(default=3)

    # Inventory
    inventory = models.JSONField(
        default=list,
        help_text="Character inventory: [{item_id, quantity, equipped}, ...]"
    )
    inventory_capacity = models.IntegerField(default=20)

    # Orders/Actions
    current_orders = models.JSONField(
        default=dict,
        blank=True,
        help_text="Current orders: {order_type, target, parameters}"
    )

    # Combat
    in_combat = models.BooleanField(default=False)
    combat_id = models.CharField(max_length=50, blank=True)  # Reference to combat instance

    # Character attributes (flexible for different character types)
    attributes = models.JSONField(
        default=dict,
        help_text="Character attributes: {strength, agility, intelligence, etc.}"
    )

    # Skills/Abilities
    skills = models.JSONField(
        default=list,
        help_text="Learned skills/abilities: [{skill_id, level, cooldown}, ...]"
    )

    # Metadata
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    died_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Character"
        verbose_name_plural = "Characters"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'owner']),
            models.Index(fields=['game', 'position_q', 'position_r']),
            models.Index(fields=['game', 'status']),
        ]

    def __str__(self):
        return f"{self.name} ({self.character_type}) - {self.owner.player_name}"


class MapItem(models.Model):
    """
    Represents loot/items placed on the map that can be collected by characters.
    """
    ITEM_RARITY_CHOICES = [
        ('common', 'Common'),
        ('uncommon', 'Uncommon'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='map_items')

    # Item reference
    item_type = models.CharField(max_length=50, help_text="Reference to item definition in content service")
    item_id = models.CharField(max_length=100, help_text="Unique item instance ID")

    # Position on map
    position_q = models.IntegerField(help_text="Q coordinate")
    position_r = models.IntegerField(help_text="R coordinate")

    # Item properties
    quantity = models.IntegerField(default=1)
    rarity = models.CharField(max_length=20, choices=ITEM_RARITY_CHOICES, default='common')

    # Item state
    is_available = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)  # Requires key/unlock

    # Spawn information
    spawned_at_tick = models.IntegerField()
    despawn_at_tick = models.IntegerField(null=True, blank=True)  # Auto-despawn after time

    # Loot source (optional)
    source_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="What spawned this: chest, mob_drop, world_spawn, etc."
    )
    source_id = models.CharField(max_length=100, blank=True)

    # Item data (flexible for different item types)
    item_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Item-specific data: {durability, enchantments, etc.}"
    )

    # Metadata
    created_at = models.DateTimeField(default=now)
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        Character,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collected_items'
    )

    class Meta:
        verbose_name = "Map Item"
        verbose_name_plural = "Map Items"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'position_q', 'position_r']),
            models.Index(fields=['game', 'is_available']),
        ]

    def __str__(self):
        return f"{self.item_type} at ({self.position_q}, {self.position_r})"


class Interactable(models.Model):
    """
    Represents interactive objects on the map (chests, doors, NPCs, etc.)
    that characters can interact with.
    """
    INTERACTABLE_TYPE_CHOICES = [
        ('chest', 'Chest'),
        ('door', 'Door'),
        ('npc', 'NPC'),
        ('portal', 'Portal'),
        ('shrine', 'Shrine'),
        ('trap', 'Trap'),
        ('resource_node', 'Resource Node'),
        ('puzzle', 'Puzzle'),
    ]

    STATE_CHOICES = [
        ('active', 'Active'),
        ('used', 'Used'),
        ('destroyed', 'Destroyed'),
        ('locked', 'Locked'),
        ('unlocked', 'Unlocked'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='interactables')

    # Type and identity
    interactable_type = models.CharField(max_length=50, choices=INTERACTABLE_TYPE_CHOICES)
    interactable_id = models.CharField(max_length=100, help_text="Reference to interactable definition")
    name = models.CharField(max_length=100)

    # Position on map
    position_q = models.IntegerField(help_text="Q coordinate")
    position_r = models.IntegerField(help_text="R coordinate")

    # State
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='active')
    is_active = models.BooleanField(default=True)

    # Interaction requirements
    required_items = models.JSONField(
        default=list,
        blank=True,
        help_text="Items required to interact: [item_id, ...]"
    )
    required_level = models.IntegerField(default=1)

    # Interaction results/loot
    loot_table = models.JSONField(
        default=list,
        blank=True,
        help_text="Possible loot drops: [{item_id, quantity, probability}, ...]"
    )

    # Uses/Cooldown
    max_uses = models.IntegerField(default=1, help_text="0 = unlimited")
    current_uses = models.IntegerField(default=0)
    cooldown_ticks = models.IntegerField(default=0)
    last_used_tick = models.IntegerField(null=True, blank=True)

    # Interactable data (flexible for different types)
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Type-specific data: {dialogue, destination, rewards, etc.}"
    )

    # Interaction history
    interactions = models.JSONField(
        default=list,
        blank=True,
        help_text="History of interactions: [{character_id, tick, result}, ...]"
    )

    # Metadata
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Interactable"
        verbose_name_plural = "Interactables"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'position_q', 'position_r']),
            models.Index(fields=['game', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.interactable_type}) at ({self.position_q}, {self.position_r})"


