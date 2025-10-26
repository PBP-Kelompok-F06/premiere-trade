from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, Profile

# Register your models here.

class ProfileInline(admin.StackedInline):
    model = Profile
    fields = ['managed_club']
    can_delete = False
    verbose_name_plural = 'Profile Info'
    fk_name = 'user'


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    list_display = (
        'username', 
        'is_fan', 
        'is_club_admin', 
        'is_staff', 
        'is_active',
        'get_managed_club' 
    )
    
    list_filter = (
        'is_fan', 
        'is_club_admin', 
        'is_staff', 
        'is_superuser', 
        'is_active'
    )
    
    search_fields = ('username',)
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Tipe Pengguna', {'fields': ('is_fan', 'is_club_admin')}), 
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def get_managed_club(self, obj):
        try:
            return obj.profile.managed_club.name if obj.profile.managed_club else 'N/A'
        except Profile.DoesNotExist:
            return 'N/A (No Profile)'
    
    get_managed_club.short_description = 'Managed Club'