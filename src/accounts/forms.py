from django.contrib.auth.forms import (
    PasswordChangeForm,
    SetPasswordForm,
)


class DoiMatKhauForm(PasswordChangeForm):
    error_messages = {
        "password_incorrect": (
            "Mật khẩu hiện tại không đúng."
        ),
        "password_mismatch": (
            "Hai mật khẩu mới không khớp."
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["old_password"].label = (
            "Mật khẩu hiện tại"
        )
        self.fields["new_password1"].label = (
            "Mật khẩu mới"
        )
        self.fields["new_password2"].label = (
            "Xác nhận mật khẩu mới"
        )

        self.fields["old_password"].widget.attrs.update(
            {
                "autocomplete": "current-password",
            }
        )
        self.fields["new_password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
            }
        )


class DatLaiMatKhauForm(SetPasswordForm):
    error_messages = {
        "password_mismatch": (
            "Hai mật khẩu mới không khớp."
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["new_password1"].label = (
            "Mật khẩu mới"
        )
        self.fields["new_password2"].label = (
            "Xác nhận mật khẩu mới"
        )

        self.fields["new_password1"].widget.attrs.update(
            {
                "autocomplete": "new-password",
            }
        )
        self.fields["new_password2"].widget.attrs.update(
            {
                "autocomplete": "new-password",
            }
        )