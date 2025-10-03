from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account, LoggedInUser

class AccountAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'last_login', 'date_joined', 'is_active')
    list_display_links = ('email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

class LoggedInUserAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'last_login')
    readonly_fields = ('last_login',)
    ordering = ('-last_login',)

admin.site.register(Account, AccountAdmin)
admin.site.register(LoggedInUser, LoggedInUserAdmin)
