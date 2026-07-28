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


def _tao_ho_so_va_tai_khoan(
    *,
    ho_so,
    ten_truong_ma,
    vai_tro,
    trang_thai_tai_khoan=None,
):
    ho_so.gan_ma_tu_dong()

    if trang_thai_tai_khoan is None:
        trang_thai_tai_khoan = ho_so.trang_thai

    tai_khoan = _tao_tai_khoan(
        username=getattr(ho_so, ten_truong_ma),
        vai_tro=vai_tro,
        trang_thai=trang_thai_tai_khoan,
    )

    ho_so.tai_khoan = tai_khoan
    ho_so.full_clean()
    ho_so.save()

    return ho_so


@transaction.atomic
def tao_hoi_vien(**du_lieu):
    hoi_vien = HoiVien(**du_lieu)
    hoi_vien.trang_thai = False

    return _tao_ho_so_va_tai_khoan(
        ho_so=hoi_vien,
        ten_truong_ma="ma_hv",
        vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        trang_thai_tai_khoan=True,
    )


@transaction.atomic
def tao_hoi_vien_tu_doi_tuong(hoi_vien):
    hoi_vien.trang_thai = False

    return _tao_ho_so_va_tai_khoan(
        ho_so=hoi_vien,
        ten_truong_ma="ma_hv",
        vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
        trang_thai_tai_khoan=True,
    )


@transaction.atomic
def tao_le_tan(**du_lieu):
    return _tao_ho_so_va_tai_khoan(
        ho_so=LeTan(**du_lieu),
        ten_truong_ma="ma_lt",
        vai_tro=TaiKhoan.VaiTro.LE_TAN,
    )


@transaction.atomic
def tao_le_tan_tu_doi_tuong(le_tan):
    return _tao_ho_so_va_tai_khoan(
        ho_so=le_tan,
        ten_truong_ma="ma_lt",
        vai_tro=TaiKhoan.VaiTro.LE_TAN,
    )


@transaction.atomic
def tao_huan_luyen_vien(**du_lieu):
    return _tao_ho_so_va_tai_khoan(
        ho_so=HuanLuyenVien(**du_lieu),
        ten_truong_ma="ma_pt",
        vai_tro=TaiKhoan.VaiTro.PT,
    )


@transaction.atomic
def tao_huan_luyen_vien_tu_doi_tuong(huan_luyen_vien):
    return _tao_ho_so_va_tai_khoan(
        ho_so=huan_luyen_vien,
        ten_truong_ma="ma_pt",
        vai_tro=TaiKhoan.VaiTro.PT,
    )
