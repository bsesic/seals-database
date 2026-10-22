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
router.register("seal-morphologies", catalog_api.SealMorphologyViewSet,
                basename="sealmorphology")
router.register("engraving-techniques", catalog_api.EngravingTechniqueViewSet,
                basename="engravingtechnique")
router.register("mounting-devices", catalog_api.MountingDeviceViewSet,
                basename="mountingdevice")
router.register("border-types", catalog_api.BorderTypeViewSet, basename="bordertype")
router.register("base-layouts", catalog_api.BaseLayoutViewSet, basename="baselayout")
router.register("surface-treatments", catalog_api.SurfaceTreatmentViewSet,
                basename="surfacetreatment")
router.register("colours", catalog_api.ColourViewSet, basename="colour")

urlpatterns = [
    path("users/me/", views.MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
