from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from common.ma_tu_dong import MaTuDongMixin


class TaiKhoan(MaTuDongMixin, AbstractUser):
    MA_PREFIX = "TK"
    class VaiTro(models.TextChoices):
        ADMIN = "Admin", "Quản trị viên"
        LE_TAN = "LeTan", "Lễ tân"
        PT = "PT", "Huấn luyện viên"
        HOI_VIEN = "HoiVien", "Hội viên"

    REQUIRED_FIELDS = ["vai_tro"]

    ma_tk = models.CharField(
        max_length=10,
        primary_key=True,
        editable=False,
        db_column="MaTK",
    )

    username = models.CharField(
        max_length=50,
        unique=True,
        db_column="TenDangNhap",
    )

    password = models.CharField(
        max_length=255,
        db_column="MatKhau",
    )

    vai_tro = models.CharField(
        max_length=20,
        choices=VaiTro.choices,
        db_column="VaiTro",
    )

    is_active = models.BooleanField(
        default=True,
        db_column="TrangThai",
    )

    date_joined = models.DateTimeField(
        default=timezone.now,
        db_column="NgayTao",
    )

    class Meta:
        db_table = "TaiKhoan"

    def __str__(self):
        return f"{self.ma_tk} - {self.username}"