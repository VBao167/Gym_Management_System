from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from gym.models import BuoiTapPT, DangKyGoiTap


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


def _chon_dang_ky_pt_uu_tien(
    *,
    hoi_vien,
    ngay_tap,
):
    if not hoi_vien or not hoi_vien.pk:
        raise ValidationError(
            {
                "hoi_vien": (
                    "Phải chọn Hội viên cần xếp buổi PT."
                )
            }
        )

    co_quyen_vao_phong_tap = (
        DangKyGoiTap.objects
        .filter(
            hoi_vien=hoi_vien,
            ngay_bat_dau__lte=ngay_tap,
            ngay_ket_thuc__gte=ngay_tap,
        )
        .exists()
    )

    if not co_quyen_vao_phong_tap:
        raise ValidationError(
            {
                "ngay_tap": (
                    "Tại ngày tập, Hội viên không có "
                    "gói tập còn hiệu lực để vào phòng gym."
                )
            }
        )

    cac_dang_ky_pt = (
        DangKyGoiTap.objects
        .select_for_update()
        .filter(
            hoi_vien=hoi_vien,
            so_buoi_pt_dang_ky__gt=0,
            ngay_dang_ky__lte=ngay_tap,
            ngay_ket_thuc__gte=ngay_tap,
        )
        .select_related(
            "hoi_vien",
            "goi_tap",
        )
        .order_by(
            "ngay_dang_ky",
            "ma_dk",
        )
    )

    for dang_ky in cac_dang_ky_pt:
        if dang_ky.so_buoi_pt_co_the_xep_lich > 0:
            return dang_ky

    raise ValidationError(
        {
            "hoi_vien": (
                "Hội viên không còn đăng ký PT "
                "có thể sử dụng tại ngày tập đã chọn."
            )
        }
    )


@transaction.atomic
def tao_buoi_tap_pt_cho_hoi_vien(
    *,
    hoi_vien,
    huan_luyen_vien,
    le_tan,
    ngay_tap,
    gio_bat_dau,
    gio_ket_thuc,
    ghi_chu="",
):
    dang_ky = _chon_dang_ky_pt_uu_tien(
        hoi_vien=hoi_vien,
        ngay_tap=ngay_tap,
    )

    return tao_buoi_tap_pt(
        dang_ky=dang_ky,
        huan_luyen_vien=huan_luyen_vien,
        le_tan=le_tan,
        ngay_tap=ngay_tap,
        gio_bat_dau=gio_bat_dau,
        gio_ket_thuc=gio_ket_thuc,
        ghi_chu=ghi_chu,
    )


@transaction.atomic
def tao_buoi_tap_pt_tu_doi_tuong(buoi_tap):
    return _tao_buoi_tap_pt(buoi_tap)

def _lay_ngay_va_gio_hien_tai():
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

    return ngay_hien_tai, gio_hien_tai


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

    cac_ket_qua_hop_le = {
        BuoiTapPT.TrangThai.HOAN_THANH,
        BuoiTapPT.TrangThai.VANG,
    }

    if trang_thai not in cac_ket_qua_hop_le:
        errors["trang_thai"] = (
            "PT chỉ được ghi nhận kết quả "
            "Hoàn thành hoặc Vắng."
        )
    else:
        ngay_hien_tai, gio_hien_tai = (
            _lay_ngay_va_gio_hien_tai()
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


@transaction.atomic
def huy_buoi_tap_pt(
    *,
    buoi_tap,
    le_tan,
    ly_do_huy,
):
    buoi_tap = (
        BuoiTapPT.objects
        .select_for_update()
        .get(pk=buoi_tap.pk)
    )

    errors = {}

    if not le_tan.trang_thai:
        errors["le_tan"] = (
            "Lễ tân đã ngừng làm việc, "
            "không thể hủy buổi tập PT."
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
            "Chỉ buổi đang ở trạng thái Đã lên lịch "
            "mới được hủy."
        )

    ly_do_huy = (ly_do_huy or "").strip()

    if not ly_do_huy:
        errors["ly_do_huy"] = (
            "Phải nhập lý do hủy buổi tập."
        )

    ngay_hien_tai, gio_hien_tai = (
        _lay_ngay_va_gio_hien_tai()
    )

    buoi_tap_chua_bat_dau = (
        buoi_tap.ngay_tap > ngay_hien_tai
        or (
            buoi_tap.ngay_tap == ngay_hien_tai
            and buoi_tap.gio_bat_dau
            > gio_hien_tai
        )
    )

    if not buoi_tap_chua_bat_dau:
        errors["ly_do_huy"] = (
            "Chỉ được hủy buổi tập trước giờ bắt đầu."
        )

    if errors:
        raise ValidationError(errors)

    buoi_tap.trang_thai = BuoiTapPT.TrangThai.HUY
    buoi_tap.ghi_chu = (
        f"Hủy bởi {le_tan.ma_lt}: {ly_do_huy}"
    )

    buoi_tap.full_clean()
    buoi_tap.save(
        update_fields=[
            "trang_thai",
            "ghi_chu",
        ]
    )

    return buoi_tap
