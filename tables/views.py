from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import ManagerOrReadOnly
from .models import Table
from .serializers import TableSerializer


class TableViewSet(ModelViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    permission_classes = [IsAuthenticated, ManagerOrReadOnly]
    ordering_fields = ["number", "status", "id"]
    search_fields = ["number"]
