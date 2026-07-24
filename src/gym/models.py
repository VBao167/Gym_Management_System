from django.conf import settings
from django.db import models
from django.utils import timezone


class GioiTinh(models.TextChoices):
    NAM = "Nam", "Nam"
    NU = "Nữ", "Nữ"


class HoiVien(models.Model):
    ma_hv = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaHV",
    )

    tai_khoan = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="MaTK",
        related_name="ho_so_hoi_vien",
    )

    ho_ten = models.CharField(
        max_length=100,
        db_column="HoTen",
    )

    gioi_tinh = models.CharField(
        max_length=5,
        choices=GioiTinh.choices,
        db_column="GioiTinh",
    )

    ngay_sinh = models.DateField(
        db_column="NgaySinh",
    )

    sdt = models.CharField(
        max_length=15,
        db_column="SDT",
    )

    email = models.EmailField(
        max_length=100,
        db_column="Email",
    )

    dia_chi = models.CharField(
        max_length=255,
        db_column="DiaChi",
    )

    ngay_tham_gia = models.DateField(
        default=timezone.localdate,
        db_column="NgayThamGia",
    )

    trang_thai = models.BooleanField(
        default=True,
        db_column="TrangThai",
    )

    class Meta:
        db_table = "HoiVien"
        ordering = ("ma_hv",)

    def __str__(self):
        return f"{self.ma_hv} - {self.ho_ten}"


class LeTan(models.Model):
    ma_lt = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaLT",
    )

    tai_khoan = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="MaTK",
        related_name="ho_so_le_tan",
    )

    ho_ten = models.CharField(
        max_length=100,
        db_column="HoTen",
    )

    gioi_tinh = models.CharField(
        max_length=5,
        choices=GioiTinh.choices,
        db_column="GioiTinh",
    )

    ngay_sinh = models.DateField(
        db_column="NgaySinh",
    )

    sdt = models.CharField(
        max_length=15,
        db_column="SDT",
    )

    email = models.EmailField(
        max_length=100,
        db_column="Email",
    )

    dia_chi = models.CharField(
        max_length=255,
        db_column="DiaChi",
    )

    ngay_vao_lam = models.DateField(
        default=timezone.localdate,
        db_column="NgayVaoLam",
    )

    trang_thai = models.BooleanField(
        default=True,
        db_column="TrangThai",
    )

    class Meta:
        db_table = "LeTan"
        ordering = ("ma_lt",)

    def __str__(self):
        return f"{self.ma_lt} - {self.ho_ten}"


class HuanLuyenVien(models.Model):
    ma_pt = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaPT",
    )

    tai_khoan = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column="MaTK",
        related_name="ho_so_huan_luyen_vien",
    )

    ho_ten = models.CharField(
        max_length=100,
        db_column="HoTen",
    )

    gioi_tinh = models.CharField(
        max_length=5,
        choices=GioiTinh.choices,
        db_column="GioiTinh",
    )

    ngay_sinh = models.DateField(
        db_column="NgaySinh",
    )

    sdt = models.CharField(
        max_length=15,
        db_column="SDT",
    )

    email = models.EmailField(
        max_length=100,
        db_column="Email",
    )

    dia_chi = models.CharField(
        max_length=255,
        db_column="DiaChi",
    )

    ngay_vao_lam = models.DateField(
        default=timezone.localdate,
        db_column="NgayVaoLam",
    )

    trang_thai = models.BooleanField(
        default=True,
        db_column="TrangThai",
    )

    class Meta:
        db_table = "HuanLuyenVien"
        ordering = ("ma_pt",)

    def __str__(self):
        return f"{self.ma_pt} - {self.ho_ten}"