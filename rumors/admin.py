# rumors/admin.py
from django.contrib import admin
from .models import Rumors

@admin.register(Rumors)
class RumorsAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "pemain",
        "club_asal",
        "club_tujuan",
        "author",
        "status",
        "rumors_views",
        "created_at",
    )
    # Field yang bisa diklik untuk lihat detail
    list_display_links = ("title",)

    list_filter = ("status", "club_asal", "club_tujuan", "author")

    search_fields = (
        "title",
        "pemain__nama_pemain",
        "club_asal__name",
        "club_tujuan__name",
        "author__username",
    )
    ordering = ("-created_at",)

    #biar gak bisa diubah manual dari admin
    readonly_fields = (
        "id",
        "title",
        "created_at",
        "rumors_views",
    )
    #tampilan detail
    fieldsets = (
        ("Informasi Utama", {
            "fields": ("author", "pemain", "club_asal", "club_tujuan", "content")
        }),
        ("Status & Statistik", {
            "fields": ("status", "title", "rumors_views", "created_at"),
        }),
    )
