from .filters import MenuItemFilter
from rest_framework import status,viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import Group
from rest_framework.pagination import PageNumberPagination
from . import models, serializers
from .permission import IsManager
from rest_framework.decorators import action


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    # allow user to specify how many item on page there is with page_size=numbers

    max_page_size = 30

class CategoryView(viewsets.ModelViewSet):
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.action in ['create','update','destroy','partial_update']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes =  [IsAuthenticated]
        return [permission() for permission in permission_classes]

class MenuItemView(viewsets.ModelViewSet):
    queryset = models.MenuItem.objects.select_related('category').all()
    serializer_class = serializers.MenuItemSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_class = MenuItemFilter
    def get_permissions(self):
        if self.action in ['create','update','destroy','partial_update']:
            permission_classes = [IsAdminUser, IsManager]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
        

def get_userToGroup(request, group_name):
    user_id = request.data.get('username')
    if user_id:
        try:
            user = models.User.objects.get(id=user_id)
            user_group = Group.objects.get(name=group_name)
            user_group.user_set.add(user)
            return Response({'message': f'{user.username} has been assigned as {group_name}'}, status=201)
        except models.User.DoesNotExist:
            return Response({"message": 'User not found!'}, status=404)
        except Group.DoesNotExist:
            return Response({"message": f'{group_name} group does not exist!'}, status=404)
    return Response({"message": 'Invalid data!'}, status=400)

def remove_userFromGroup(group_name, pk):
    user_id = models.User.objects.get(id=pk)
    if user_id:
        group = Group.objects.filter(name=group_name).first()
        if group:
            if user_id.groups.filter(name=group_name).exists():
                user_id.groups.remove(group)
                return Response({
                    'message':f'you successfully remove {user_id.username} from the {group_name} role'
                }, status=200)

            else:
                return Response({
                    'message':f'This user is not in the {group_name} group'
                },status=404)
        else:
            return Response({'message':f'{group_name} group does not exist!'},status=404)


class ManagerUserView(viewsets.ModelViewSet):
    queryset = models.User.objects.filter(groups__name='Manager').all()
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get', 'post', 'delete']
    pagination_class = StandardResultsSetPagination
    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        return remove_userFromGroup(group_name='Manager', pk=pk)
    
    def create(self, request):
        return get_userToGroup(request=request, group_name='Manager')

    def retrieve(self, request, *args, **kwargs):
        return Response({'detail': 'Method "GET" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class deliveryCrewUserView(viewsets.ModelViewSet):
    queryset = models.User.objects.filter(groups__name='Delivery Crew').all()
    permission_classes = [IsManager, IsAdminUser]
    http_method_names = ['get','post','delete']
    serializer_class = serializers.UserSerializer
    pagination_class = StandardResultsSetPagination
    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        return remove_userFromGroup(group_name='Delivery Crew', pk=pk)
    
    def create(self, request):
        return get_userToGroup(request=request, group_name='Delivery Crew')

    def retrieve(self, request, *args, **kwargs):
        return Response({'detail': 'Method "GET" not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

class CartAPIView(viewsets.ModelViewSet):
    serializer_class = serializers.CartSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return models.Cart.objects.filter(user=user)
    
    #remove all item from cart for that user, access by api/carts/menu-items/clear
    @action(detail=False, methods=['delete'], url_path='clear', url_name='clear-cart')
    def clear_cart(self, request):
        user = request.user
        models.Cart.objects.filter(user=user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    