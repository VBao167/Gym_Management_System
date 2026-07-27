from django.contrib import admin

from .models import (
    BuoiTapPT,
    DangKyGoiTap,
    DiemDanh,
    GoiTap,
    HoaDon,
    HoiVien,
    HuanLuyenVien,
    LeTan,
)


admin.site.site_header = "Hệ thống Quản lý Phòng Gym"
admin.site.site_title = "Gym Management"
admin.site.index_title = "Trang quản trị hệ thống"


@admin.register(HoiVien)
class HoiVienAdmin(admin.ModelAdmin):
    readonly_fields = ("ma_hv",)
    list_display = (
        "ma_hv",
        "ho_ten",
        "tai_khoan",
        "sdt",
        "ngay_tham_gia",
        "trang_thai",
    )
    list_filter = ("trang_thai", "gioi_tinh", "ngay_tham_gia")
    search_fields = (
        "ma_hv",
        "ho_ten",
        "sdt",
        "email",
        "tai_khoan__username",
    )
    autocomplete_fields = ("tai_khoan",)
    list_select_related = ("tai_khoan",)
    ordering = ("ma_hv",)
    list_per_page = 25


@admin.register(LeTan)
class LeTanAdmin(admin.ModelAdmin):
    readonly_fields = ("ma_lt",)
    list_display = (
        "ma_lt",
        "ho_ten",
        "tai_khoan",
        "sdt",
        "ngay_vao_lam",
        "trang_thai",
    )
    list_filter = ("trang_thai", "gioi_tinh", "ngay_vao_lam")
    search_fields = (
        "ma_lt",
        "ho_ten",
        "sdt",
        "email",
        "tai_khoan__username",
    )
    autocomplete_fields = ("tai_khoan",)
    list_select_related = ("tai_khoan",)
    ordering = ("ma_lt",)
    list_per_page = 25


@admin.register(HuanLuyenVien)
class HuanLuyenVienAdmin(admin.ModelAdmin):
    readonly_fields = ("ma_pt",)
    list_display = (
        "ma_pt",
        "ho_ten",
        "tai_khoan",
        "sdt",
        "ngay_vao_lam",
        "trang_thai",
    )
    list_filter = ("trang_thai", "gioi_tinh", "ngay_vao_lam")
    search_fields = (
        "ma_pt",
        "ho_ten",
        "sdt",
        "email",
        "tai_khoan__username",
    )
    autocomplete_fields = ("tai_khoan",)
    list_select_related = ("tai_khoan",)
    ordering = ("ma_pt",)
    list_per_page = 25


@admin.register(GoiTap)
class GoiTapAdmin(admin.ModelAdmin):
    list_display = (
        "ma_goi",
        "ten_goi",
        "thoi_han_ngay",
        "gia_tien",
        "co_pt",
        "so_buoi_pt",
        "trang_thai",
    )
    list_filter = ("trang_thai", "co_pt")
    search_fields = ("ma_goi", "ten_goi")
    ordering = ("ma_goi",)
    list_per_page = 25


