from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import vai_tro_required
from accounts.models import TaiKhoan
from gym.forms import TaoHoiVienForm
from gym.models import DiemDanh, GoiTap, HoiVien
from gym.services.nguoi_dung import tao_hoi_vien_tu_doi_tuong
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_toan_bo,
)


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def trang_quan_tri(request):
    cap_nhat_trang_thai_toan_bo()

    hom_nay = timezone.localdate()

    context = {
        "tong_hoi_vien": HoiVien.objects.count(),
        "hoi_vien_dang_hoat_dong": HoiVien.objects.filter(
            trang_thai=True,
        ).count(),
        "goi_tap_dang_kinh_doanh": GoiTap.objects.filter(
            trang_thai=True,
        ).count(),
        "diem_danh_hom_nay": DiemDanh.objects.filter(
            thoi_gian_diem_danh__date=hom_nay,
        ).count(),
    }

    return render(
        request,
        "users/quan_tri.html",
        context,
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def danh_sach_hoi_vien(request):
    cap_nhat_trang_thai_toan_bo()

    cac_hoi_vien = (
        HoiVien.objects
        .select_related("tai_khoan")
        .order_by("ma_hv")
    )

    return render(
        request,
        "users/quan_tri/danh_sach_hoi_vien.html",
        {
            "cac_hoi_vien": cac_hoi_vien,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def tao_hoi_vien_moi(request):
    form = TaoHoiVienForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        hoi_vien = form.save(commit=False)

        tao_hoi_vien_tu_doi_tuong(
            hoi_vien
        )

        return redirect(
            "gym:danh_sach_hoi_vien"
        )

    return render(
        request,
        "users/quan_tri/tao_hoi_vien.html",
        {
            "form": form,
        },
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