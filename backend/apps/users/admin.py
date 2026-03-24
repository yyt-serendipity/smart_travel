from django.contrib import admin

from apps.users.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname", "home_city", "updated_at")
    search_fields = ("user__username", "nickname", "home_city")
