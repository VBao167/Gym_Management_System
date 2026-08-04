from django import forms

from gym.models import GoiTap, HoiVien


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
