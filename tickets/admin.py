from django.contrib import admin
from .models import Ticket, Wallet

# Register your models here.


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Status', {'fields': ('status',)}),
        ('Details', {'fields': ('id', 'start', 'stop', 'created_at', 'expired'), 'classes': ('collapse',)})
    )
    list_display = ('user', 'start', 'stop', 'created_at', 'status')
    list_select_related = ('user', 'start', 'stop')
    readonly_fields = ('id', 'user', 'created_at', 'expired')
    search_fields = ('id', 'user__username', 'start__name', 'stop__name')
    ordering = ('-created_at',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user', 'balance')}),
    )
    readonly_fields = ('user',)
    list_display = ('user', 'balance')
    search_fields = ('user__username',)
    ordering = ('user__username',)
