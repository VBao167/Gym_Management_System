from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from gym.models import BuoiTapPT


def _tao_buoi_tap_pt(buoi_tap):
    errors = {}

    if not buoi_tap.huan_luyen_vien_id:
        errors["huan_luyen_vien"] = (
            "Phải chọn Huấn luyện viên."
        )
    else:
        huan_luyen_vien = buoi_tap.huan_luyen_vien

        if not huan_luyen_vien.trang_thai:
            errors["huan_luyen_vien"] = (
                "Huấn luyện viên đã ngừng làm việc."
            )
        elif not huan_luyen_vien.tai_khoan.is_active:
            errors["huan_luyen_vien"] = (
                "Tài khoản Huấn luyện viên đang bị khóa."
            )

    if not buoi_tap.le_tan_id:
        errors["le_tan"] = "Phải chọn Lễ tân."
    else:
        le_tan = buoi_tap.le_tan

        if not le_tan.trang_thai:
            errors["le_tan"] = (
                "Lễ tân đã ngừng làm việc, "
                "không thể xếp buổi PT."
            )
        elif not le_tan.tai_khoan.is_active:
            errors["le_tan"] = (
                "Tài khoản Lễ tân đang bị khóa."
            )

    if (
        buoi_tap.trang_thai
        != BuoiTapPT.TrangThai.DA_LEN_LICH
    ):
        errors["trang_thai"] = (
            "Buổi PT mới phải có trạng thái Đã lên lịch."
        )

    if errors:
        raise ValidationError(errors)

    buoi_tap.save()
    return buoi_tap


@transaction.atomic
def tao_buoi_tap_pt(
    *,
    dang_ky,
    huan_luyen_vien,
    le_tan,
    ngay_tap,
    gio_bat_dau,
    gio_ket_thuc,
    ghi_chu="",
):
    buoi_tap = BuoiTapPT(
        dang_ky=dang_ky,
        huan_luyen_vien=huan_luyen_vien,
        le_tan=le_tan,
        ngay_tap=ngay_tap,
        gio_bat_dau=gio_bat_dau,
        gio_ket_thuc=gio_ket_thuc,
        trang_thai=BuoiTapPT.TrangThai.DA_LEN_LICH,
        ghi_chu=ghi_chu,
    )

    return _tao_buoi_tap_pt(buoi_tap)


@transaction.atomic
def tao_buoi_tap_pt_tu_doi_tuong(buoi_tap):
    return _tao_buoi_tap_pt(buoi_tap)

@transaction.atomic
def cap_nhat_ket_qua_buoi_tap_pt(
    *,
    buoi_tap,
    huan_luyen_vien,
    trang_thai,
    ghi_chu="",
):
    buoi_tap = (
        BuoiTapPT.objects
        .select_for_update()
        .select_related(
            "huan_luyen_vien",
            "huan_luyen_vien__tai_khoan",
        )
        .get(pk=buoi_tap.pk)
    )

    errors = {}

    if (
        buoi_tap.huan_luyen_vien_id
        != huan_luyen_vien.pk
    ):
        errors["huan_luyen_vien"] = (
            "Huấn luyện viên không được phân công "
            "cho buổi tập này."
        )

    if not huan_luyen_vien.trang_thai:
        errors["huan_luyen_vien"] = (
            "Huấn luyện viên đã ngừng làm việc."
        )
    elif not huan_luyen_vien.tai_khoan.is_active:
        errors["huan_luyen_vien"] = (
            "Tài khoản Huấn luyện viên đang bị khóa."
        )

    if (
        buoi_tap.trang_thai
        != BuoiTapPT.TrangThai.DA_LEN_LICH
    ):
        errors["trang_thai"] = (
            "Chỉ buổi đang ở trạng thái Đã lên lịch "
            "mới được cập nhật kết quả."
        )

    cac_trang_thai_hop_le = {
        BuoiTapPT.TrangThai.HOAN_THANH,
        BuoiTapPT.TrangThai.VANG,
        BuoiTapPT.TrangThai.HUY,
    }

    if trang_thai not in cac_trang_thai_hop_le:
        errors["trang_thai"] = (
            "Kết quả buổi tập không hợp lệ."
        )

    if trang_thai in {
        BuoiTapPT.TrangThai.HOAN_THANH,
        BuoiTapPT.TrangThai.VANG,
    }:
        thoi_diem_hien_tai = timezone.now()

        if timezone.is_aware(thoi_diem_hien_tai):
            thoi_diem_hien_tai = timezone.localtime(
                thoi_diem_hien_tai
            )

        ngay_hien_tai = thoi_diem_hien_tai.date()
        gio_hien_tai = (
            thoi_diem_hien_tai
            .time()
            .replace(tzinfo=None)
        )

        buoi_tap_da_ket_thuc = (
            buoi_tap.ngay_tap < ngay_hien_tai
            or (
                buoi_tap.ngay_tap == ngay_hien_tai
                and buoi_tap.gio_ket_thuc
                <= gio_hien_tai
            )
        )

        if not buoi_tap_da_ket_thuc:
            errors["trang_thai"] = (
                "Chỉ được ghi nhận Hoàn thành "
                "hoặc Vắng sau khi buổi tập kết thúc."
            )

    if errors:
        raise ValidationError(errors)

    buoi_tap.trang_thai = trang_thai
    buoi_tap.ghi_chu = (ghi_chu or "").strip()

    buoi_tap.full_clean()
    buoi_tap.save(
        update_fields=[
            "trang_thai",
            "ghi_chu",
        ]
    )

    return buoi_tap
