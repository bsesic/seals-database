from django.urls import path

from documents import views

app_name = "documents"

urlpatterns = [
    path("", views.DocumentListView.as_view(), name="list"),
    path("new/", views.DocumentCreateView.as_view(), name="create"),
    path("activity/", views.ActivityListView.as_view(), name="activity"),
    path("<int:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.DocumentUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.DocumentDeleteView.as_view(), name="delete"),
    path(
        "<int:pk>/transition/<str:action>/",
        views.DocumentTransitionView.as_view(),
        name="transition",
    ),
]
