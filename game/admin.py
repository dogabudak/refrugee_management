from django.contrib import admin
from django.utils.html import format_html
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
# Game Admin
# ============================================================================

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin interface for Game model."""

    list_display = [
        'id', 'name', 'status_badge', 'player_count', 'current_tick',
        'tick_duration_minutes', 'map_size', 'started_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'started_at']
    search_fields = ['name', 'map_name']
    readonly_fields = ['created_at', 'updated_at', 'current_tick']
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'status', 'max_players']
        }),
        ('Game Settings', {
            'fields': ['current_tick', 'tick_duration_minutes', 'settings']
        }),
        ('Map Configuration', {
            'fields': ['map_name', 'map_width', 'map_height']
        }),
        ('Timing', {
            'fields': ['started_at', 'next_tick_at', 'finished_at', 'created_at', 'updated_at']
        }),
    ]

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'waiting': '#FFA500',
            'active': '#28A745',
            'paused': '#FFC107',
            'finished': '#6C757D'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def player_count(self, obj):
        """Display current player count vs max."""
        count = obj.players.filter(is_active=True).count()
        return f"{count}/{obj.max_players}"
    player_count.short_description = 'Players'

    def map_size(self, obj):
        """Display map dimensions."""
        return f"{obj.map_width}x{obj.map_height}"
    map_size.short_description = 'Map Size'


# ============================================================================
# WorldState Admin
# ============================================================================

@admin.register(WorldState)
class WorldStateAdmin(admin.ModelAdmin):
    """Admin interface for WorldState model."""

    list_display = [
        'id', 'game', 'tick', 'is_current', 'active_players',
        'total_characters', 'commands_processed', 'created_at'
    ]
    list_filter = ['is_current', 'game', 'created_at']
    search_fields = ['game__name', 'tick']
    readonly_fields = ['created_at', 'state_hash']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'tick', 'is_current']
        }),
        ('Statistics', {
            'fields': ['active_players', 'total_characters', 'commands_processed']
        }),
        ('State Data', {
            'fields': ['state_snapshot', 'state_hash', 'events'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at']
        }),
    ]

    def has_add_permission(self, request):
        """WorldStates should typically be created programmatically."""
        return False


# ============================================================================
# Player Admin
# ============================================================================

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Admin interface for Player model."""

    list_display = [
        'id', 'player_name', 'user', 'game', 'color_badge',
        'is_active', 'is_ai', 'score', 'character_count', 'joined_at'
    ]
    list_filter = ['is_active', 'is_ai', 'game', 'joined_at']
    search_fields = ['player_name', 'user__username', 'game__name']
    readonly_fields = ['joined_at', 'last_active_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'user', 'player_name', 'color', 'avatar']
        }),
        ('Game Status', {
            'fields': ['is_active', 'is_ai', 'defeated_at', 'score']
        }),
        ('Resources & Progress', {
            'fields': ['resources', 'researched_technologies', 'current_research'],
            'classes': ['collapse']
        }),
        ('Diplomacy', {
            'fields': ['diplomacy'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['joined_at', 'last_active_at']
        }),
    ]

    def color_badge(self, obj):
        """Display player color as a colored square."""
        return format_html(
            '<span style="background-color: {}; padding: 5px 15px; border: 1px solid #000;">&nbsp;</span> {}',
            obj.color, obj.color
        )
    color_badge.short_description = 'Color'

    def character_count(self, obj):
        """Display number of characters owned by player."""
        return obj.characters.exclude(status='dead').count()
    character_count.short_description = 'Characters'


# ============================================================================
# HexTile Admin
# ============================================================================

@admin.register(HexTile)
class HexTileAdmin(admin.ModelAdmin):
    """Admin interface for HexTile model."""

    list_display = [
        'id', 'game', 'coordinates', 'terrain_type',
        'elevation', 'is_passable', 'has_structure', 'updated_at'
    ]
    list_filter = ['terrain_type', 'is_passable', 'game']
    search_fields = ['game__name', 'q', 'r']
    readonly_fields = ['updated_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'q', 'r']
        }),
        ('Terrain Properties', {
            'fields': ['terrain_type', 'elevation', 'is_passable']
        }),
        ('Visibility', {
            'fields': ['visibility'],
            'classes': ['collapse']
        }),
        ('Structure & Effects', {
            'fields': ['structure', 'effects'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['updated_at']
        }),
    ]

    def coordinates(self, obj):
        """Display hex coordinates."""
        return f"({obj.q}, {obj.r})"
    coordinates.short_description = 'Coordinates'

    def has_structure(self, obj):
        """Check if tile has a structure."""
        return bool(obj.structure)
    has_structure.boolean = True
    has_structure.short_description = 'Structure'


