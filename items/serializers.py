from rest_framework import serializers
from .models import Item


# ============================================================================
# Item Serializers
# ============================================================================

class ItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for item list views."""

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'type', 'rarity', 'category', 'sub_category',
            'icon', 'stack_size', 'is_active'
        ]
        read_only_fields = ['id']


class ItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for item detail views."""

    class Meta:
        model = Item
        fields = [
            'id', 'name', 'description', 'type', 'rarity', 'icon',
            'stat_modifiers', 'effect', 'durability',
            'category', 'sub_category', 'stack_size', 'cooldown',
            'upgrade_level', 'drop_rate', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new items."""

    class Meta:
        model = Item
        fields = [
            'name', 'description', 'type', 'rarity', 'icon',
            'stat_modifiers', 'effect', 'durability',
            'category', 'sub_category', 'stack_size', 'cooldown',
            'upgrade_level', 'drop_rate', 'is_active'
        ]

    def validate_name(self, value):
        """Validate item name is not empty and unique."""
        if not value or not value.strip():
            raise serializers.ValidationError("Item name cannot be empty")
        return value.strip()

    def validate_rarity(self, value):
        """Validate rarity is one of the allowed choices."""
        allowed_rarities = ['common', 'rare', 'legendary']
        if value not in allowed_rarities:
            raise serializers.ValidationError(
                f"Rarity must be one of: {', '.join(allowed_rarities)}"
            )
        return value

    def validate_stack_size(self, value):
        """Validate stack size is positive."""
        if value < 1:
            raise serializers.ValidationError("Stack size must be at least 1")
        if value > 9999:
            raise serializers.ValidationError("Stack size cannot exceed 9999")
        return value

    def validate_cooldown(self, value):
        """Validate cooldown is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Cooldown cannot be negative")
        return value

    def validate_upgrade_level(self, value):
        """Validate upgrade level is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Upgrade level cannot be negative")
        if value > 100:
            raise serializers.ValidationError("Upgrade level cannot exceed 100")
        return value

    def validate_drop_rate(self, value):
        """Validate drop rate is between 0 and 1."""
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("Drop rate must be between 0.0 and 1.0")
        return value

    def validate_durability(self, value):
        """Validate durability is positive if provided."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Durability cannot be negative")
        return value

    def validate_stat_modifiers(self, value):
        """Validate stat_modifiers is a valid dictionary if provided."""
        if value is not None:
            if not isinstance(value, dict):
                raise serializers.ValidationError("stat_modifiers must be a dictionary")
            # Validate all values are numeric
            for key, val in value.items():
                if not isinstance(val, (int, float)):
                    raise serializers.ValidationError(
                        f"stat_modifiers['{key}'] must be a number"
                    )
        return value


class ItemUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing items."""

    class Meta:
        model = Item
        fields = [
            'name', 'description', 'type', 'rarity', 'icon',
            'stat_modifiers', 'effect', 'durability',
            'category', 'sub_category', 'stack_size', 'cooldown',
            'upgrade_level', 'drop_rate', 'is_active'
        ]

    def validate_stack_size(self, value):
        """Validate stack size is positive."""
        if value < 1:
            raise serializers.ValidationError("Stack size must be at least 1")
        if value > 9999:
            raise serializers.ValidationError("Stack size cannot exceed 9999")
        return value

    def validate_cooldown(self, value):
        """Validate cooldown is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Cooldown cannot be negative")
        return value

    def validate_upgrade_level(self, value):
        """Validate upgrade level is non-negative."""
        if value < 0:
            raise serializers.ValidationError("Upgrade level cannot be negative")
        if value > 100:
            raise serializers.ValidationError("Upgrade level cannot exceed 100")
        return value

    def validate_drop_rate(self, value):
        """Validate drop rate is between 0 and 1."""
        if value < 0.0 or value > 1.0:
            raise serializers.ValidationError("Drop rate must be between 0.0 and 1.0")
        return value

    def validate_durability(self, value):
        """Validate durability is positive if provided."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Durability cannot be negative")
        return value

    def validate_stat_modifiers(self, value):
        """Validate stat_modifiers is a valid dictionary if provided."""
        if value is not None:
            if not isinstance(value, dict):
                raise serializers.ValidationError("stat_modifiers must be a dictionary")
            # Validate all values are numeric
            for key, val in value.items():
                if not isinstance(val, (int, float)):
                    raise serializers.ValidationError(
                        f"stat_modifiers['{key}'] must be a number"
                    )
        return value
