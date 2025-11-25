from django.contrib import admin
from django.http import HttpRequest
from django.template.response import TemplateResponse
from .models import Ticket, Wallet

# Register your models here.


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user',)}),
        ('Status', {'fields': ('raw_status',)}),
        ('Details', {'fields': ('id', 'start', 'stop', 'created_at'), 'classes': ('collapse',)})
    )
    list_display = ('user', 'start', 'stop', 'created_at', 'raw_status')
    list_select_related = ('user', 'start', 'stop')
    readonly_fields = ('id', 'user', 'created_at')
    search_fields = ('id', 'user__username', 'start__name', 'stop__name')
    ordering = ('-created_at',)

    def changelist_view(self, request: HttpRequest, extra_context: dict[str, str] | None = ...) -> TemplateResponse: # type: ignore
        Ticket.bulk_update_ticket_expiry()
        return super().changelist_view(request, extra_context)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('user', 'balance')}),
    )
    readonly_fields = ('user',)
    list_display = ('user', 'balance')
    search_fields = ('user__username',)
    ordering = ('user__username',)
