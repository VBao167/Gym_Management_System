from django.shortcuts import render

from accounts.decorators import vai_tro_required
from accounts.models import TaiKhoan
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_toan_bo,
)


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def trang_quan_tri(request):
    cap_nhat_trang_thai_toan_bo()

    return render(
        request,
        "users/quan_tri.html",
    )


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def trang_le_tan(request):
    cap_nhat_trang_thai_toan_bo()

    return render(
        request,
        "users/le_tan.html",
    )


@vai_tro_required(TaiKhoan.VaiTro.PT)
def trang_pt(request):
    cap_nhat_trang_thai_toan_bo()

    return render(
        request,
        "users/pt.html",
    )


@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def trang_hoi_vien(request):
    cap_nhat_trang_thai_toan_bo()

    return render(
        request,
        "users/hoi_vien.html",
    )