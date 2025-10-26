from django.contrib import admin
from player_transaction.models import Negotiation
from main.models import Player, Club
from django.utils.html import format_html

@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "player",
        "from_club",
        "to_club",
        "offered_price",
        "colored_status",
        "created_at",
    )

    list_filter = ("status", "from_club", "to_club", "created_at")
    search_fields = ("player__nama_pemain", "from_club__name", "to_club__name")
    ordering = ("-created_at",)
    list_per_page = 20
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
                "player",
                ("from_club", "to_club"),
                "offered_price",
                "status",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at",),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request):
        """Boleh buat negosiasi manual"""
        return True

    def colored_status(self, obj):
        color_map = {
            "pending": "orange",
            "accepted": "green",
            "rejected": "red",
            "cancelled": "gray",
        }
        color = color_map.get(obj.status, "black")
        return format_html(f"<b style='color:{color}'>{obj.get_status_display()}</b>")
    colored_status.short_description = "Status"

    # 💡 Custom dropdown filtering
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player":
            # Hanya tampilkan pemain yang sedang dijual
            kwargs["queryset"] = Player.objects.filter(sedang_dijual=True).select_related("current_club")

        elif db_field.name == "to_club":
            # Hanya tampilkan klub yang memiliki pemain yang sedang dijual
            kwargs["queryset"] = Club.objects.filter(players__sedang_dijual=True).distinct()

        elif db_field.name == "from_club":
            # Hanya tampilkan klub yang berbeda dengan klub penerima (jika to_club sudah dipilih)
            kwargs["queryset"] = Club.objects.all()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Opsional: validasi ringan di level simpan
    def save_model(self, request, obj, form, change):
        if obj.from_club == obj.to_club:
            from django.core.exceptions import ValidationError
            raise ValidationError("Klub pengirim dan penerima tidak boleh sama.")

        # Pastikan pemain yang dipilih memang berasal dari klub penerima
        if obj.player.current_club != obj.to_club:
            obj.to_club = obj.player.current_club  # otomatis disesuaikan
        super().save_model(request, obj, form, change)



