from django.urls import path

from . import views


app_name = "gym"

urlpatterns = [
    path(
        "quan-tri/",
        views.trang_quan_tri,
        name="trang_quan_tri",
    ),
    path(
        "le-tan/",
        views.trang_le_tan,
        name="trang_le_tan",
    ),
    path(
        "pt/",
        views.trang_pt,
        name="trang_pt",
    ),
    path(
        "hoi-vien/",
        views.trang_hoi_vien,
        name="trang_hoi_vien",
    ),
]