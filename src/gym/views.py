from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied, ValidationError

from accounts.decorators import vai_tro_required
from accounts.models import TaiKhoan
from gym.forms import (
    DangKyGoiVaHoaDonForm,
    GiaHanGoiForm,
    GoiTapForm,
    HuanLuyenVienForm,
    LeTanForm,
    TaoHoiVienForm,
)
from gym.models import (
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
        "users/quan_tri.html",
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
        "users/quan_tri/danh_sach_hoi_vien.html",
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
        "users/quan_tri/tao_hoi_vien.html",
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
        "users/quan_tri/tao_hoi_vien.html",
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
        "users/quan_tri/chi_tiet_hoi_vien.html",
        {
            "hoi_vien": hoi_vien,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def danh_sach_goi_tap(request):
    cac_goi_tap = GoiTap.objects.order_by("ma_goi")

    return render(
        request,
        "users/quan_tri/danh_sach_goi_tap.html",
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
        "users/quan_tri/bieu_mau_goi_tap.html",
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
        "users/quan_tri/bieu_mau_goi_tap.html",
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
        "users/quan_tri/danh_sach_nhan_vien.html",
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
        "users/quan_tri/bieu_mau_nhan_vien.html",
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
        "users/quan_tri/chi_tiet_nhan_vien.html",
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
        "users/quan_tri/bieu_mau_nhan_vien.html",
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


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
)
def danh_sach_dang_ky_hoa_don(request):
    cap_nhat_trang_thai_toan_bo()

    cac_dang_ky = (
        DangKyGoiTap.objects
        .select_related(
            "hoi_vien",
            "goi_tap",
            "hoa_don",
            "hoa_don__le_tan",
        )
        .order_by(
            "-ngay_dang_ky",
            "ma_dk",
        )
    )

    return render(
        request,
        "users/dang_ky_hoa_don/"
        "danh_sach_dang_ky_hoa_don.html",
        {
            "cac_dang_ky": cac_dang_ky,
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
        "users/dang_ky_hoa_don/"
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
        "users/dang_ky_hoa_don/"
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
        "users/dang_ky_hoa_don/"
        "chi_tiet_dang_ky_hoa_don.html",
        {
            "dang_ky": dang_ky,
            "hoa_don": hoa_don,
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