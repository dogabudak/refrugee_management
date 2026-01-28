from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Item
from .serializers import (
    ItemListSerializer,
    ItemDetailSerializer,
    ItemCreateSerializer,
    ItemUpdateSerializer,
)


# ============================================================================
# Item ViewSet
# ============================================================================

@extend_schema_view(
    list=extend_schema(description="List all items", tags=["Items"]),
    retrieve=extend_schema(description="Get item details", tags=["Items"]),
    create=extend_schema(description="Create a new item", tags=["Items"]),
    update=extend_schema(description="Update an item", tags=["Items"]),
    partial_update=extend_schema(description="Partially update an item", tags=["Items"]),
    destroy=extend_schema(description="Delete an item", tags=["Items"]),
)
class ItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing items.
    Provides CRUD operations and filtering capabilities.
    """
    queryset = Item.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return ItemListSerializer
        elif self.action == 'create':
            return ItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ItemUpdateSerializer
        return ItemDetailSerializer

    def get_queryset(self):
        """
        Filter queryset based on query parameters.
        Supports filtering by: type, rarity, category, sub_category, is_active
        """
        queryset = Item.objects.all()

        # Filter by type
        item_type = self.request.query_params.get('type', None)
        if item_type:
            queryset = queryset.filter(type=item_type)

        # Filter by rarity
        rarity = self.request.query_params.get('rarity', None)
        if rarity:
            queryset = queryset.filter(rarity=rarity)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by sub_category
        sub_category = self.request.query_params.get('sub_category', None)
        if sub_category:
            queryset = queryset.filter(sub_category=sub_category)

        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        # Search by name (case-insensitive partial match)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset.order_by('name')

    @extend_schema(
        description="Activate an item (set is_active to True)",
        tags=["Items"],
        responses={200: ItemDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate an item."""
        item = self.get_object()
        item.is_active = True
        item.save()
        serializer = ItemDetailSerializer(item)
        return Response(serializer.data)

    @extend_schema(
        description="Deactivate an item (set is_active to False)",
        tags=["Items"],
        responses={200: ItemDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate an item."""
        item = self.get_object()
        item.is_active = False
        item.save()
        serializer = ItemDetailSerializer(item)
        return Response(serializer.data)

    @extend_schema(
        description="Get items by rarity level",
        tags=["Items"],
        responses={200: ItemListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_rarity(self, request):
        """Get items filtered by rarity."""
        rarity = request.query_params.get('rarity')
        if not rarity:
            return Response(
                {"error": "rarity parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = self.get_queryset().filter(rarity=rarity)
        serializer = ItemListSerializer(items, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Get items by type",
        tags=["Items"],
        responses={200: ItemListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get items filtered by type."""
        item_type = request.query_params.get('type')
        if not item_type:
            return Response(
                {"error": "type parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        items = self.get_queryset().filter(type=item_type)
        serializer = ItemListSerializer(items, many=True)
        return Response(serializer.data)