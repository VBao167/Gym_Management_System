from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from gym.models import (
    DangKyGoiTap,
    GoiTap,
    HoaDon,
    HoiVien,
    HuanLuyenVien,
    LeTan,
)


class TaoHoiVienForm(forms.ModelForm):
    class Meta:
        model = HoiVien
        fields = (
            "ho_ten",
            "gioi_tinh",
            "ngay_sinh",
            "sdt",
            "email",
            "dia_chi",
        )

        labels = {
            "ho_ten": "Họ và tên",
            "gioi_tinh": "Giới tính",
            "ngay_sinh": "Ngày sinh",
            "sdt": "Số điện thoại",
            "email": "Email",
            "dia_chi": "Địa chỉ",
        }

        widgets = {
            "ho_ten": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập họ và tên",
                    "autocomplete": "name",
                }
            ),
            "gioi_tinh": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "ngay_sinh": forms.DateInput(
                attrs={
                    "class": "form-input",
                    "type": "date",
                }
            ),
            "sdt": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập số điện thoại",
                    "autocomplete": "tel",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập địa chỉ email",
                    "autocomplete": "email",
                }
            ),
            "dia_chi": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "placeholder": "Nhập địa chỉ",
                    "rows": 3,
                }
            ),
        }

NHAN_VIEN_FIELDS = (
    "ho_ten",
    "gioi_tinh",
    "ngay_sinh",
    "sdt",
    "email",
    "dia_chi",
    "ngay_vao_lam",
)

NHAN_VIEN_LABELS = {
    "ho_ten": "Họ và tên",
    "gioi_tinh": "Giới tính",
    "ngay_sinh": "Ngày sinh",
    "sdt": "Số điện thoại",
    "email": "Email",
    "dia_chi": "Địa chỉ",
    "ngay_vao_lam": "Ngày vào làm",
}


def _tao_widgets_nhan_vien():
    return {
        "ho_ten": forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập họ và tên",
                "autocomplete": "name",
            }
        ),
        "gioi_tinh": forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
        "ngay_sinh": forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-input",
                "type": "date",
            },
        ),
        "sdt": forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập số điện thoại",
                "autocomplete": "tel",
            }
        ),
        "email": forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "Nhập địa chỉ email",
                "autocomplete": "email",
            }
        ),
        "dia_chi": forms.Textarea(
            attrs={
                "class": "form-textarea",
                "placeholder": "Nhập địa chỉ",
                "rows": 3,
            }
        ),
        "ngay_vao_lam": forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-input",
                "type": "date",
            },
        ),
    }


class LeTanForm(forms.ModelForm):
    class Meta:
        model = LeTan
        fields = NHAN_VIEN_FIELDS
        labels = NHAN_VIEN_LABELS
        widgets = _tao_widgets_nhan_vien()


class HuanLuyenVienForm(forms.ModelForm):
    class Meta:
        model = HuanLuyenVien
        fields = NHAN_VIEN_FIELDS
        labels = NHAN_VIEN_LABELS
        widgets = _tao_widgets_nhan_vien()

class GoiTapForm(forms.ModelForm):
    thoi_han_ngay = forms.IntegerField(
        min_value=1,
        label="Thời hạn sử dụng (ngày)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "1",
                "placeholder": "Ví dụ: 30",
            }
        ),
    )

    gia_tien = forms.DecimalField(
        min_value=0,
        max_digits=18,
        decimal_places=2,
        label="Giá tiền",
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "0",
                "step": "1000",
                "placeholder": "Ví dụ: 500000",
            }
        ),
    )

    so_buoi_pt = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label="Số buổi PT",
        widget=forms.NumberInput(
            attrs={
                "class": "form-input",
                "min": "0",
                "placeholder": "Nhập 0 nếu gói không có PT",
            }
        ),
    )

    class Meta:
        model = GoiTap
        fields = (
            "ten_goi",
            "thoi_han_ngay",
            "gia_tien",
            "co_pt",
            "so_buoi_pt",
            "mo_ta",
        )

        labels = {
            "ten_goi": "Tên gói tập",
            "co_pt": "Gói có PT",
            "mo_ta": "Mô tả",
        }

        widgets = {
            "ten_goi": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Nhập tên gói tập",
                }
            ),
            "co_pt": forms.CheckboxInput(
                attrs={
                    "class": "form-checkbox",
                }
            ),
            "mo_ta": forms.Textarea(
                attrs={
                    "class": "form-textarea",
                    "placeholder": "Nhập mô tả gói tập",
                    "rows": 3,
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        co_pt = cleaned_data.get("co_pt")
        so_buoi_pt = cleaned_data.get("so_buoi_pt")

        if co_pt:
            if not so_buoi_pt or so_buoi_pt <= 0:
                self.add_error(
                    "so_buoi_pt",
                    "Gói có PT phải có ít nhất một buổi PT.",
                )
        else:
            cleaned_data["so_buoi_pt"] = 0

        return cleaned_data

class DangKyGoiVaHoaDonForm(forms.Form):
    hoi_vien = forms.ModelChoiceField(
        queryset=HoiVien.objects.none(),
        label="Hội viên",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    goi_tap = forms.ModelChoiceField(
        queryset=GoiTap.objects.none(),
        label="Gói tập",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    ngay_bat_dau = forms.DateField(
        label="Ngày bắt đầu",
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "class": "form-input",
                "type": "date",
            },
        ),
    )

    phuong_thuc_thanh_toan = forms.ChoiceField(
        choices=HoaDon.PhuongThucThanhToan.choices,
        label="Phương thức thanh toán",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    ghi_chu_dang_ky = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú đăng ký",
        widget=forms.Textarea(
            attrs={
                "class": "form-textarea",
                "placeholder": "Nhập ghi chú đăng ký nếu có",
                "rows": 3,
            }
        ),
    )

    ghi_chu_hoa_don = forms.CharField(
        required=False,
        max_length=255,
        label="Ghi chú hóa đơn",
        widget=forms.Textarea(
            attrs={
                "class": "form-textarea",
                "placeholder": "Nhập ghi chú hóa đơn nếu có",
                "rows": 3,
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["hoi_vien"].queryset = (
            HoiVien.objects.order_by("ma_hv")
        )

        self.fields["goi_tap"].queryset = (
            GoiTap.objects.filter(
                trang_thai=True,
            ).order_by("ma_goi")
        )

        self.fields["ngay_bat_dau"].initial = (
            timezone.localdate()
        )

    def clean(self):
        cleaned_data = super().clean()

        hoi_vien = cleaned_data.get("hoi_vien")
        goi_tap = cleaned_data.get("goi_tap")
        ngay_bat_dau = cleaned_data.get("ngay_bat_dau")
        ghi_chu = cleaned_data.get(
            "ghi_chu_dang_ky",
            "",
        )

        if not all(
            (
                hoi_vien,
                goi_tap,
                ngay_bat_dau,
            )
        ):
            return cleaned_data

        dang_ky_kiem_tra = DangKyGoiTap(
            hoi_vien=hoi_vien,
            goi_tap=goi_tap,
            ngay_bat_dau=ngay_bat_dau,
            ghi_chu=ghi_chu,
        )

        try:
            dang_ky_kiem_tra.full_clean()
        except ValidationError as error:
            raise forms.ValidationError(
                error.messages
            ) from error

        return cleaned_data

class GiaHanGoiForm(DangKyGoiVaHoaDonForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields.pop("hoi_vien")
        self.fields.pop("ngay_bat_dau")

    def clean(self):
        return forms.Form.clean(self)