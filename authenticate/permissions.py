from rest_framework import permissions
from rest_framework_simplejwt.tokens import AccessToken
class IsOwnerOrReadonly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return False
    
class IsAuthenticatedAndTokenValid(permissions.IsAuthenticated):
    def has_permission(self, request, view):
        is_authenticated = super().has_permission(request, view)
        if not is_authenticated:
            return False

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                access_token = AccessToken(token)
                if access_token.blacklisted():
                    return False
            except:
                return False
        return True