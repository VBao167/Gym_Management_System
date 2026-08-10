from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError,
)
from django.db import transaction

from accounts.models import TaiKhoan


def _lay_ho_so_nhan_vien(tai_khoan):
    quan_he_theo_vai_tro = {
        TaiKhoan.VaiTro.LE_TAN: "ho_so_le_tan",
        TaiKhoan.VaiTro.PT: "ho_so_huan_luyen_vien",
    }

    ten_quan_he = quan_he_theo_vai_tro.get(
        tai_khoan.vai_tro
    )

    if ten_quan_he is None:
        return None

    try:
        return getattr(
            tai_khoan,
            ten_quan_he,
        )
    except ObjectDoesNotExist as error:
        raise ValidationError(
            "Tài khoản nhân viên chưa có hồ sơ tương ứng."
        ) from error


@transaction.atomic
def cap_nhat_trang_thai_tai_khoan(
    *,
    tai_khoan,
    hanh_dong,
):
    if hanh_dong not in {
        "khoa",
        "mo_khoa",
    }:
        raise ValidationError(
            "Hành động thay đổi tài khoản không hợp lệ."
        )

    tai_khoan = (
        TaiKhoan.objects
        .select_for_update()
        .get(pk=tai_khoan.pk)
    )

    if (
        tai_khoan.vai_tro
        == TaiKhoan.VaiTro.ADMIN
    ):
        raise ValidationError(
            "Không được thay đổi trạng thái "
            "tài khoản quản trị viên."
        )

    if (
        hanh_dong == "mo_khoa"
        and tai_khoan.vai_tro
        in {
            TaiKhoan.VaiTro.LE_TAN,
            TaiKhoan.VaiTro.PT,
        }
    ):
        ho_so_nhan_vien = _lay_ho_so_nhan_vien(
            tai_khoan
        )

        if not ho_so_nhan_vien.trang_thai:
            raise ValidationError(
                "Nhân viên phải đang làm việc "
                "trước khi mở khóa tài khoản."
            )

    trang_thai_moi = (
        hanh_dong == "mo_khoa"
    )

    if tai_khoan.is_active != trang_thai_moi:
        tai_khoan.is_active = trang_thai_moi
        tai_khoan.save(
            update_fields=["is_active"],
        )

    return tai_khoan