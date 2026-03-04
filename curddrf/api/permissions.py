from rest_framework import permissions


class IsOrganizationMember(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'profile') or not request.user.profile.organization:
            return False
        
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.profile.organization

        if obj.__class__.__name__ == 'Organization':
            return obj == request.user.profile.organization
        
        return False


class IsOrganizationAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not hasattr(request.user, 'profile'):
            return False
        return request.user.profile.is_admin()
    
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'profile'):
            return False
        
        if not request.user.profile.is_admin():
            return False
        
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.profile.organization
        
        if obj.__class__.__name__ == 'Organization':
            return obj == request.user.profile.organization
        
        return False


class CanManageCustomers(permissions.BasePermission):
   
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if not hasattr(request.user, 'profile'):
            return False
        
        return request.user.profile.can_manage_customers()
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'organization'):
                return obj.organization == request.user.profile.organization
        
        if not hasattr(request.user, 'profile'):
            return False
        
        if not request.user.profile.can_manage_customers():
            return False
        
        if hasattr(obj, 'organization'):
            return obj.organization == request.user.profile.organization
        
        return False
