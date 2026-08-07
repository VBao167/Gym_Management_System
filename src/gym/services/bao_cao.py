from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

from gym.models import (
    BuoiTapPT,
    DangKyGoiTap,
    DiemDanh,
    HoaDon,
)

def _tao_khoang_thoi_gian(tu_ngay, den_ngay):
    bat_dau = datetime.combine(
        tu_ngay,
        time.min,
    )

    ket_thuc = datetime.combine(
        den_ngay + timedelta(days=1),
        time.min,
    )

    mui_gio = timezone.get_current_timezone()

    bat_dau = timezone.make_aware(
        bat_dau,
        mui_gio,
    )
    ket_thuc = timezone.make_aware(
        ket_thuc,
        mui_gio,
    )

    return bat_dau, ket_thuc


def lay_thong_ke_bao_cao(
    *,
    tu_ngay,
    den_ngay,
):
    if tu_ngay > den_ngay:
        raise ValueError(
            "Từ ngày không được sau Đến ngày."
        )

    bat_dau, ket_thuc = _tao_khoang_thoi_gian(
        tu_ngay,
        den_ngay,
    )

    tong_doanh_thu = (
        HoaDon.objects
        .filter(
            ngay_lap__gte=bat_dau,
            ngay_lap__lt=ket_thuc,
        )
        .aggregate(
            tong=Sum("tong_tien")
        )["tong"]
        or Decimal("0.00")
    )

    so_dang_ky_goi = (
        DangKyGoiTap.objects
        .filter(
            ngay_dang_ky__range=(
                tu_ngay,
                den_ngay,
            )
        )
        .count()
    )

    so_luot_diem_danh = (
        DiemDanh.objects
        .filter(
            thoi_gian_diem_danh__gte=bat_dau,
            thoi_gian_diem_danh__lt=ket_thuc,
        )
        .count()
    )

    thong_ke_buoi_pt = (
        BuoiTapPT.objects
        .filter(
            ngay_tap__range=(
                tu_ngay,
                den_ngay,
            )
        )
        .aggregate(
            tong_buoi_pt=Count("pk"),
            so_buoi_da_len_lich=Count(
                "pk",
                filter=Q(
                    trang_thai=(
                        BuoiTapPT.TrangThai.DA_LEN_LICH
                    )
                ),
            ),
            so_buoi_hoan_thanh=Count(
                "pk",
                filter=Q(
                    trang_thai=(
                        BuoiTapPT.TrangThai.HOAN_THANH
                    )
                ),
            ),
            so_buoi_vang=Count(
                "pk",
                filter=Q(
                    trang_thai=(
                        BuoiTapPT.TrangThai.VANG
                    )
                ),
            ),
            so_buoi_huy=Count(
                "pk",
                filter=Q(
                    trang_thai=(
                        BuoiTapPT.TrangThai.HUY
                    )
                ),
            ),
        )
    )

    return {
        "tong_doanh_thu": tong_doanh_thu,
        "so_dang_ky_goi": so_dang_ky_goi,
        "so_luot_diem_danh": so_luot_diem_danh,
        **thong_ke_buoi_pt,
    }