from datetime import date

from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError

from accounts.decorators import vai_tro_required
from accounts.models import TaiKhoan
from gym.forms import (
    BuoiTapPTForm,
    HuyBuoiTapPTForm,
    CapNhatKetQuaBuoiTapPTForm,
    DangKyGoiVaHoaDonForm,
    DiemDanhForm,
    GiaHanGoiForm,
    GoiTapForm,
    HuanLuyenVienForm,
    LeTanForm,
    TaoHoiVienForm,
)
from gym.models import (
    BuoiTapPT,
    DiemDanh,
    GoiTap,
    HoiVien,
    HuanLuyenVien,
    LeTan,
    DangKyGoiTap,
    HoaDon,
)
from gym.services.nguoi_dung import (
    tao_hoi_vien_tu_doi_tuong,
    tao_huan_luyen_vien_tu_doi_tuong,
    tao_le_tan_tu_doi_tuong,
)
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_toan_bo,
)
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)
from gym.services.gia_han_goi import gia_han_goi
from gym.services.diem_danh import tao_diem_danh
from gym.services.buoi_tap_pt import (
    cap_nhat_ket_qua_buoi_tap_pt,
    huy_buoi_tap_pt,
    tao_buoi_tap_pt,
    tao_buoi_tap_pt_cho_hoi_vien,
)

CAU_HINH_NHAN_VIEN = {
    "le-tan": {
        "model": LeTan,
        "form_class": LeTanForm,
        "ham_tao": tao_le_tan_tu_doi_tuong,
        "truong_ma": "ma_lt",
        "ten_loai": "Lễ tân",
        "ten_loai_viet_thuong": "lễ tân",
    },
    "pt": {
        "model": HuanLuyenVien,
        "form_class": HuanLuyenVienForm,
        "ham_tao": tao_huan_luyen_vien_tu_doi_tuong,
        "truong_ma": "ma_pt",
        "ten_loai": "Huấn luyện viên",
        "ten_loai_viet_thuong": "huấn luyện viên",
    },
}