# ============================================================================
# Character Admin
# ============================================================================

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    """Admin interface for Character model."""

    list_display = [
        'id', 'name', 'character_type', 'owner', 'game',
        'health_bar', 'level', 'position', 'status_badge',
        'is_hero', 'in_combat'
    ]
    list_filter = ['status', 'is_hero', 'in_combat', 'game', 'character_type']
    search_fields = ['name', 'owner__player_name', 'game__name']
    readonly_fields = ['created_at', 'updated_at', 'died_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'owner', 'character_type', 'name', 'is_hero']
        }),
        ('Stats', {
            'fields': [
                'health', 'max_health', 'stamina', 'max_stamina',
                'experience', 'level'
            ]
        }),
        ('Position & Movement', {
            'fields': [
                'position_q', 'position_r', 'status',
                'movement_path', 'movement_points', 'max_movement_points'
            ]
        }),
        ('Inventory', {
            'fields': ['inventory', 'inventory_capacity'],
            'classes': ['collapse']
        }),
        ('Orders & Combat', {
            'fields': ['current_orders', 'in_combat', 'combat_id']
        }),
        ('Attributes & Skills', {
            'fields': ['attributes', 'skills'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at', 'died_at']
        }),
    ]

    def health_bar(self, obj):
        """Display health as a visual bar."""
        if obj.max_health == 0:
            percentage = 0
        else:
            percentage = (obj.health / obj.max_health) * 100

        if percentage > 75:
            color = '#28A745'
        elif percentage > 50:
            color = '#FFC107'
        elif percentage > 25:
            color = '#FD7E14'
        else:
            color = '#DC3545'

        return format_html(
            '<div style="width: 100px; background-color: #ddd; border: 1px solid #999;">'
            '<div style="width: {}%; background-color: {}; height: 20px;"></div>'
            '</div> {}/{}',
            percentage, color, obj.health, obj.max_health
        )
    health_bar.short_description = 'Health'

    def position(self, obj):
        """Display position coordinates."""
        return f"({obj.position_q}, {obj.position_r})"
    position.short_description = 'Position'

    def status_badge(self, obj):
        """Display status with color coding."""
        colors = {
            'idle': '#6C757D',
            'moving': '#17A2B8',
            'looting': '#FFC107',
            'interacting': '#007BFF',
            'in_combat': '#DC3545',
            'dead': '#000000'
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


# ============================================================================
# MapItem Admin
# ============================================================================

@admin.register(MapItem)
class MapItemAdmin(admin.ModelAdmin):
    """Admin interface for MapItem model."""

    list_display = [
        'id', 'item_type', 'game', 'position', 'quantity',
        'rarity_badge', 'is_available', 'is_locked',
        'spawned_at_tick', 'collected_status'
    ]
    list_filter = ['rarity', 'is_available', 'is_locked', 'game', 'item_type']
    search_fields = ['item_type', 'item_id', 'game__name']
    readonly_fields = ['created_at', 'collected_at', 'collected_by']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'item_type', 'item_id']
        }),
        ('Position', {
            'fields': ['position_q', 'position_r']
        }),
        ('Item Properties', {
            'fields': ['quantity', 'rarity', 'is_available', 'is_locked']
        }),
        ('Spawn Information', {
            'fields': ['spawned_at_tick', 'despawn_at_tick', 'source_type', 'source_id']
        }),
        ('Item Data', {
            'fields': ['item_data'],
            'classes': ['collapse']
        }),
        ('Collection', {
            'fields': ['collected_at', 'collected_by', 'created_at']
        }),
    ]

    def position(self, obj):
        """Display position coordinates."""
        return f"({obj.position_q}, {obj.position_r})"
    position.short_description = 'Position'

    def rarity_badge(self, obj):
        """Display rarity with color coding."""
        colors = {
            'common': '#6C757D',
            'uncommon': '#28A745',
            'rare': '#007BFF',
            'epic': '#6F42C1',
            'legendary': '#FD7E14'
        }
        color = colors.get(obj.rarity, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_rarity_display()
        )
    rarity_badge.short_description = 'Rarity'

    def collected_status(self, obj):
        """Display collection status."""
        if obj.collected_at:
            return format_html(
                '<span style="color: #28A745;">Collected</span>'
            )
        return format_html(
            '<span style="color: #FFC107;">Available</span>'
        )
    collected_status.short_description = 'Status'


# ============================================================================
# Interactable Admin
# ============================================================================

@admin.register(Interactable)
class InteractableAdmin(admin.ModelAdmin):
    """Admin interface for Interactable model."""

    list_display = [
        'id', 'name', 'interactable_type', 'game',
        'position', 'state_badge', 'is_active',
        'usage', 'created_at'
    ]
    list_filter = ['interactable_type', 'state', 'is_active', 'game']
    search_fields = ['name', 'interactable_id', 'game__name']
    readonly_fields = ['created_at', 'updated_at', 'current_uses', 'last_used_tick']
    fieldsets = [
        ('Basic Information', {
            'fields': ['game', 'interactable_type', 'interactable_id', 'name']
        }),
        ('Position', {
            'fields': ['position_q', 'position_r']
        }),
        ('State', {
            'fields': ['state', 'is_active']
        }),
        ('Requirements', {
            'fields': ['required_items', 'required_level']
        }),
        ('Rewards', {
            'fields': ['loot_table'],
            'classes': ['collapse']
        }),
        ('Usage & Cooldown', {
            'fields': ['max_uses', 'current_uses', 'cooldown_ticks', 'last_used_tick']
        }),
        ('Data', {
            'fields': ['data'],
            'classes': ['collapse']
        }),
        ('Interaction History', {
            'fields': ['interactions'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    ]

    def position(self, obj):
        """Display position coordinates."""
        return f"({obj.position_q}, {obj.position_r})"
    position.short_description = 'Position'

    def state_badge(self, obj):
        """Display state with color coding."""
        colors = {
            'active': '#28A745',
            'used': '#6C757D',
            'destroyed': '#DC3545',
            'locked': '#FFC107',
            'unlocked': '#007BFF'
        }
        color = colors.get(obj.state, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_state_display()
        )
    state_badge.short_description = 'State'

    def usage(self, obj):
        """Display usage count."""
        if obj.max_uses == 0:
            return "Unlimited"
        return f"{obj.current_uses}/{obj.max_uses}"
    usage.short_description = 'Usage'