@admin.register(DangKyGoiTap)
class DangKyGoiTapAdmin(admin.ModelAdmin):
    list_display = (
        "ma_dk",
        "hoi_vien",
        "goi_tap",
        "ngay_bat_dau",
        "ngay_ket_thuc",
        "trang_thai",
        "hien_thi_so_buoi_con_lai",
        "hien_thi_so_buoi_co_the_xep",
    )
    list_filter = (
        "trang_thai",
        "goi_tap",
        "ngay_bat_dau",
    )
    search_fields = (
        "ma_dk",
        "hoi_vien__ma_hv",
        "hoi_vien__ho_ten",
        "goi_tap__ma_goi",
        "goi_tap__ten_goi",
    )
    autocomplete_fields = ("hoi_vien", "goi_tap")
    list_select_related = ("hoi_vien", "goi_tap")
    readonly_fields = (
        "ngay_ket_thuc",
        "so_buoi_pt_dang_ky",
        "trang_thai",
        "hien_thi_so_buoi_da_dung",
        "hien_thi_so_buoi_da_len_lich",
        "hien_thi_so_buoi_con_lai",
        "hien_thi_so_buoi_co_the_xep",
    )
    date_hierarchy = "ngay_dang_ky"
    ordering = ("-ngay_dang_ky", "ma_dk")
    list_per_page = 25

    @admin.display(description="Số buổi đã dùng")
    def hien_thi_so_buoi_da_dung(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.so_buoi_pt_da_dung

    @admin.display(description="Số buổi đã lên lịch")
    def hien_thi_so_buoi_da_len_lich(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.so_buoi_pt_da_len_lich

    @admin.display(description="Số buổi còn lại")
    def hien_thi_so_buoi_con_lai(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.so_buoi_pt_con_lai

    @admin.display(description="Có thể xếp thêm")
    def hien_thi_so_buoi_co_the_xep(self, obj):
        if not obj or not obj.pk:
            return 0
        return obj.so_buoi_pt_co_the_xep_lich


@admin.register(HoaDon)
class HoaDonAdmin(admin.ModelAdmin):
    list_display = (
        "ma_hd",
        "dang_ky",
        "le_tan",
        "ngay_lap",
        "tong_tien",
        "phuong_thuc_thanh_toan",
    )
    list_filter = (
        "phuong_thuc_thanh_toan",
        "ngay_lap",
    )
    search_fields = (
        "ma_hd",
        "dang_ky__ma_dk",
        "dang_ky__hoi_vien__ma_hv",
        "dang_ky__hoi_vien__ho_ten",
        "le_tan__ma_lt",
        "le_tan__ho_ten",
    )
    autocomplete_fields = ("dang_ky", "le_tan")
    list_select_related = ("dang_ky", "le_tan")
    readonly_fields = ("ngay_lap", "tong_tien")
    date_hierarchy = "ngay_lap"
    ordering = ("-ngay_lap", "ma_hd")
    list_per_page = 25


@admin.register(BuoiTapPT)
class BuoiTapPTAdmin(admin.ModelAdmin):
    list_display = (
        "ma_buoi",
        "dang_ky",
        "huan_luyen_vien",
        "ngay_tap",
        "gio_bat_dau",
        "gio_ket_thuc",
        "trang_thai",
    )
    list_filter = (
        "trang_thai",
        "ngay_tap",
        "huan_luyen_vien",
    )
    search_fields = (
        "ma_buoi",
        "dang_ky__ma_dk",
        "dang_ky__hoi_vien__ma_hv",
        "dang_ky__hoi_vien__ho_ten",
        "huan_luyen_vien__ma_pt",
        "huan_luyen_vien__ho_ten",
    )
    autocomplete_fields = (
        "dang_ky",
        "huan_luyen_vien",
        "le_tan",
    )
    list_select_related = (
        "dang_ky",
        "huan_luyen_vien",
        "le_tan",
    )
    date_hierarchy = "ngay_tap"
    ordering = ("-ngay_tap", "-gio_bat_dau", "ma_buoi")
    list_per_page = 25


@admin.register(DiemDanh)
class DiemDanhAdmin(admin.ModelAdmin):
    list_display = (
        "ma_dd",
        "hoi_vien",
        "le_tan",
        "thoi_gian_diem_danh",
    )
    list_filter = (
        "thoi_gian_diem_danh",
        "le_tan",
    )
    search_fields = (
        "ma_dd",
        "hoi_vien__ma_hv",
        "hoi_vien__ho_ten",
        "le_tan__ma_lt",
        "le_tan__ho_ten",
    )
    autocomplete_fields = ("hoi_vien", "le_tan")
    list_select_related = ("hoi_vien", "le_tan")
    readonly_fields = ("thoi_gian_diem_danh",)
    date_hierarchy = "thoi_gian_diem_danh"
    ordering = ("-thoi_gian_diem_danh", "ma_dd")
    list_per_page = 25