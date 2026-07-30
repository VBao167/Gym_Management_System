from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from accounts.models import TaiKhoan


@login_required
def trang_chu(request):
    dieu_huong_theo_vai_tro = {
        TaiKhoan.VaiTro.ADMIN: "gym:trang_quan_tri",
        TaiKhoan.VaiTro.LE_TAN: "gym:trang_le_tan",
        TaiKhoan.VaiTro.PT: "gym:trang_pt",
        TaiKhoan.VaiTro.HOI_VIEN: "gym:trang_hoi_vien",
    }

    ten_url = dieu_huong_theo_vai_tro.get(
        request.user.vai_tro
    )

    if ten_url is None:
        raise PermissionDenied(
            "Tài khoản không có vai trò hợp lệ."
        )

    return redirect(ten_url)