from django.db import models
from django.utils.timezone import now

class Item(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50)  # Example: 'weapon', 'armor', etc.
    rarity = models.CharField(max_length=50, choices=[
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('legendary', 'Legendary'),
    ])
    icon = models.URLField(blank=True, null=True)
    stat_modifiers = models.JSONField(blank=True, null=True)  # Example: {"strength": +5, "health": +10}
    effect = models.TextField(blank=True, null=True)  # Example: "Heals 50 HP over 10 seconds"
    durability = models.IntegerField(blank=True, null=True)
    category = models.CharField(max_length=50, blank=True, null=True)  # Example: 'equipment', 'consumable'
    sub_category = models.CharField(max_length=50, blank=True, null=True)  # Example: 'sword', 'potion'
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    stack_size = models.IntegerField(default=1)  # Maximum stackable quantity
    cooldown = models.IntegerField(default=0)  # Cooldown time in seconds
    upgrade_level = models.IntegerField(default=0)  # Current upgrade level
    drop_rate = models.FloatField(default=0.0)  # Probability of dropping

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Item"
        verbose_name_plural = "Items"
        ordering = ['name']
