from django import forms

from gym.models import HoiVien


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