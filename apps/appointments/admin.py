from django.contrib import admin

from apps.appointments.models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("appointment_id", "patient", "service", "date", "time", "status")
    list_filter = ("status", "date")
    search_fields = ("appointment_id", "patient__first_name", "patient__last_name")
    ordering = ("-date", "-time")
