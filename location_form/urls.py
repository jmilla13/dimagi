from django.contrib import admin
from django.urls import path, re_path
from location_form_app.views import (
    api_get_user_locations,
    api_update_location,
    form_view,
    map_view,
    normalized_data_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", map_view, name="home"),
    path("remote-location-form/", form_view, name="form"),
    path("map/", map_view, name="map"),
    path("normalized-data/", normalized_data_view, name="normalized_data"),
    path("api/locations/", api_update_location, name="api_update_location"),
    path("api/locations/<str:email>/", api_get_user_locations, name="api_get_user_locations"),
    path("api/search/", api_get_user_locations, name="api_search_locations"),
    re_path(r"^.*$", form_view, name="catch_all"),
]
