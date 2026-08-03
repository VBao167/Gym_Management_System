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
        "quan-tri/hoi-vien/",
        views.danh_sach_hoi_vien,
        name="danh_sach_hoi_vien",
    ),
    path(
    "quan-tri/hoi-vien/them-moi/",
    views.tao_hoi_vien_moi,
    name="tao_hoi_vien_moi",
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