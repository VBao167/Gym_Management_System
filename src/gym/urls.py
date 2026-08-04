from django.urls import path

from . import views


app_name = "gym"

urlpatterns = [
    path(
        "quan-tri/",
        views.trang_quan_tri,
        name="trang_quan_tri",
    ),

    # Quản lý Hội viên
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
        "quan-tri/hoi-vien/<str:ma_hv>/chinh-sua/",
        views.chinh_sua_hoi_vien,
        name="chinh_sua_hoi_vien",
    ),
    path(
        (
            "quan-tri/hoi-vien/<str:ma_hv>/"
            "doi-trang-thai-tai-khoan/"
        ),
        views.doi_trang_thai_tai_khoan_hoi_vien,
        name="doi_trang_thai_tai_khoan_hoi_vien",
    ),
    path(
        "quan-tri/hoi-vien/<str:ma_hv>/",
        views.chi_tiet_hoi_vien,
        name="chi_tiet_hoi_vien",
    ),

    # Quản lý Gói tập
    path(
        "quan-tri/goi-tap/",
        views.danh_sach_goi_tap,
        name="danh_sach_goi_tap",
    ),
    path(
        "quan-tri/goi-tap/them-moi/",
        views.tao_goi_tap_moi,
        name="tao_goi_tap_moi",
    ),
    path(
        "quan-tri/goi-tap/<str:ma_goi>/chinh-sua/",
        views.chinh_sua_goi_tap,
        name="chinh_sua_goi_tap",
    ),
    path(
        "quan-tri/goi-tap/<str:ma_goi>/doi-trang-thai/",
        views.doi_trang_thai_goi_tap,
        name="doi_trang_thai_goi_tap",
    ),

    # Trang chính theo vai trò
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