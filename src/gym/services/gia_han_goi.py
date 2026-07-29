from datetime import timedelta

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from gym.models import DangKyGoiTap
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)


def tinh_ngay_bat_dau_gia_han(
    *,
    hoi_vien,
    ngay_dang_ky,
):
    """
    Tính ngày bắt đầu của đăng ký nối tiếp.

    Nếu Hội viên không còn gói tại ngày đăng ký,
    gói mới bắt đầu ngay từ ngày đăng ký.
    """
    ngay_ket_thuc_muon_nhat = (
        DangKyGoiTap.objects.filter(
            hoi_vien=hoi_vien,
        ).aggregate(
            ngay_cuoi=Max("ngay_ket_thuc"),
        )["ngay_cuoi"]
    )

    if (
        ngay_ket_thuc_muon_nhat is None
        or ngay_ket_thuc_muon_nhat < ngay_dang_ky
    ):
        return ngay_dang_ky

    return ngay_ket_thuc_muon_nhat + timedelta(days=1)


@transaction.atomic
def gia_han_goi(
    *,
    hoi_vien,
    goi_tap,
    le_tan,
    phuong_thuc_thanh_toan,
    ngay_dang_ky=None,
    ghi_chu_dang_ky="",
    ghi_chu_hoa_don="",
):
    """
    Tạo đăng ký gói nối tiếp và hóa đơn tương ứng.
    """
    if ngay_dang_ky is None:
        ngay_dang_ky = timezone.localdate()

    ngay_bat_dau = tinh_ngay_bat_dau_gia_han(
        hoi_vien=hoi_vien,
        ngay_dang_ky=ngay_dang_ky,
    )

    return tao_dang_ky_va_hoa_don(
        hoi_vien=hoi_vien,
        goi_tap=goi_tap,
        le_tan=le_tan,
        ngay_dang_ky=ngay_dang_ky,
        ngay_bat_dau=ngay_bat_dau,
        phuong_thuc_thanh_toan=phuong_thuc_thanh_toan,
        ghi_chu_dang_ky=ghi_chu_dang_ky,
        ghi_chu_hoa_don=ghi_chu_hoa_don,
    )
