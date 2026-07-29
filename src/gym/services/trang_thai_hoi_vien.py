from django.db import transaction
from django.utils import timezone

from gym.models import DangKyGoiTap, HoiVien


@transaction.atomic
def cap_nhat_trang_thai_hoi_vien(hoi_vien):
    """
    Đồng bộ trạng thái các đăng ký và trạng thái Hội viên
    theo ngày hiện tại.

    Hàm không khóa hoặc mở khóa tài khoản Hội viên.
    """
    if not hoi_vien.pk:
        raise ValueError(
            "Hội viên phải được lưu trước khi cập nhật trạng thái."
        )

    hom_nay = timezone.localdate()

    cac_dang_ky = DangKyGoiTap.objects.filter(
        hoi_vien=hoi_vien,
    )

    cac_dang_ky.filter(
        ngay_bat_dau__gt=hom_nay,
    ).exclude(
        trang_thai=DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
    ).update(
        trang_thai=DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
    )

    cac_dang_ky.filter(
        ngay_ket_thuc__lt=hom_nay,
    ).exclude(
        trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
    ).update(
        trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
    )

    cac_dang_ky.filter(
        ngay_bat_dau__lte=hom_nay,
        ngay_ket_thuc__gte=hom_nay,
    ).exclude(
        trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
    ).update(
        trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
    )

    co_goi_hoat_dong = cac_dang_ky.filter(
        ngay_bat_dau__lte=hom_nay,
        ngay_ket_thuc__gte=hom_nay,
    ).exists()

    HoiVien.objects.filter(
        pk=hoi_vien.pk,
    ).exclude(
        trang_thai=co_goi_hoat_dong,
    ).update(
        trang_thai=co_goi_hoat_dong,
    )

    hoi_vien.trang_thai = co_goi_hoat_dong

    return co_goi_hoat_dong
