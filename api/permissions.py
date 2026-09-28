from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsDoctorOwnerOrReadOnly(BasePermission):
    """Doctors are visible to all authenticated users, but only their creator can edit them."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.created_by == request.user
