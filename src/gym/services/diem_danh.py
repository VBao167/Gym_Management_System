from django.core.exceptions import ValidationError
from django.db import transaction

from gym.models import DiemDanh
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_hoi_vien,
)


@transaction.atomic
def tao_diem_danh(
    *,
    hoi_vien,
    le_tan,
    ghi_chu="",
):
    """
    Tạo một lần điểm danh cho Hội viên.

    Hội viên phải có gói tập đang hiệu lực.
    Lễ tân phải đang làm việc và có tài khoản hoạt động.
    """
    co_quyen_tap = cap_nhat_trang_thai_hoi_vien(
        hoi_vien,
    )

    if not co_quyen_tap:
        raise ValidationError(
            {
                "hoi_vien": (
                    "Hội viên không có gói tập đang hoạt động."
                )
            }
        )

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

    return DiemDanh.objects.create(
        hoi_vien=hoi_vien,
        le_tan=le_tan,
        ghi_chu=ghi_chu,
    )
