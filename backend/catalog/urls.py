from django.urls import path

from catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.ArtefactListView.as_view(), name="artefact-list"),
    path("map/", views.ArtefactMapView.as_view(), name="artefact-map"),
    path("stats/", views.StatisticsView.as_view(), name="statistics"),
    path("rdf/", views.DatasetRDFView.as_view(), name="rdf-dump"),
    path("new/", views.ArtefactCreateView.as_view(), name="artefact-create"),
    path("mine/", views.MyArtefactListView.as_view(), name="artefact-mine"),
    path("<slug:slug>/", views.ArtefactDetailView.as_view(), name="artefact-detail"),
    path("<slug:slug>/rdf/", views.ArtefactRDFView.as_view(), name="artefact-rdf"),
    path("<slug:slug>/edit/", views.ArtefactUpdateView.as_view(), name="artefact-edit"),
]
