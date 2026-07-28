from django import forms
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

from .services.nguoi_dung import (
    tao_hoi_vien_tu_doi_tuong,
    tao_huan_luyen_vien_tu_doi_tuong,
    tao_le_tan_tu_doi_tuong,
)

from .services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don_tu_doi_tuong,
)


admin.site.site_header = "Hệ thống Quản lý Phòng Gym"
admin.site.site_title = "Gym Management"
admin.site.index_title = "Trang quản trị hệ thống"

class HoSoNguoiDungAdmin(admin.ModelAdmin):
    truong_ma = ""
    cac_truong_ho_so = ()
    khoa_tai_khoan_khi_ngung_hoat_dong = True

    def get_fields(self, request, obj=None):
        fields = [self.truong_ma]

        if obj:
            fields.append("tai_khoan")

        fields.extend(self.cac_truong_ho_so)
        return tuple(fields)

    def get_readonly_fields(self, request, obj=None):
        fields = [self.truong_ma]

        if obj:
            fields.append("tai_khoan")

        return tuple(fields)

    def save_model(self, request, obj, form, change):
        if not change:
            self.tao_ho_so_tu_doi_tuong(obj)
            return

        super().save_model(request, obj, form, change)

        # Chỉ tự khóa tài khoản đối với hồ sơ nhân viên.
        # Hồ sơ hoạt động lại không tự mở tài khoản.
        if (
            self.khoa_tai_khoan_khi_ngung_hoat_dong
            and not obj.trang_thai
            and obj.tai_khoan.is_active
        ):
            obj.tai_khoan.is_active = False
            obj.tai_khoan.save(update_fields=["is_active"])

    def tao_ho_so_tu_doi_tuong(self, obj):
        raise NotImplementedError


@admin.register(HoiVien)
class HoiVienAdmin(HoSoNguoiDungAdmin):
    truong_ma = "ma_hv"
    khoa_tai_khoan_khi_ngung_hoat_dong = False
    cac_truong_ho_so = (
        "ho_ten",
        "gioi_tinh",
        "ngay_sinh",
        "sdt",
        "email",
        "dia_chi",
        "ngay_tham_gia",
        "trang_thai",
    )

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
    list_select_related = ("tai_khoan",)
    ordering = ("ma_hv",)
    list_per_page = 25

    def tao_ho_so_tu_doi_tuong(self, obj):
        tao_hoi_vien_tu_doi_tuong(obj)

    def get_readonly_fields(self, request, obj=None):
        fields = list(
            super().get_readonly_fields(request, obj)
        )

        if "trang_thai" not in fields:
            fields.append("trang_thai")

        return tuple(fields)


@admin.register(LeTan)
class LeTanAdmin(HoSoNguoiDungAdmin):
    truong_ma = "ma_lt"
    cac_truong_ho_so = (
        "ho_ten",
        "gioi_tinh",
        "ngay_sinh",
        "sdt",
        "email",
        "dia_chi",
        "ngay_vao_lam",
        "trang_thai",
    )

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
    list_select_related = ("tai_khoan",)
    ordering = ("ma_lt",)
    list_per_page = 25

    def tao_ho_so_tu_doi_tuong(self, obj):
        tao_le_tan_tu_doi_tuong(obj)


@admin.register(HuanLuyenVien)
class HuanLuyenVienAdmin(HoSoNguoiDungAdmin):
    truong_ma = "ma_pt"
    cac_truong_ho_so = (
        "ho_ten",
        "gioi_tinh",
        "ngay_sinh",
        "sdt",
        "email",
        "dia_chi",
        "ngay_vao_lam",
        "trang_thai",
    )

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
    list_select_related = ("tai_khoan",)
    ordering = ("ma_pt",)
    list_per_page = 25

    def tao_ho_so_tu_doi_tuong(self, obj):
        tao_huan_luyen_vien_tu_doi_tuong(obj)


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

class DangKyGoiTapTaoForm(forms.ModelForm):
    le_tan_lap_hoa_don = forms.ModelChoiceField(
        queryset=LeTan.objects.filter(trang_thai=True),
        label="Lễ tân lập hóa đơn",
    )

    phuong_thuc_thanh_toan = forms.ChoiceField(
        choices=HoaDon.PhuongThucThanhToan.choices,
        label="Phương thức thanh toán",
    )

    ghi_chu_hoa_don = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú hóa đơn",
    )

    class Meta:
        model = DangKyGoiTap
        fields = (
            "hoi_vien",
            "goi_tap",
            "ngay_dang_ky",
            "ngay_bat_dau",
            "ghi_chu",
        )

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
        "ma_dk",
        "ngay_ket_thuc",
        "so_buoi_pt_dang_ky",
        "trang_thai",
        "hien_thi_hoa_don",
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

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = DangKyGoiTapTaoForm

        return super().get_form(
            request,
            obj,
            **kwargs,
        )

    def get_fields(self, request, obj=None):
        fields = [
            "ma_dk",
            "hoi_vien",
            "goi_tap",
            "ngay_dang_ky",
            "ngay_bat_dau",
            "ngay_ket_thuc",
            "so_buoi_pt_dang_ky",
            "trang_thai",
            "ghi_chu",
        ]

        if obj is None:
            fields.extend(
                [
                    "le_tan_lap_hoa_don",
                    "phuong_thuc_thanh_toan",
                    "ghi_chu_hoa_don",
                ]
            )
        else:
            fields.append("hien_thi_hoa_don")

        fields.extend(
            [
                "hien_thi_so_buoi_da_dung",
                "hien_thi_so_buoi_da_len_lich",
                "hien_thi_so_buoi_con_lai",
                "hien_thi_so_buoi_co_the_xep",
            ]
        )

        return tuple(fields)

    def get_readonly_fields(self, request, obj=None):
        fields = list(
            super().get_readonly_fields(request, obj)
        )

        if obj is not None:
            fields.extend(
                [
                    "hoi_vien",
                    "goi_tap",
                    "ngay_dang_ky",
                    "ngay_bat_dau",
                ]
            )

        return tuple(fields)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if not change:
            tao_dang_ky_va_hoa_don_tu_doi_tuong(
                dang_ky=obj,
                le_tan=form.cleaned_data[
                    "le_tan_lap_hoa_don"
                ],
                phuong_thuc_thanh_toan=form.cleaned_data[
                    "phuong_thuc_thanh_toan"
                ],
                ghi_chu_hoa_don=form.cleaned_data[
                    "ghi_chu_hoa_don"
                ],
            )
            return

        super().save_model(
            request,
            obj,
            form,
            change,
        )

    @admin.display(description="Hóa đơn")
    def hien_thi_hoa_don(self, obj):
        if not obj or not obj.pk:
            return "-"

        try:
            return obj.hoa_don
        except HoaDon.DoesNotExist:
            return "Không có hóa đơn — dữ liệu không hợp lệ"


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
    readonly_fields = (
        "ma_hd",
        "dang_ky",
        "le_tan",
        "ngay_lap",
        "tong_tien",
        "phuong_thuc_thanh_toan",
        "ghi_chu",
    )
    date_hierarchy = "ngay_lap"
    ordering = ("-ngay_lap", "ma_hd")
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
    readonly_fields = ("ma_buoi",)
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
    readonly_fields = ("ma_dd", "thoi_gian_diem_danh",)
    date_hierarchy = "thoi_gian_diem_danh"
    ordering = ("-thoi_gian_diem_danh", "ma_dd")
    list_per_page = 25
