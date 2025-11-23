from django.contrib import admin
from .models import Ticket, Wallet

# Register your models here.


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Details', {'fields': ('start', 'stop', 'created_at', 'status', 'expired'), 'classes': ('collapse',)}),
    )
    list_display = ('user', 'start', 'stop', 'created_at', 'status', 'expired')
    search_fields = ('user',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user', 'balance')}),
    )
    readonly_fields = ('user',)
    list_display = ('user', 'balance')
    search_fields = ('user',)
