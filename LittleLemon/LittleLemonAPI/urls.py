from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter(trailing_slash=False)
router.register('menu-items',views.MenuItemView)
router.register('groups/manager/users',views.ManagerUserView)
router.register('groups/delivery_crew/users',views.deliveryCrewUserView, basename='delivery_crew')
router.register('cart/menu-items', views.CartAPIView, basename='cart')
router.register('category',views.CategoryView,basename='category')
router.register('orders',views.OrderView,basename='orders')
urlpatterns = [
    path('',include(router.urls)),

]

