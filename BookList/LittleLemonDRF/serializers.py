from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, User, OrderItem
import decimal
from rest_framework.validators import UniqueValidator
from django.contrib.auth.models import Group


class CategorySerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255,
                                  validators = [
                                    UniqueValidator(queryset=Category.objects.all())])
    class Meta:
        model = Category
        fields = ['slug','id','title']

class MenuItemSerializer(serializers.ModelSerializer):
    item_id = serializers.ReadOnlyField(source='id')
    category_id = serializers.PrimaryKeyRelatedField(queryset = Category.objects.all(), write_only=True)
    category_title = serializers.ReadOnlyField(source='category.title')
    class Meta:
        model = MenuItem
        fields = ['item_id','title','price','featured','category_id','category_title']

    def create(self,validated_data):
        category = validated_data.pop('category_id')
        menu_item = MenuItem.objects.create(category=category,**validated_data)
        return menu_item


class UserSerializer(serializers.ModelSerializer):
    username = serializers.PrimaryKeyRelatedField(queryset = User.objects.all())
    class Meta:
        model = User
        fields = ['id','username']
        extra_kwargs ={
            'username':{'read_only':True}
        }

class CartSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()  # Represents the cart ID
    user_id = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem',write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    title = serializers.CharField(source='menuitem.title', read_only=True)
    unit_price = serializers.DecimalField(source='menuitem.price', max_digits=10, decimal_places=2,write_only=True)
    total_price = serializers.SerializerMethodField(method_name='get_total',read_only=True)  # Total price of the cart item
    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'menuitem_id','menuitem', 'title', 'quantity', 'unit_price', 'total_price']
    
    def create(self, validated_data):
        user = self.context['request'].user
        menuitem = validated_data['menuitem']
        item_price = menuitem.price
        quantity = validated_data['quantity']
        cart = Cart.objects.filter(user=user,menuitem=menuitem).first()
        if cart:
                
                cart.quantity += quantity
                cart.total_price = cart.quantity * cart.unit_price
                cart.save()
        else:
                cart = Cart.objects.create(
                    user=user,
                    menuitem=menuitem,
                    unit_price=item_price,
                    quantity=quantity,
                    price=quantity*item_price
        )
        return cart
    def get_total(self, obj):
         return obj.quantity * obj.unit_price
    
class OrderItemSerializer(serializers.ModelSerializer):
    order = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    menuitem = MenuItemSerializer(read_only=True)
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.none(), write_only=True)

    class Meta:
        model = OrderItem
        #select menuItemfrom the cart 
        fields = ['order','menuitem','menuitem_id','quantity','price']
        extra_kwargs = {
             'quantity':{'read_only':True},
             'price':{'read_only':True}
        }
    #get the menuitem available from the user carts
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context['request'].user
        self.fields['menuitem_id'].queryset = MenuItem.objects.filter(cart__user=user)

    def create(self, validated_data):
        order = self.context['request'].user
        menuitem_id = validated_data['menuitem_id']
        cart = Cart.objects.filter(user=order, menuitem=menuitem_id).first()
        order_item = OrderItem.objects.create(order=order,menuitem=cart.menuitem,quantity=cart.quantity,unit_price=cart.unit_price,price=cart.price)

        cart.delete()
        return order_item
             

     
        

