from rest_framework import serializers
from .models import MenuItem, Category, Cart, Order, User, OrderItem
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
    
    def create(self, validated_data):
        category = validated_data.pop('category_id')
        menu_item = MenuItem.objects.create(category=category, **validated_data)
        return menu_item

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username']



class CartSerializer(serializers.ModelSerializer):
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    menuitem = MenuItemSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'menuitem_id', 'menuitem', 'quantity','price']
        extra_kwargs = {
        'price':{'read_only':True}
        }
    
    def create(self, validated_data):
        user = self.context['request'].user
        menuitem = validated_data['menuitem']
        quantity = validated_data.get('quantity', 1)

        cart_item, created = Cart.objects.get_or_create(user=user, menuitem=menuitem, 
            defaults={
            'quantity': quantity,
            'unit_price': menuitem.price,
            'price': menuitem.price * quantity
        })

        if not created:
            cart_item.quantity += quantity
            cart_item.price = cart_item.quantity * cart_item.unit_price
            cart_item.save()
        
        return cart_item
    

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(groups__name='Delivery Crew'), required=False)
    total = serializers.DecimalField(read_only=True,max_digits=100,decimal_places=3)
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'date', 'items','total']
    
    def create(self, validated_data):
        user = self.context['request'].user
        cart_items = Cart.objects.filter(user=user)

        if not cart_items.exists():
            raise serializers.ValidationError("No items in cart to create an order.")
        validated_data.pop('user')
        # Handle delivery_crew separately
        delivery_crew = validated_data.pop('delivery_crew', None)

        # Calculate the total before creating the order
        total = sum(cart_item.price for cart_item in cart_items)

        # Create the order with total value
        order = Order.objects.create(user=user, total=total, **validated_data)

        if delivery_crew:
            order.delivery_crew = delivery_crew
            order.save()

        order_items = []
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                menuitem=cart_item.menuitem,
                quantity=cart_item.quantity,
                unit_price=cart_item.menuitem.price,
                price=cart_item.price
            )
            order_items.append(order_item)
        OrderItem.objects.bulk_create(order_items)

        # Clear the cart
        cart_items.delete()

        return order

     
        

