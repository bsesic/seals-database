from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.ArtefactListView.as_view(), name="artefact-list"),
    path("map/", views.ArtefactMapView.as_view(), name="artefact-map"),
    path("stats/", views.StatisticsView.as_view(), name="statistics"),
    path("rdf/", views.DatasetRDFView.as_view(), name="rdf-dump"),
    path("<slug:slug>/", views.ArtefactDetailView.as_view(), name="artefact-detail"),
    path("<slug:slug>/rdf/", views.ArtefactRDFView.as_view(), name="artefact-rdf"),
]
