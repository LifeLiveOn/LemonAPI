from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsManager(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Manager').exists():
            return True
        return False

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Delivery Crew').exists():
            return True
        return False

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        return False