def _lay_cau_hinh_nhan_vien(loai_nhan_vien):
    cau_hinh = CAU_HINH_NHAN_VIEN.get(
        loai_nhan_vien
    )

    if cau_hinh is None:
        raise Http404(
            "Loại nhân viên không tồn tại."
        )

    return cau_hinh


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
        "gym/trang_chu/quan_tri.html",
        context,
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def danh_sach_hoi_vien(request):
    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

    cap_nhat_trang_thai_toan_bo()

    cac_hoi_vien = (
        HoiVien.objects
        .select_related("tai_khoan")
        .order_by("ma_hv")
    )

    return render(
        request,
        "gym/hoi_vien/danh_sach_hoi_vien.html",
        {
            "cac_hoi_vien": cac_hoi_vien,
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def tao_hoi_vien_moi(request):
    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

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
        "gym/hoi_vien/tao_hoi_vien.html",
        {
            "form": form,
            "tieu_de_trang": "Thêm hội viên",
            "tieu_de_bieu_mau": "Thông tin hội viên mới",
            "mo_ta_bieu_mau": (
                "Tài khoản đăng nhập sẽ được hệ thống "
                "tạo tự động sau khi lưu hội viên."
            ),
            "nhan_nut_luu": "Lưu hội viên",
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def chinh_sua_hoi_vien(request, ma_hv):
    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

    hoi_vien = get_object_or_404(
        HoiVien,
        pk=ma_hv,
    )

    form = TaoHoiVienForm(
        request.POST or None,
        instance=hoi_vien,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect(
            "gym:chi_tiet_hoi_vien",
            ma_hv=hoi_vien.ma_hv,
        )

    return render(
        request,
        "gym/hoi_vien/tao_hoi_vien.html",
        {
            "form": form,
            "tieu_de_trang": "Chỉnh sửa hội viên",
            "tieu_de_bieu_mau": "Cập nhật thông tin hội viên",
            "mo_ta_bieu_mau": (
                f"Chỉnh sửa thông tin cá nhân của "
                f"hội viên {hoi_vien.ma_hv}."
            ),
            "nhan_nut_luu": "Lưu thay đổi",
            "hoi_vien": hoi_vien,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
@require_POST
def doi_trang_thai_tai_khoan_hoi_vien(request, ma_hv):
    hoi_vien = get_object_or_404(
        HoiVien.objects.select_related("tai_khoan"),
        pk=ma_hv,
    )

    hanh_dong = request.POST.get("hanh_dong")

    if hanh_dong == "khoa":
        trang_thai_moi = False
    elif hanh_dong == "mo_khoa":
        trang_thai_moi = True
    else:
        return HttpResponseBadRequest(
            "Hành động thay đổi trạng thái không hợp lệ."
        )

    tai_khoan = hoi_vien.tai_khoan

    if tai_khoan.is_active != trang_thai_moi:
        tai_khoan.is_active = trang_thai_moi
        tai_khoan.save(
            update_fields=["is_active"],
        )

    return redirect(
        "gym:chi_tiet_hoi_vien",
        ma_hv=hoi_vien.ma_hv,
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def chi_tiet_hoi_vien(request, ma_hv):
    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

    cap_nhat_trang_thai_toan_bo()

    hoi_vien = get_object_or_404(
        HoiVien.objects.select_related("tai_khoan"),
        pk=ma_hv,
    )

    return render(
        request,
        "gym/hoi_vien/chi_tiet_hoi_vien.html",
        {
            "hoi_vien": hoi_vien,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def danh_sach_goi_tap(request):
    cac_goi_tap = GoiTap.objects.order_by("ma_goi")

    return render(
        request,
        "gym/goi_tap/danh_sach_goi_tap.html",
        {
            "cac_goi_tap": cac_goi_tap,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def tao_goi_tap_moi(request):
    form = GoiTapForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect(
            "gym:danh_sach_goi_tap"
        )

    return render(
        request,
        "gym/goi_tap/bieu_mau_goi_tap.html",
        {
            "form": form,
            "tieu_de_trang": "Thêm gói tập",
            "tieu_de_bieu_mau": "Thông tin gói tập mới",
            "mo_ta_bieu_mau": (
                "Khai báo thời hạn, mức giá và quyền sử dụng "
                "PT của gói tập."
            ),
            "nhan_nut_luu": "Lưu gói tập",
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def chinh_sua_goi_tap(request, ma_goi):
    goi_tap = get_object_or_404(
        GoiTap,
        pk=ma_goi,
    )

    form = GoiTapForm(
        request.POST or None,
        instance=goi_tap,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect(
            "gym:danh_sach_goi_tap"
        )

    return render(
        request,
        "gym/goi_tap/bieu_mau_goi_tap.html",
        {
            "form": form,
            "goi_tap": goi_tap,
            "tieu_de_trang": "Chỉnh sửa gói tập",
            "tieu_de_bieu_mau": "Cập nhật thông tin gói tập",
            "mo_ta_bieu_mau": (
                f"Chỉnh sửa thông tin của gói {goi_tap.ma_goi}."
            ),
            "nhan_nut_luu": "Lưu thay đổi",
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
@require_POST
def doi_trang_thai_goi_tap(request, ma_goi):
    goi_tap = get_object_or_404(
        GoiTap,
        pk=ma_goi,
    )

    hanh_dong = request.POST.get("hanh_dong")

    if hanh_dong == "ngung_kinh_doanh":
        trang_thai_moi = False
    elif hanh_dong == "mo_kinh_doanh":
        trang_thai_moi = True
    else:
        return HttpResponseBadRequest(
            "Hành động thay đổi trạng thái không hợp lệ."
        )

    if goi_tap.trang_thai != trang_thai_moi:
        goi_tap.trang_thai = trang_thai_moi
        goi_tap.save(
            update_fields=["trang_thai"],
        )

    return redirect(
        "gym:danh_sach_goi_tap"
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def danh_sach_nhan_vien(request):
    cac_le_tan = (
        LeTan.objects
        .select_related("tai_khoan")
        .order_by("ma_lt")
    )

    cac_huan_luyen_vien = (
        HuanLuyenVien.objects
        .select_related("tai_khoan")
        .order_by("ma_pt")
    )

    return render(
        request,
        "gym/nhan_vien/danh_sach_nhan_vien.html",
        {
            "cac_le_tan": cac_le_tan,
            "cac_huan_luyen_vien": (
                cac_huan_luyen_vien
            ),
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def tao_nhan_vien_moi(request, loai_nhan_vien):
    cau_hinh = _lay_cau_hinh_nhan_vien(
        loai_nhan_vien
    )

    form = cau_hinh["form_class"](
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        nhan_vien = form.save(commit=False)

        cau_hinh["ham_tao"](nhan_vien)

        ma_nhan_vien = getattr(
            nhan_vien,
            cau_hinh["truong_ma"],
        )

        return redirect(
            "gym:chi_tiet_nhan_vien",
            loai_nhan_vien=loai_nhan_vien,
            ma_nhan_vien=ma_nhan_vien,
        )

    return render(
        request,
        "gym/nhan_vien/bieu_mau_nhan_vien.html",
        {
            "form": form,
            "loai_nhan_vien": loai_nhan_vien,
            "tieu_de_trang": (
                f"Thêm {cau_hinh['ten_loai']}"
            ),
            "tieu_de_bieu_mau": (
                f"Thông tin {cau_hinh['ten_loai_viet_thuong']} "
                "mới"
            ),
            "mo_ta_bieu_mau": (
                "Mã nhân viên, tài khoản đăng nhập và "
                "mật khẩu mặc định sẽ được tạo tự động."
            ),
            "nhan_nut_luu": "Lưu nhân viên",
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def chi_tiet_nhan_vien(
    request,
    loai_nhan_vien,
    ma_nhan_vien,
):
    cau_hinh = _lay_cau_hinh_nhan_vien(
        loai_nhan_vien
    )

    nhan_vien = get_object_or_404(
        cau_hinh["model"].objects.select_related(
            "tai_khoan"
        ),
        pk=ma_nhan_vien,
    )

    return render(
        request,
        "gym/nhan_vien/chi_tiet_nhan_vien.html",
        {
            "nhan_vien": nhan_vien,
            "ma_nhan_vien": ma_nhan_vien,
            "loai_nhan_vien": loai_nhan_vien,
            "ten_loai": cau_hinh["ten_loai"],
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def chinh_sua_nhan_vien(
    request,
    loai_nhan_vien,
    ma_nhan_vien,
):
    cau_hinh = _lay_cau_hinh_nhan_vien(
        loai_nhan_vien
    )

    nhan_vien = get_object_or_404(
        cau_hinh["model"],
        pk=ma_nhan_vien,
    )

    form = cau_hinh["form_class"](
        request.POST or None,
        instance=nhan_vien,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect(
            "gym:chi_tiet_nhan_vien",
            loai_nhan_vien=loai_nhan_vien,
            ma_nhan_vien=ma_nhan_vien,
        )

    return render(
        request,
        "gym/nhan_vien/bieu_mau_nhan_vien.html",
        {
            "form": form,
            "nhan_vien": nhan_vien,
            "loai_nhan_vien": loai_nhan_vien,
            "tieu_de_trang": (
                f"Chỉnh sửa {cau_hinh['ten_loai']}"
            ),
            "tieu_de_bieu_mau": (
                "Cập nhật thông tin nhân viên"
            ),
            "mo_ta_bieu_mau": (
                f"Chỉnh sửa thông tin của "
                f"{cau_hinh['ten_loai_viet_thuong']} "
                f"{ma_nhan_vien}."
            ),
            "nhan_nut_luu": "Lưu thay đổi",
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
@require_POST
def doi_trang_thai_lam_viec_nhan_vien(
    request,
    loai_nhan_vien,
    ma_nhan_vien,
):
    cau_hinh = _lay_cau_hinh_nhan_vien(
        loai_nhan_vien
    )

    hanh_dong = request.POST.get("hanh_dong")

    if hanh_dong not in {
        "ngung_lam_viec",
        "cho_lam_viec_lai",
    }:
        return HttpResponseBadRequest(
            "Hành động thay đổi trạng thái không hợp lệ."
        )

    with transaction.atomic():
        nhan_vien = get_object_or_404(
            cau_hinh["model"].objects
            .select_related("tai_khoan")
            .select_for_update(),
            pk=ma_nhan_vien,
        )

        if hanh_dong == "ngung_lam_viec":
            nhan_vien.trang_thai = False
            nhan_vien.save(
                update_fields=["trang_thai"],
            )

            if nhan_vien.tai_khoan.is_active:
                nhan_vien.tai_khoan.is_active = False
                nhan_vien.tai_khoan.save(
                    update_fields=["is_active"],
                )
        else:
            nhan_vien.trang_thai = True
            nhan_vien.save(
                update_fields=["trang_thai"],
            )

    return redirect(
        "gym:chi_tiet_nhan_vien",
        loai_nhan_vien=loai_nhan_vien,
        ma_nhan_vien=ma_nhan_vien,
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
@require_POST
def doi_trang_thai_tai_khoan_nhan_vien(
    request,
    loai_nhan_vien,
    ma_nhan_vien,
):
    cau_hinh = _lay_cau_hinh_nhan_vien(
        loai_nhan_vien
    )

    hanh_dong = request.POST.get("hanh_dong")

    if hanh_dong not in {"khoa", "mo_khoa"}:
        return HttpResponseBadRequest(
            "Hành động thay đổi tài khoản không hợp lệ."
        )

    with transaction.atomic():
        nhan_vien = get_object_or_404(
            cau_hinh["model"].objects
            .select_related("tai_khoan")
            .select_for_update(),
            pk=ma_nhan_vien,
        )

        if (
            hanh_dong == "mo_khoa"
            and not nhan_vien.trang_thai
        ):
            return HttpResponseBadRequest(
                "Nhân viên phải đang làm việc "
                "trước khi mở khóa tài khoản."
            )

        trang_thai_moi = hanh_dong == "mo_khoa"
        tai_khoan = nhan_vien.tai_khoan

        if tai_khoan.is_active != trang_thai_moi:
            tai_khoan.is_active = trang_thai_moi
            tai_khoan.save(
                update_fields=["is_active"],
            )

    return redirect(
        "gym:chi_tiet_nhan_vien",
        loai_nhan_vien=loai_nhan_vien,
        ma_nhan_vien=ma_nhan_vien,
    )


def _lay_le_tan_dang_nhap(request):
    try:
        le_tan = request.user.ho_so_le_tan
    except LeTan.DoesNotExist as error:
        raise PermissionDenied(
            "Tài khoản không có hồ sơ Lễ tân."
        ) from error

    if not le_tan.trang_thai:
        raise PermissionDenied(
            "Lễ tân đã ngừng làm việc."
        )

    return le_tan


def _lay_huan_luyen_vien_dang_nhap(request):
    try:
        huan_luyen_vien = (
            HuanLuyenVien.objects
            .select_related("tai_khoan")
            .get(tai_khoan=request.user)
        )
    except HuanLuyenVien.DoesNotExist as error:
        raise PermissionDenied(
            "Tài khoản chưa có hồ sơ Huấn luyện viên."
        ) from error

    if not huan_luyen_vien.trang_thai:
        raise PermissionDenied(
            "Huấn luyện viên đã ngừng làm việc."
        )

    if not huan_luyen_vien.tai_khoan.is_active:
        raise PermissionDenied(
            "Tài khoản Huấn luyện viên đang bị khóa."
        )

    return huan_luyen_vien


def _lay_hoi_vien_dang_nhap(request):
    try:
        hoi_vien = (
            HoiVien.objects
            .select_related("tai_khoan")
            .get(tai_khoan=request.user)
        )
    except HoiVien.DoesNotExist as error:
        raise PermissionDenied(
            "Tài khoản chưa có hồ sơ Hội viên."
        ) from error

    return hoi_vien


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def danh_sach_dang_ky_hoa_don(request):
    cap_nhat_trang_thai_toan_bo()

    trang_thai_duoc_chon = request.GET.get(
        "trang_thai",
        "",
    ).strip()

    cac_trang_thai_hop_le = {
        DangKyGoiTap.TrangThai.HOAT_DONG,
        DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        DangKyGoiTap.TrangThai.HET_HAN,
    }

    if (
        trang_thai_duoc_chon
        not in cac_trang_thai_hop_le
    ):
        trang_thai_duoc_chon = ""

    cac_dang_ky = (
        DangKyGoiTap.objects
        .select_related(
            "hoi_vien",
            "goi_tap",
            "hoa_don",
            "hoa_don__le_tan",
        )
    )

    if trang_thai_duoc_chon:
        cac_dang_ky = cac_dang_ky.filter(
            trang_thai=trang_thai_duoc_chon,
        )

    cac_dang_ky = cac_dang_ky.order_by(
        "ma_dk",
    )

    cac_bo_loc_trang_thai = [
        (
            "",
            "Tất cả",
        ),
        (
            DangKyGoiTap.TrangThai.HOAT_DONG,
            "Hoạt động",
        ),
        (
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
            "Chưa kích hoạt",
        ),
        (
            DangKyGoiTap.TrangThai.HET_HAN,
            "Hết hạn",
        ),
    ]

    return render(
        request,
        (
            "gym/dang_ky_hoa_don/"
            "danh_sach_dang_ky_hoa_don.html"
        ),
        {
            "cac_dang_ky": cac_dang_ky,
            "trang_thai_duoc_chon": (
                trang_thai_duoc_chon
            ),
            "cac_bo_loc_trang_thai": (
                cac_bo_loc_trang_thai
            ),
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def tao_dang_ky_hoa_don(request):
    le_tan = _lay_le_tan_dang_nhap(request)

    form = DangKyGoiVaHoaDonForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        try:
            dang_ky, _ = tao_dang_ky_va_hoa_don(
                hoi_vien=form.cleaned_data["hoi_vien"],
                goi_tap=form.cleaned_data["goi_tap"],
                le_tan=le_tan,
                ngay_bat_dau=(
                    form.cleaned_data["ngay_bat_dau"]
                ),
                phuong_thuc_thanh_toan=(
                    form.cleaned_data[
                        "phuong_thuc_thanh_toan"
                    ]
                ),
                ghi_chu_dang_ky=(
                    form.cleaned_data[
                        "ghi_chu_dang_ky"
                    ]
                ),
                ghi_chu_hoa_don=(
                    form.cleaned_data[
                        "ghi_chu_hoa_don"
                    ]
                ),
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect(
                "gym:chi_tiet_dang_ky_hoa_don",
                ma_dk=dang_ky.ma_dk,
            )

    return render(
        request,
        "gym/dang_ky_hoa_don/"
        "tao_dang_ky_hoa_don.html",
        {
            "form": form,
            "le_tan": le_tan,
            "tieu_de_trang": "Tạo đăng ký gói",
            "tieu_de_bieu_mau": (
                "Thông tin đăng ký và thanh toán"
            ),
            "mo_ta_bieu_mau": (
                "Tạo đăng ký gói mới và hóa đơn "
                "tương ứng cho hội viên."
            ),
            "nhan_nut_luu": (
                "Lưu đăng ký và lập hóa đơn"
            ),
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def gia_han_goi_hoi_vien(request, ma_dk):
    le_tan = _lay_le_tan_dang_nhap(request)

    dang_ky_goc = get_object_or_404(
        DangKyGoiTap.objects.select_related(
            "hoi_vien",
            "goi_tap",
        ),
        pk=ma_dk,
    )

    form = GiaHanGoiForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():
        try:
            dang_ky_moi, _ = gia_han_goi(
                hoi_vien=dang_ky_goc.hoi_vien,
                goi_tap=form.cleaned_data["goi_tap"],
                le_tan=le_tan,
                phuong_thuc_thanh_toan=(
                    form.cleaned_data[
                        "phuong_thuc_thanh_toan"
                    ]
                ),
                ghi_chu_dang_ky=(
                    form.cleaned_data[
                        "ghi_chu_dang_ky"
                    ]
                ),
                ghi_chu_hoa_don=(
                    form.cleaned_data[
                        "ghi_chu_hoa_don"
                    ]
                ),
            )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect(
                "gym:chi_tiet_dang_ky_hoa_don",
                ma_dk=dang_ky_moi.ma_dk,
            )

    return render(
        request,
        "gym/dang_ky_hoa_don/"
        "tao_dang_ky_hoa_don.html",
        {
            "form": form,
            "le_tan": le_tan,
            "dang_ky_goc": dang_ky_goc,
            "tieu_de_trang": "Gia hạn gói tập",
            "tieu_de_bieu_mau": (
                "Thông tin gia hạn và thanh toán"
            ),
            "mo_ta_bieu_mau": (
                f"Gia hạn cho hội viên "
                f"{dang_ky_goc.hoi_vien.ma_hv} — "
                f"{dang_ky_goc.hoi_vien.ho_ten}. "
                "Ngày bắt đầu gói mới sẽ được "
                "hệ thống tự động tính nối tiếp."
            ),
            "nhan_nut_luu": (
                "Gia hạn và lập hóa đơn"
            ),
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def chi_tiet_dang_ky_hoa_don(request, ma_dk):
    cap_nhat_trang_thai_toan_bo()

    dang_ky = get_object_or_404(
        DangKyGoiTap.objects.select_related(
            "hoi_vien",
            "goi_tap",
            "hoa_don",
            "hoa_don__le_tan",
        ),
        pk=ma_dk,
    )

    try:
        hoa_don = dang_ky.hoa_don
    except HoaDon.DoesNotExist:
        hoa_don = None

    return render(
        request,
        "gym/dang_ky_hoa_don/"
        "chi_tiet_dang_ky_hoa_don.html",
        {
            "dang_ky": dang_ky,
            "hoa_don": hoa_don,
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def danh_sach_diem_danh(request):
    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

    cap_nhat_trang_thai_toan_bo()

    cac_diem_danh = (
        DiemDanh.objects
        .select_related(
            "hoi_vien",
            "le_tan",
        )
        .order_by(
            "-thoi_gian_diem_danh",
            "ma_dd",
        )
    )

    return render(
        request,
        "gym/diem_danh/danh_sach_diem_danh.html",
        {
            "cac_diem_danh": cac_diem_danh,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def tao_diem_danh_moi(request):
    le_tan = _lay_le_tan_dang_nhap(request)

    cap_nhat_trang_thai_toan_bo()

    if request.method == "POST":
        tu_khoa = request.POST.get(
            "tu_khoa",
            "",
        ).strip()
    else:
        tu_khoa = request.GET.get(
            "tu_khoa",
            "",
        ).strip()

    form = DiemDanhForm(
        request.POST or None,
        tu_khoa=tu_khoa,
    )

    cac_hoi_vien_hop_le = (
        form.fields["hoi_vien"].queryset
    )

    if request.method == "POST" and form.is_valid():
        try:
            tao_diem_danh(
                hoi_vien=(
                    form.cleaned_data["hoi_vien"]
                ),
                le_tan=le_tan,
                ghi_chu=(
                    form.cleaned_data["ghi_chu"]
                ),
            )
        except ValidationError as error:
            if hasattr(error, "error_dict"):
                for ten_truong, cac_loi in (
                    error.error_dict.items()
                ):
                    truong_form = (
                        ten_truong
                        if ten_truong in form.fields
                        else None
                    )

                    for loi in cac_loi:
                        form.add_error(
                            truong_form,
                            loi,
                        )
            else:
                form.add_error(None, error)
        else:
            return redirect(
                "gym:danh_sach_diem_danh"
            )

    return render(
        request,
        "gym/diem_danh/tao_diem_danh.html",
        {
            "form": form,
            "le_tan": le_tan,
            "tu_khoa": tu_khoa,
            "cac_hoi_vien_hop_le": (
                cac_hoi_vien_hop_le
            ),
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
    TaiKhoan.VaiTro.PT,
)
def danh_sach_buoi_tap_pt(request):
    cap_nhat_trang_thai_toan_bo()

    cac_buoi_tap = (
        BuoiTapPT.objects
        .select_related(
            "dang_ky",
            "dang_ky__hoi_vien",
            "dang_ky__goi_tap",
            "huan_luyen_vien",
            "le_tan",
        )
        .order_by(
            "-ngay_tap",
            "-gio_bat_dau",
            "ma_buoi",
        )
    )

    la_lich_ca_nhan = False

    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        _lay_le_tan_dang_nhap(request)

    elif request.user.vai_tro == TaiKhoan.VaiTro.PT:
        huan_luyen_vien = (
            _lay_huan_luyen_vien_dang_nhap(request)
        )

        cac_buoi_tap = cac_buoi_tap.filter(
            huan_luyen_vien=huan_luyen_vien,
        )
        la_lich_ca_nhan = True

    return render(
        request,
        "gym/buoi_tap_pt/"
        "danh_sach_buoi_tap_pt.html",
        {
            "cac_buoi_tap": cac_buoi_tap,
            "la_lich_ca_nhan": la_lich_ca_nhan,
        },
    )


def _lay_hoi_vien_co_the_xep_buoi_pt(tu_khoa=""):
    cac_dang_ky_pt = (
        DangKyGoiTap.objects
        .filter(
            so_buoi_pt_dang_ky__gt=0,
        )
        .select_related(
            "hoi_vien",
        )
        .prefetch_related(
            "cac_buoi_tap_pt",
        )
        .order_by(
            "hoi_vien__ma_hv",
            "ngay_dang_ky",
            "ma_dk",
        )
    )

    if tu_khoa:
        cac_dang_ky_pt = cac_dang_ky_pt.filter(
            Q(
                hoi_vien__ma_hv__icontains=tu_khoa
            )
            | Q(
                hoi_vien__ho_ten__icontains=tu_khoa
            )
            | Q(
                hoi_vien__sdt__icontains=tu_khoa
            )
            | Q(
                hoi_vien__email__icontains=tu_khoa
            )
        )

    gioi_han = 20 if tu_khoa else 10

    ket_qua = []
    theo_ma_hoi_vien = {}

    for dang_ky in cac_dang_ky_pt:
        so_buoi_co_the_xep = (
            dang_ky.so_buoi_pt_co_the_xep_lich
        )

        if so_buoi_co_the_xep <= 0:
            continue

        ma_hoi_vien = dang_ky.hoi_vien_id

        if ma_hoi_vien not in theo_ma_hoi_vien:
            if len(ket_qua) >= gioi_han:
                break

            thong_tin = {
                "hoi_vien": dang_ky.hoi_vien,
                "so_buoi_pt_co_the_xep": 0,
            }

            theo_ma_hoi_vien[ma_hoi_vien] = thong_tin
            ket_qua.append(thong_tin)

        theo_ma_hoi_vien[ma_hoi_vien][
            "so_buoi_pt_co_the_xep"
        ] += so_buoi_co_the_xep

    return ket_qua


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def tao_buoi_tap_pt_moi(request):
    le_tan = _lay_le_tan_dang_nhap(request)

    cap_nhat_trang_thai_toan_bo()

    if request.method == "POST":
        tu_khoa = (
            request.POST.get("tu_khoa", "")
            .strip()
        )
        ma_hoi_vien_da_chon = request.POST.get(
            "hoi_vien",
            "",
        )
    else:
        tu_khoa = (
            request.GET.get("tu_khoa", "")
            .strip()
        )
        ma_hoi_vien_da_chon = request.GET.get(
            "hoi_vien",
            "",
        )

    hoi_vien_da_chon = (
        HoiVien.objects
        .filter(pk=ma_hoi_vien_da_chon)
        .first()
        if ma_hoi_vien_da_chon
        else None
    )

    form = BuoiTapPTForm(
        request.POST or None,
        initial={
            "hoi_vien": hoi_vien_da_chon,
        },
    )

    if request.method == "POST" and form.is_valid():
        try:
            tao_buoi_tap_pt_cho_hoi_vien(
                hoi_vien=(
                    form.cleaned_data["hoi_vien"]
                ),
                huan_luyen_vien=(
                    form.cleaned_data[
                        "huan_luyen_vien"
                    ]
                ),
                le_tan=le_tan,
                ngay_tap=(
                    form.cleaned_data["ngay_tap"]
                ),
                gio_bat_dau=(
                    form.cleaned_data[
                        "gio_bat_dau"
                    ]
                ),
                gio_ket_thuc=(
                    form.cleaned_data[
                        "gio_ket_thuc"
                    ]
                ),
                ghi_chu=(
                    form.cleaned_data["ghi_chu"]
                ),
            )
        except ValidationError as error:
            if hasattr(error, "error_dict"):
                for ten_truong, cac_loi in (
                    error.error_dict.items()
                ):
                    truong_form = (
                        ten_truong
                        if ten_truong in form.fields
                        else None
                    )

                    for loi in cac_loi:
                        form.add_error(
                            truong_form,
                            loi,
                        )
            else:
                form.add_error(None, error)
        else:
            return redirect(
                "gym:danh_sach_buoi_tap_pt"
            )

    cac_hoi_vien = (
        _lay_hoi_vien_co_the_xep_buoi_pt(
            tu_khoa
        )
    )

    so_buoi_pt_cua_hoi_vien_da_chon = 0

    if hoi_vien_da_chon:
        for thong_tin in cac_hoi_vien:
            if (
                thong_tin["hoi_vien"].pk
                == hoi_vien_da_chon.pk
            ):
                so_buoi_pt_cua_hoi_vien_da_chon = (
                    thong_tin[
                        "so_buoi_pt_co_the_xep"
                    ]
                )
                break

    return render(
        request,
        "gym/buoi_tap_pt/tao_buoi_tap_pt.html",
        {
            "form": form,
            "le_tan": le_tan,
            "tu_khoa": tu_khoa,
            "cac_hoi_vien": cac_hoi_vien,
            "hoi_vien_da_chon": hoi_vien_da_chon,
            "so_buoi_pt_cua_hoi_vien_da_chon": (
                so_buoi_pt_cua_hoi_vien_da_chon
            ),
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
    TaiKhoan.VaiTro.PT,
)
def chi_tiet_buoi_tap_pt(request, ma_buoi):
    buoi_tap = get_object_or_404(
        BuoiTapPT.objects.select_related(
            "dang_ky",
            "dang_ky__hoi_vien",
            "dang_ky__goi_tap",
            "huan_luyen_vien",
            "huan_luyen_vien__tai_khoan",
            "le_tan",
        ),
        pk=ma_buoi,
    )

    form_ket_qua = None
    form_huy = None

    if request.user.vai_tro == TaiKhoan.VaiTro.LE_TAN:
        le_tan = _lay_le_tan_dang_nhap(request)

        if (
            buoi_tap.trang_thai
            == BuoiTapPT.TrangThai.DA_LEN_LICH
        ):
            form_huy = HuyBuoiTapPTForm(
                request.POST or None
            )

            if (
                request.method == "POST"
                and form_huy.is_valid()
            ):
                try:
                    huy_buoi_tap_pt(
                        buoi_tap=buoi_tap,
                        le_tan=le_tan,
                        ly_do_huy=(
                            form_huy.cleaned_data[
                                "ly_do_huy"
                            ]
                        ),
                    )
                except ValidationError as error:
                    if hasattr(error, "error_dict"):
                        for ten_truong, cac_loi in (
                            error.error_dict.items()
                        ):
                            truong_form = (
                                ten_truong
                                if ten_truong
                                in form_huy.fields
                                else None
                            )

                            for loi in cac_loi:
                                form_huy.add_error(
                                    truong_form,
                                    loi,
                                )
                    else:
                        form_huy.add_error(
                            None,
                            error,
                        )
                else:
                    return redirect(
                        "gym:chi_tiet_buoi_tap_pt",
                        ma_buoi=buoi_tap.ma_buoi,
                    )

        elif request.method == "POST":
            raise PermissionDenied(
                "Buổi tập đã được chốt trạng thái "
                "và không thể hủy."
            )

    elif request.user.vai_tro == TaiKhoan.VaiTro.PT:
        huan_luyen_vien = (
            _lay_huan_luyen_vien_dang_nhap(
                request
            )
        )

        if (
            buoi_tap.huan_luyen_vien_id
            != huan_luyen_vien.pk
        ):
            raise PermissionDenied(
                "Huấn luyện viên không được xem "
                "buổi tập của người khác."
            )

        if (
            buoi_tap.trang_thai
            == BuoiTapPT.TrangThai.DA_LEN_LICH
        ):
            form_ket_qua = (
                CapNhatKetQuaBuoiTapPTForm(
                    request.POST or None,
                    initial={
                        "ghi_chu": buoi_tap.ghi_chu,
                    },
                )
            )

            if (
                request.method == "POST"
                and form_ket_qua.is_valid()
            ):
                try:
                    cap_nhat_ket_qua_buoi_tap_pt(
                        buoi_tap=buoi_tap,
                        huan_luyen_vien=(
                            huan_luyen_vien
                        ),
                        trang_thai=(
                            form_ket_qua.cleaned_data[
                                "trang_thai"
                            ]
                        ),
                        ghi_chu=(
                            form_ket_qua.cleaned_data[
                                "ghi_chu"
                            ]
                        ),
                    )
                except ValidationError as error:
                    if hasattr(error, "error_dict"):
                        for ten_truong, cac_loi in (
                            error.error_dict.items()
                        ):
                            truong_form = (
                                ten_truong
                                if ten_truong
                                in form_ket_qua.fields
                                else None
                            )

                            for loi in cac_loi:
                                form_ket_qua.add_error(
                                    truong_form,
                                    loi,
                                )
                    else:
                        form_ket_qua.add_error(
                            None,
                            error,
                        )
                else:
                    return redirect(
                        "gym:chi_tiet_buoi_tap_pt",
                        ma_buoi=buoi_tap.ma_buoi,
                    )

        elif request.method == "POST":
            raise PermissionDenied(
                "Kết quả buổi tập đã được chốt."
            )

    elif request.method == "POST":
        raise PermissionDenied(
            "Admin không được thay đổi "
            "trạng thái buổi tập PT."
        )

    return render(
        request,
        "gym/buoi_tap_pt/"
        "chi_tiet_buoi_tap_pt.html",
        {
            "buoi_tap": buoi_tap,
            "form_ket_qua": form_ket_qua,
            "form_huy": form_huy,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.LE_TAN)
def trang_le_tan(request):
    cap_nhat_trang_thai_toan_bo()

    le_tan = _lay_le_tan_dang_nhap(request)
    hom_nay = timezone.localdate()

    ngay_duoc_chon = hom_nay
    ngay_khong_hop_le = False

    gia_tri_ngay = request.GET.get("ngay", "").strip()

    if gia_tri_ngay:
        try:
            ngay_duoc_chon = date.fromisoformat(
                gia_tri_ngay
            )
        except ValueError:
            ngay_khong_hop_le = True

    cac_buoi_tap_trong_ngay = (
        BuoiTapPT.objects
        .filter(
            ngay_tap=ngay_duoc_chon,
        )
        .select_related(
            "dang_ky",
            "dang_ky__hoi_vien",
            "dang_ky__goi_tap",
            "huan_luyen_vien",
            "le_tan",
        )
        .order_by(
            "gio_bat_dau",
            "gio_ket_thuc",
            "ma_buoi",
        )
    )

    cac_lan_diem_danh_trong_ngay = (
        DiemDanh.objects
        .filter(
            thoi_gian_diem_danh__date=(
                ngay_duoc_chon
            ),
        )
        .select_related(
            "hoi_vien",
            "le_tan",
        )
        .order_by(
            "-thoi_gian_diem_danh",
            "-ma_dd",
        )
    )

    return render(
        request,
        "gym/trang_chu/le_tan.html",
        {
            "le_tan": le_tan,
            "hom_nay": hom_nay,
            "ngay_duoc_chon": ngay_duoc_chon,
            "ngay_khong_hop_le": (
                ngay_khong_hop_le
            ),
            "cac_buoi_tap_trong_ngay": (
                cac_buoi_tap_trong_ngay
            ),
            "cac_lan_diem_danh_gan_nhat": (
                cac_lan_diem_danh_trong_ngay[:5]
            ),
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.PT)
def trang_pt(request):
    cap_nhat_trang_thai_toan_bo()

    return render(
        request,
        "gym/trang_chu/pt.html",
    )

@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def goi_tap_cua_toi(request):
    cap_nhat_trang_thai_toan_bo()

    hoi_vien = _lay_hoi_vien_dang_nhap(request)

    cac_dang_ky = (
        DangKyGoiTap.objects
        .filter(
            hoi_vien=hoi_vien,
        )
        .select_related(
            "goi_tap",
        )
        .order_by("ma_dk")
    )

    return render(
        request,
        (
            "gym/khu_vuc_hoi_vien/"
            "goi_tap_cua_toi.html"
        ),
        {
            "hoi_vien": hoi_vien,
            "cac_dang_ky": cac_dang_ky,
        },
    )

@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def chi_tiet_goi_tap_cua_toi(request, ma_dk):
    cap_nhat_trang_thai_toan_bo()

    hoi_vien = _lay_hoi_vien_dang_nhap(request)

    dang_ky = get_object_or_404(
        DangKyGoiTap.objects.select_related(
            "goi_tap",
            "hoa_don",
            "hoa_don__le_tan",
        ),
        ma_dk=ma_dk,
        hoi_vien=hoi_vien,
    )

    hoa_don = getattr(
        dang_ky,
        "hoa_don",
        None,
    )

    return render(
        request,
        (
            "gym/khu_vuc_hoi_vien/"
            "chi_tiet_goi_tap_cua_toi.html"
        ),
        {
            "hoi_vien": hoi_vien,
            "dang_ky": dang_ky,
            "hoa_don": hoa_don,
        },
    )

@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def lich_tap_pt_cua_toi(request):
    cap_nhat_trang_thai_toan_bo()

    hoi_vien = _lay_hoi_vien_dang_nhap(request)
    hom_nay = timezone.localdate()

    cac_buoi_tap = (
        BuoiTapPT.objects
        .filter(
            dang_ky__hoi_vien=hoi_vien,
        )
        .select_related(
            "dang_ky",
            "dang_ky__goi_tap",
            "huan_luyen_vien",
        )
    )

    cac_buoi_tap_sap_toi = (
        cac_buoi_tap
        .filter(
            trang_thai=(
                BuoiTapPT.TrangThai.DA_LEN_LICH
            ),
            ngay_tap__gte=hom_nay,
        )
        .order_by(
            "ngay_tap",
            "gio_bat_dau",
            "ma_buoi",
        )
    )

    cac_buoi_tap_lich_su = (
        cac_buoi_tap
        .exclude(
            trang_thai=(
                BuoiTapPT.TrangThai.DA_LEN_LICH
            ),
            ngay_tap__gte=hom_nay,
        )
        .order_by(
            "-ngay_tap",
            "-gio_bat_dau",
            "ma_buoi",
        )
    )

    return render(
        request,
        (
            "gym/khu_vuc_hoi_vien/"
            "lich_tap_pt_cua_toi.html"
        ),
        {
            "hoi_vien": hoi_vien,
            "cac_buoi_tap_sap_toi": (
                cac_buoi_tap_sap_toi
            ),
            "cac_buoi_tap_lich_su": (
                cac_buoi_tap_lich_su
            ),
            "so_buoi_sap_toi": (
                cac_buoi_tap_sap_toi.count()
            ),
            "so_buoi_hoan_thanh": (
                cac_buoi_tap
                .filter(
                    trang_thai=(
                        BuoiTapPT.TrangThai.HOAN_THANH
                    )
                )
                .count()
            ),
            "so_buoi_vang": (
                cac_buoi_tap
                .filter(
                    trang_thai=(
                        BuoiTapPT.TrangThai.VANG
                    )
                )
                .count()
            ),
            "so_buoi_huy": (
                cac_buoi_tap
                .filter(
                    trang_thai=(
                        BuoiTapPT.TrangThai.HUY
                    )
                )
                .count()
            ),
        },
    )

@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def lich_su_diem_danh_cua_toi(request):
    cap_nhat_trang_thai_toan_bo()

    hoi_vien = _lay_hoi_vien_dang_nhap(request)
    hom_nay = timezone.localdate()

    cac_lan_diem_danh = (
        DiemDanh.objects
        .filter(
            hoi_vien=hoi_vien,
        )
        .select_related(
            "le_tan",
        )
        .order_by(
            "-thoi_gian_diem_danh",
            "-ma_dd",
        )
    )

    lan_diem_danh_gan_nhat = (
        cac_lan_diem_danh.first()
    )

    return render(
        request,
        (
            "gym/khu_vuc_hoi_vien/"
            "lich_su_diem_danh.html"
        ),
        {
            "hoi_vien": hoi_vien,
            "cac_lan_diem_danh": (
                cac_lan_diem_danh
            ),
            "tong_so_lan_diem_danh": (
                cac_lan_diem_danh.count()
            ),
            "so_lan_diem_danh_hom_nay": (
                cac_lan_diem_danh
                .filter(
                    thoi_gian_diem_danh__date=hom_nay,
                )
                .count()
            ),
            "lan_diem_danh_gan_nhat": (
                lan_diem_danh_gan_nhat
            ),
        },
    )

@vai_tro_required(TaiKhoan.VaiTro.HOI_VIEN)
def trang_hoi_vien(request):
    cap_nhat_trang_thai_toan_bo()

    hoi_vien = _lay_hoi_vien_dang_nhap(request)
    hom_nay = timezone.localdate()

    cac_dang_ky = (
        DangKyGoiTap.objects
        .filter(hoi_vien=hoi_vien)
        .select_related(
            "goi_tap",
            "hoa_don",
        )
        .order_by(
            "-ngay_bat_dau",
            "ma_dk",
        )
    )

    dang_ky_dang_hoat_dong = (
        cac_dang_ky
        .filter(
            trang_thai=(
                DangKyGoiTap.TrangThai.HOAT_DONG
            )
        )
        .order_by(
            "ngay_ket_thuc",
            "ma_dk",
        )
        .first()
    )

    dang_ky_sap_kich_hoat = (
        cac_dang_ky
        .filter(
            trang_thai=(
                DangKyGoiTap.TrangThai.CHUA_KICH_HOAT
            )
        )
        .order_by(
            "ngay_bat_dau",
            "ma_dk",
        )
        .first()
    )

    cac_buoi_tap_pt = (
        BuoiTapPT.objects
        .filter(
            dang_ky__hoi_vien=hoi_vien,
        )
        .select_related(
            "dang_ky",
            "dang_ky__goi_tap",
            "huan_luyen_vien",
        )
    )

    cac_buoi_tap_pt_sap_toi = (
        cac_buoi_tap_pt
        .filter(
            trang_thai=(
                BuoiTapPT.TrangThai.DA_LEN_LICH
            ),
            ngay_tap__gte=hom_nay,
        )
        .order_by(
            "ngay_tap",
            "gio_bat_dau",
            "ma_buoi",
        )[:3]
    )

    lan_diem_danh_gan_nhat = (
        DiemDanh.objects
        .filter(hoi_vien=hoi_vien)
        .order_by(
            "-thoi_gian_diem_danh",
            "ma_dd",
        )
        .first()
    )

    context = {
        "hoi_vien": hoi_vien,
        "tong_so_dang_ky": cac_dang_ky.count(),
        "dang_ky_dang_hoat_dong": (
            dang_ky_dang_hoat_dong
        ),
        "dang_ky_sap_kich_hoat": (
            dang_ky_sap_kich_hoat
        ),
        "so_buoi_pt_da_len_lich": (
            cac_buoi_tap_pt
            .filter(
                trang_thai=(
                    BuoiTapPT.TrangThai.DA_LEN_LICH
                )
            )
            .count()
        ),
        "cac_buoi_tap_pt_sap_toi": (
            cac_buoi_tap_pt_sap_toi
        ),
        "lan_diem_danh_gan_nhat": (
            lan_diem_danh_gan_nhat
        ),
    }

    return render(
        request,
        "gym/trang_chu/hoi_vien.html",
        context,
    )