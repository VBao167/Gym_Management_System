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

    # Quản lý Nhân viên
    path(
        "quan-tri/nhan-vien/",
        views.danh_sach_nhan_vien,
        name="danh_sach_nhan_vien",
    ),
    path(
        (
            "quan-tri/nhan-vien/them-moi/"
            "<slug:loai_nhan_vien>/"
        ),
        views.tao_nhan_vien_moi,
        name="tao_nhan_vien_moi",
    ),
    path(
        (
            "quan-tri/nhan-vien/"
            "<slug:loai_nhan_vien>/"
            "<str:ma_nhan_vien>/chinh-sua/"
        ),
        views.chinh_sua_nhan_vien,
        name="chinh_sua_nhan_vien",
    ),
    path(
        (
            "quan-tri/nhan-vien/"
            "<slug:loai_nhan_vien>/"
            "<str:ma_nhan_vien>/"
            "doi-trang-thai-lam-viec/"
        ),
        views.doi_trang_thai_lam_viec_nhan_vien,
        name="doi_trang_thai_lam_viec_nhan_vien",
    ),
    path(
        (
            "quan-tri/nhan-vien/"
            "<slug:loai_nhan_vien>/"
            "<str:ma_nhan_vien>/"
            "doi-trang-thai-tai-khoan/"
        ),
        views.doi_trang_thai_tai_khoan_nhan_vien,
        name="doi_trang_thai_tai_khoan_nhan_vien",
    ),
    path(
        (
            "quan-tri/nhan-vien/"
            "<slug:loai_nhan_vien>/"
            "<str:ma_nhan_vien>/"
        ),
        views.chi_tiet_nhan_vien,
        name="chi_tiet_nhan_vien",
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

    # Đăng ký gói và hóa đơn
    path(
        "dang-ky-hoa-don/",
        views.danh_sach_dang_ky_hoa_don,
        name="danh_sach_dang_ky_hoa_don",
    ),
    path(
        "dang-ky-hoa-don/them-moi/",
        views.tao_dang_ky_hoa_don,
        name="tao_dang_ky_hoa_don",
    ),
    path(
        "dang-ky-hoa-don/<str:ma_dk>/",
        views.chi_tiet_dang_ky_hoa_don,
        name="chi_tiet_dang_ky_hoa_don",
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