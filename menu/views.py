from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import ManagerOrReadOnly
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer
from .filters import MenuItemFilter


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, ManagerOrReadOnly]
    search_fields = ["name"]
    ordering_fields = ["sort_order", "name", "id"]


class MenuItemViewSet(ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, ManagerOrReadOnly]

    filterset_class = MenuItemFilter
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "id", "prep_time_minutes"]
