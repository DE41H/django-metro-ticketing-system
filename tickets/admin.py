from django.contrib import admin
from .models import Ticket

# Register your models here.


class TicketAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {'fields': ['id', 'user']}),
        ('Details', {'fields': ['start', 'stop', 'created_at'], 'classes': ['collapse']}),
    ]
    list_display = ['id', 'start', 'stop', 'created_at', 'user']
    search_fields = ['id']


admin.site.register(Ticket, TicketAdmin)
