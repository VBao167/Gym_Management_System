from django.contrib import messages
from django.contrib.auth import (
    update_session_auth_hash,
)
from django.core.exceptions import (
    ObjectDoesNotExist,
    PermissionDenied,
    ValidationError,
)
from django.db.models import Q
from django.http import HttpResponseBadRequest
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from accounts.decorators import vai_tro_required
from accounts.forms import (
    DatLaiMatKhauForm,
    DoiMatKhauForm,
)
from accounts.models import TaiKhoan
from accounts.services.tai_khoan import (
    cap_nhat_trang_thai_tai_khoan,
)


def _lay_ten_nguoi_dung(tai_khoan):
    quan_he_theo_vai_tro = {
        TaiKhoan.VaiTro.HOI_VIEN: (
            "ho_so_hoi_vien"
        ),
        TaiKhoan.VaiTro.LE_TAN: (
            "ho_so_le_tan"
        ),
        TaiKhoan.VaiTro.PT: (
            "ho_so_huan_luyen_vien"
        ),
    }

    ten_quan_he = quan_he_theo_vai_tro.get(
        tai_khoan.vai_tro
    )

    if ten_quan_he is None:
        return tai_khoan.username

    try:
        return getattr(
            tai_khoan,
            ten_quan_he,
        ).ho_ten
    except ObjectDoesNotExist:
        return "Chưa có hồ sơ"


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def danh_sach_tai_khoan(request):
    tu_khoa = request.GET.get(
        "tu_khoa",
        "",
    ).strip()

    vai_tro = request.GET.get(
        "vai_tro",
        "",
    ).strip()

    trang_thai = request.GET.get(
        "trang_thai",
        "",
    ).strip()

    if vai_tro not in set(
        TaiKhoan.VaiTro.values
    ):
        vai_tro = ""

    if trang_thai not in {
        "hoat_dong",
        "bi_khoa",
    }:
        trang_thai = ""

    cac_tai_khoan = (
        TaiKhoan.objects
        .select_related(
            "ho_so_hoi_vien",
            "ho_so_le_tan",
            "ho_so_huan_luyen_vien",
        )
    )

    if tu_khoa:
        cac_tai_khoan = cac_tai_khoan.filter(
            Q(ma_tk__icontains=tu_khoa)
            | Q(username__icontains=tu_khoa)
            | Q(
                ho_so_hoi_vien__ho_ten__icontains=(
                    tu_khoa
                )
            )
            | Q(
                ho_so_le_tan__ho_ten__icontains=(
                    tu_khoa
                )
            )
            | Q(
                ho_so_huan_luyen_vien__ho_ten__icontains=(
                    tu_khoa
                )
            )
        )

    if vai_tro:
        cac_tai_khoan = cac_tai_khoan.filter(
            vai_tro=vai_tro
        )

    if trang_thai == "hoat_dong":
        cac_tai_khoan = cac_tai_khoan.filter(
            is_active=True
        )
    elif trang_thai == "bi_khoa":
        cac_tai_khoan = cac_tai_khoan.filter(
            is_active=False
        )

    cac_tai_khoan = list(
        cac_tai_khoan.order_by("ma_tk")
    )

    for tai_khoan in cac_tai_khoan:
        tai_khoan.ten_nguoi_dung = (
            _lay_ten_nguoi_dung(
                tai_khoan
            )
        )

    return render(
        request,
        "accounts/danh_sach_tai_khoan.html",
        {
            "cac_tai_khoan": cac_tai_khoan,
            "tu_khoa": tu_khoa,
            "vai_tro_duoc_chon": vai_tro,
            "trang_thai_duoc_chon": trang_thai,
            "cac_vai_tro": (
                TaiKhoan.VaiTro.choices
            ),
        },
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.HOI_VIEN,
)
def doi_mat_khau_cua_toi(request):
    form = DoiMatKhauForm(
        request.user,
        request.POST or None,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):
        tai_khoan = form.save()

        update_session_auth_hash(
            request,
            tai_khoan,
        )

        messages.success(
            request,
            "Đổi mật khẩu thành công.",
        )

        if (
            request.user.vai_tro
            == TaiKhoan.VaiTro.ADMIN
        ):
            return redirect(
                "accounts:danh_sach_tai_khoan"
            )

        return redirect(
            "gym:trang_hoi_vien"
        )

    return render(
        request,
        "accounts/doi_mat_khau.html",
        {
            "form": form,
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
def dat_lai_mat_khau(request, ma_tk):
    tai_khoan = get_object_or_404(
        TaiKhoan,
        pk=ma_tk,
    )

    if (
        tai_khoan.vai_tro
        == TaiKhoan.VaiTro.ADMIN
    ):
        raise PermissionDenied(
            "Quản trị viên không được đặt lại "
            "mật khẩu của quản trị viên khác."
        )

    form = DatLaiMatKhauForm(
        tai_khoan,
        request.POST or None,
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):
        form.save()

        messages.success(
            request,
            (
                "Đã đặt lại mật khẩu cho "
                f"{tai_khoan.username}."
            ),
        )

        return redirect(
            "accounts:danh_sach_tai_khoan"
        )

    return render(
        request,
        "accounts/dat_lai_mat_khau.html",
        {
            "form": form,
            "tai_khoan": tai_khoan,
            "ten_nguoi_dung": (
                _lay_ten_nguoi_dung(
                    tai_khoan
                )
            ),
        },
    )


@vai_tro_required(TaiKhoan.VaiTro.ADMIN)
@require_POST
def doi_trang_thai_tai_khoan(
    request,
    ma_tk,
):
    tai_khoan = get_object_or_404(
        TaiKhoan,
        pk=ma_tk,
    )

    if (
        tai_khoan.vai_tro
        == TaiKhoan.VaiTro.ADMIN
    ):
        raise PermissionDenied(
            "Không được thay đổi trạng thái "
            "tài khoản quản trị viên."
        )

    try:
        tai_khoan = (
            cap_nhat_trang_thai_tai_khoan(
                tai_khoan=tai_khoan,
                hanh_dong=request.POST.get(
                    "hanh_dong",
                    "",
                ),
            )
        )
    except ValidationError as error:
        return HttpResponseBadRequest(
            error.messages[0]
        )

    if tai_khoan.is_active:
        noi_dung = "Đã mở khóa tài khoản."
    else:
        noi_dung = "Đã khóa tài khoản."

    messages.success(
        request,
        noi_dung,
    )

    return redirect(
        "accounts:danh_sach_tai_khoan"
    )


@vai_tro_required(
    TaiKhoan.VaiTro.ADMIN,
    TaiKhoan.VaiTro.LE_TAN,
    TaiKhoan.VaiTro.PT,
    TaiKhoan.VaiTro.HOI_VIEN,
)
def trang_chu(request):
    dieu_huong_theo_vai_tro = {
        TaiKhoan.VaiTro.ADMIN: (
            "gym:trang_quan_tri"
        ),
        TaiKhoan.VaiTro.LE_TAN: (
            "gym:trang_le_tan"
        ),
        TaiKhoan.VaiTro.PT: (
            "gym:trang_pt"
        ),
        TaiKhoan.VaiTro.HOI_VIEN: (
            "gym:trang_hoi_vien"
        ),
    }

    ten_url = dieu_huong_theo_vai_tro.get(
        request.user.vai_tro
    )

    if ten_url is None:
        raise PermissionDenied(
            "Tài khoản không có vai trò hợp lệ."
        )

    return redirect(ten_url)