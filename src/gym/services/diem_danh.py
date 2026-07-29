from django.core.exceptions import ValidationError
from django.db import transaction

from gym.models import DiemDanh
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_hoi_vien,
)


def _tao_diem_danh(diem_danh):
    co_quyen_tap = cap_nhat_trang_thai_hoi_vien(
        diem_danh.hoi_vien,
    )

    if not co_quyen_tap:
        raise ValidationError(
            {
                "hoi_vien": (
                    "Hội viên không có gói tập đang hoạt động."
                )
            }
        )

    le_tan = diem_danh.le_tan

    if not le_tan.trang_thai:
        raise ValidationError(
            {
                "le_tan": (
                    "Lễ tân đã ngừng làm việc, "
                    "không thể thực hiện điểm danh."
                )
            }
        )

    if not le_tan.tai_khoan.is_active:
        raise ValidationError(
            {
                "le_tan": (
                    "Tài khoản Lễ tân đang bị khóa."
                )
            }
        )

    diem_danh.save()
    return diem_danh


@transaction.atomic
def tao_diem_danh(
    *,
    hoi_vien,
    le_tan,
    ghi_chu="",
):
    return _tao_diem_danh(
        DiemDanh(
            hoi_vien=hoi_vien,
            le_tan=le_tan,
            ghi_chu=ghi_chu,
        )
    )


@transaction.atomic
def tao_diem_danh_tu_doi_tuong(diem_danh):
    return _tao_diem_danh(diem_danh)
