from django.db import transaction

from gym.models import DangKyGoiTap, HoaDon


def _tao_dang_ky_va_hoa_don(
    *,
    dang_ky,
    le_tan,
    phuong_thuc_thanh_toan,
    ghi_chu_hoa_don="",
):
    dang_ky.save()

    hoa_don = HoaDon.objects.create(
        dang_ky=dang_ky,
        le_tan=le_tan,
        phuong_thuc_thanh_toan=phuong_thuc_thanh_toan,
        ghi_chu=ghi_chu_hoa_don,
    )

    return dang_ky, hoa_don


@transaction.atomic
def tao_dang_ky_va_hoa_don(
    *,
    hoi_vien,
    goi_tap,
    le_tan,
    ngay_bat_dau,
    phuong_thuc_thanh_toan,
    ngay_dang_ky=None,
    ghi_chu_dang_ky="",
    ghi_chu_hoa_don="",
):
    du_lieu_dang_ky = {
        "hoi_vien": hoi_vien,
        "goi_tap": goi_tap,
        "ngay_bat_dau": ngay_bat_dau,
        "ghi_chu": ghi_chu_dang_ky,
    }

    if ngay_dang_ky is not None:
        du_lieu_dang_ky["ngay_dang_ky"] = ngay_dang_ky

    dang_ky = DangKyGoiTap(**du_lieu_dang_ky)

    return _tao_dang_ky_va_hoa_don(
        dang_ky=dang_ky,
        le_tan=le_tan,
        phuong_thuc_thanh_toan=phuong_thuc_thanh_toan,
        ghi_chu_hoa_don=ghi_chu_hoa_don,
    )


@transaction.atomic
def tao_dang_ky_va_hoa_don_tu_doi_tuong(
    *,
    dang_ky,
    le_tan,
    phuong_thuc_thanh_toan,
    ghi_chu_hoa_don="",
):
    return _tao_dang_ky_va_hoa_don(
        dang_ky=dang_ky,
        le_tan=le_tan,
        phuong_thuc_thanh_toan=phuong_thuc_thanh_toan,
        ghi_chu_hoa_don=ghi_chu_hoa_don,
    )
