from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views
from catalog import api as catalog_api

app_name = "api"

router = DefaultRouter()
router.register("documents", views.DocumentViewSet, basename="document")
router.register("organizations", views.OrganizationViewSet, basename="organization")
router.register("notifications", views.NotificationViewSet, basename="notification")

# Public catalogue (read-only).
router.register("artefacts", catalog_api.ArtefactViewSet, basename="artefact")
router.register("findspots", catalog_api.FindspotViewSet, basename="findspot")
router.register("regions", catalog_api.RegionViewSet, basename="region")
router.register("periods", catalog_api.PeriodViewSet, basename="period")
router.register("object-types", catalog_api.ObjectTypeViewSet, basename="objecttype")
router.register("materials", catalog_api.MaterialViewSet, basename="material")
router.register("scripts", catalog_api.ScriptTypeViewSet, basename="scripttype")

urlpatterns = [
    path("users/me/", views.MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
