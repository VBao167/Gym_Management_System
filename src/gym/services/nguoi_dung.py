from django.db import transaction

from accounts.models import TaiKhoan
from gym.models import HoiVien, HuanLuyenVien, LeTan


MAT_KHAU_MAC_DINH = "1"


def _tao_tai_khoan(
    *,
    username,
    vai_tro,
    trang_thai=True,
):
    tai_khoan = TaiKhoan(
        username=username,
        vai_tro=vai_tro,
        is_active=trang_thai,
    )
    tai_khoan.set_password(MAT_KHAU_MAC_DINH)
    tai_khoan.full_clean()
    tai_khoan.save()

    return tai_khoan


@transaction.atomic
def tao_hoi_vien(**du_lieu):
    hoi_vien = HoiVien(**du_lieu)
    hoi_vien.gan_ma_tu_dong()

    tai_khoan = _tao_tai_khoan(
        username=hoi_vien.ma_hv,
        vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        trang_thai=hoi_vien.trang_thai,
    )

    hoi_vien.tai_khoan = tai_khoan
    hoi_vien.full_clean()
    hoi_vien.save()

    return hoi_vien


@transaction.atomic
def tao_le_tan(**du_lieu):
    le_tan = LeTan(**du_lieu)
    le_tan.gan_ma_tu_dong()

    tai_khoan = _tao_tai_khoan(
        username=le_tan.ma_lt,
        vai_tro=TaiKhoan.VaiTro.LE_TAN,
        trang_thai=le_tan.trang_thai,
    )

    le_tan.tai_khoan = tai_khoan
    le_tan.full_clean()
    le_tan.save()

    return le_tan


@transaction.atomic
def tao_huan_luyen_vien(**du_lieu):
    huan_luyen_vien = HuanLuyenVien(**du_lieu)
    huan_luyen_vien.gan_ma_tu_dong()

    tai_khoan = _tao_tai_khoan(
        username=huan_luyen_vien.ma_pt,
        vai_tro=TaiKhoan.VaiTro.PT,
        trang_thai=huan_luyen_vien.trang_thai,
    )

    huan_luyen_vien.tai_khoan = tai_khoan
    huan_luyen_vien.full_clean()
    huan_luyen_vien.save()

    return huan_luyen_vien
