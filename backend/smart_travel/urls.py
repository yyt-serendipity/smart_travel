from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("site-admin/", admin.site.urls),
    path("api/", include("apps.users.urls")),
    path("api/", include("apps.destinations.urls")),
    path("api/", include("apps.planner.urls")),
    path("api/", include("apps.community.urls")),
    path("api/backoffice/", include("apps.backoffice.urls")),
]
