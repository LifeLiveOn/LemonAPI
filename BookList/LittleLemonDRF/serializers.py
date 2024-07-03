from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, User
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
    category_id = serializers.PrimaryKeyRelatedField(queryset = Category.objects.all())
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
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem')
    title = serializers.CharField(source='menuitem.title', read_only=True)
    unit_price = serializers.DecimalField(source='menuitem.price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # Total price of the cart item

    class Meta:
        model = Cart
        fields = ['id', 'user_id', 'menuitem_id', 'title', 'quantity', 'unit_price', 'total_price']
        extra_kwargs = {
            'unit_price': {'read_only': True},
            'price': {'read_only': True},
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        menuitem = validated_data['menuitem']
        item_price = menuitem.price
        quantity = validated_data['quantity']
        total_price = item_price * quantity
        cart = Cart.objects.filter(user=user,menuitem=menuitem).first()
        if cart:
                
                cart.quantity += quantity
                cart.save()
        else:
                cart = Cart.objects.create(
                    user=user,
                    menuitem=menuitem,
                    unit_price=item_price,
                    quantity=quantity,
                    price=total_price
        )
        return cart
        

