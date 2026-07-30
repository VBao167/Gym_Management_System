from django.http import HttpResponse

from accounts.decorators import vai_tro_required
from accounts.models import TaiKhoan


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def trang_quan_tri(request):
    return HttpResponse("Khu vực Quản trị viên.")


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def trang_le_tan(request):
    return HttpResponse("Khu vực Lễ tân.")


@vai_tro_required(TaiKhoan.VaiTro.PT)
def trang_pt(request):
    return HttpResponse("Khu vực Huấn luyện viên.")


@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def trang_hoi_vien(request):
    return HttpResponse("Khu vực Hội viên.")