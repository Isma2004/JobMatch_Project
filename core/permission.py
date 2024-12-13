from rest_framework import permissions

class IsCandidate(permissions.BasePermission):
    # Custom permission to check if the user is a candidate
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_candidate)

class IsHRManager(permissions.BasePermission):
    # Custom permission to check if the user is an HR manager
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_hr_manager)
    
class IsCandidateOrHRManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_candidate or request.user.is_hr_manager)