from rest_framework.permissions import  BasePermission
from rest_framework.exceptions import PermissionDenied

class IsManager(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.groups.filter(name='Manager').exists():
            return True
        raise PermissionDenied("You do not have permission to perform this action", 403)

class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.group.filter(name='Delivery Crew').exists():
            return True
        raise PermissionDenied("You do not have permission to perform this action", 403)