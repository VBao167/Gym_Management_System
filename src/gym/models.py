from django.conf import settings
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from common.ma_tu_dong import MaTuDongMixin


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

class GoiTap(MaTuDongMixin, models.Model):
    MA_PREFIX = "Goi"
    ma_goi = models.CharField(
        max_length=10,
        primary_key=True,
        editable=False,
        db_column="MaGoi",
    )

    ten_goi = models.CharField(
        max_length=100,
        db_column="TenGoi",
    )

    thoi_han_ngay = models.IntegerField(
        db_column="ThoiHanNgay",
    )

    gia_tien = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        db_column="GiaTien",
    )

    co_pt = models.BooleanField(
        default=False,
        db_column="CoPT",
    )

    so_buoi_pt = models.IntegerField(
        default=0,
        db_column="SoBuoiPT",
    )

    mo_ta = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="MoTa",
    )

    trang_thai = models.BooleanField(
        default=True,
        db_column="TrangThai",
    )

    class Meta:
        db_table = "GoiTap"
        ordering = ("ma_goi",)

        constraints = [
            models.CheckConstraint(
                condition=models.Q(thoi_han_ngay__gt=0),
                name="CK_GoiTap_ThoiHanNgay_Positive",
            ),
            models.CheckConstraint(
                condition=models.Q(gia_tien__gte=0),
                name="CK_GoiTap_GiaTien_NonNegative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(co_pt=False, so_buoi_pt=0)
                    | models.Q(co_pt=True, so_buoi_pt__gt=0)
                ),
                name="CK_GoiTap_CoPT_SoBuoiPT",
            ),
        ]

    def __str__(self):
        return f"{self.ma_goi} - {self.ten_goi}"

class DangKyGoiTap(models.Model):
    class TrangThai(models.TextChoices):
        CHUA_KICH_HOAT = "ChuaKichHoat", "Chưa kích hoạt"
        HOAT_DONG = "HoatDong", "Hoạt động"
        HET_HAN = "HetHan", "Hết hạn"

    ma_dk = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaDK",
    )

    hoi_vien = models.ForeignKey(
        HoiVien,
        on_delete=models.PROTECT,
        db_column="MaHV",
        related_name="cac_dang_ky_goi",
    )

    goi_tap = models.ForeignKey(
        GoiTap,
        on_delete=models.PROTECT,
        db_column="MaGoi",
        related_name="cac_luot_dang_ky",
    )

    ngay_dang_ky = models.DateField(
        default=timezone.localdate,
        db_column="NgayDangKy",
    )

    ngay_bat_dau = models.DateField(
        db_column="NgayBatDau",
    )

    ngay_ket_thuc = models.DateField(
        editable=False,
        db_column="NgayKetThuc",
    )

    so_buoi_pt_dang_ky = models.IntegerField(
        default=0,
        editable=False,
        db_column="SoBuoiPTDangKy",
    )

    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.CHUA_KICH_HOAT,
        editable=False,
        db_column="TrangThai",
    )

    ghi_chu = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="GhiChu",
    )

    class Meta:
        db_table = "DangKyGoiTap"
        ordering = ("-ngay_dang_ky", "ma_dk")

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    ngay_ket_thuc__gte=models.F("ngay_bat_dau")
                ),
                name="CK_DangKy_NgayKetThuc",
            ),
            models.CheckConstraint(
                condition=models.Q(so_buoi_pt_dang_ky__gte=0),
                name="CK_DangKy_SoBuoiPTDangKy",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    trang_thai__in=[
                        "ChuaKichHoat",
                        "HoatDong",
                        "HetHan",
                    ]
                ),
                name="CK_DangKy_TrangThai",
            ),
        ]

    def gan_du_lieu_tu_dong(self):
        if (
            self._state.adding
            and self.goi_tap_id
            and self.ngay_bat_dau
        ):
            self.ngay_ket_thuc = (
                self.ngay_bat_dau
                + timedelta(days=self.goi_tap.thoi_han_ngay - 1)
            )

            self.so_buoi_pt_dang_ky = self.goi_tap.so_buoi_pt

        if self.ngay_bat_dau and self.ngay_ket_thuc:
            hom_nay = timezone.localdate()

            if hom_nay < self.ngay_bat_dau:
                self.trang_thai = self.TrangThai.CHUA_KICH_HOAT
            elif hom_nay <= self.ngay_ket_thuc:
                self.trang_thai = self.TrangThai.HOAT_DONG
            else:
                self.trang_thai = self.TrangThai.HET_HAN

    def clean(self):
        super().clean()
        self.gan_du_lieu_tu_dong()

        if not (
            self.hoi_vien_id
            and self.ngay_bat_dau
            and self.ngay_ket_thuc
        ):
            return

        dang_ky_trung = DangKyGoiTap.objects.filter(
            hoi_vien_id=self.hoi_vien_id,
            ngay_bat_dau__lte=self.ngay_ket_thuc,
            ngay_ket_thuc__gte=self.ngay_bat_dau,
        ).exclude(pk=self.pk)

        if dang_ky_trung.exists():
            raise ValidationError(
                "Hội viên đã có gói tập bị chồng thời gian."
            )

    def save(self, *args, **kwargs):
        self.gan_du_lieu_tu_dong()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ma_dk} - {self.hoi_vien} - {self.goi_tap}"

    @property
    def so_buoi_pt_da_dung(self):
        return self.cac_buoi_tap_pt.filter(
            trang_thai="HoanThanh",
        ).count()

    @property
    def so_buoi_pt_da_len_lich(self):
        return self.cac_buoi_tap_pt.filter(
            trang_thai="DaLenLich",
        ).count()

    @property
    def so_buoi_pt_con_lai(self):
        return max(
            self.so_buoi_pt_dang_ky - self.so_buoi_pt_da_dung,
            0,
        )

    @property
    def so_buoi_pt_co_the_xep_lich(self):
        return max(
            self.so_buoi_pt_dang_ky
            - self.so_buoi_pt_da_dung
            - self.so_buoi_pt_da_len_lich,
            0,
        )

class HoaDon(models.Model):
    class PhuongThucThanhToan(models.TextChoices):
        TIEN_MAT = "TienMat", "Tiền mặt"
        CHUYEN_KHOAN = "ChuyenKhoan", "Chuyển khoản"
        THE = "The", "Thẻ"

    ma_hd = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaHD",
    )

    dang_ky = models.OneToOneField(
        DangKyGoiTap,
        on_delete=models.PROTECT,
        db_column="MaDK",
        related_name="hoa_don",
    )

    le_tan = models.ForeignKey(
        LeTan,
        on_delete=models.PROTECT,
        db_column="MaLT",
        related_name="cac_hoa_don_da_lap",
    )

    ngay_lap = models.DateTimeField(
        default=timezone.now,
        db_column="NgayLap",
    )

    tong_tien = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        editable=False,
        db_column="TongTien",
    )

    phuong_thuc_thanh_toan = models.CharField(
        max_length=30,
        choices=PhuongThucThanhToan.choices,
        db_column="PhuongThucThanhToan",
    )

    ghi_chu = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="GhiChu",
    )

    class Meta:
        db_table = "HoaDon"
        ordering = ("-ngay_lap", "ma_hd")

        constraints = [
            models.CheckConstraint(
                condition=models.Q(tong_tien__gte=0),
                name="CK_HoaDon_TongTien",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    phuong_thuc_thanh_toan__in=[
                        "TienMat",
                        "ChuyenKhoan",
                        "The",
                    ]
                ),
                name="CK_HoaDon_PhuongThucThanhToan",
            ),
        ]

    def gan_tong_tien(self):
        if self._state.adding and self.dang_ky_id:
            self.tong_tien = self.dang_ky.goi_tap.gia_tien

    def save(self, *args, **kwargs):
        self.gan_tong_tien()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ma_hd} - {self.dang_ky.ma_dk}"

class BuoiTapPT(models.Model):
    class TrangThai(models.TextChoices):
        DA_LEN_LICH = "DaLenLich", "Đã lên lịch"
        HOAN_THANH = "HoanThanh", "Hoàn thành"
        VANG = "Vang", "Vắng"
        HUY = "Huy", "Hủy"

    ma_buoi = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaBuoi",
    )

    dang_ky = models.ForeignKey(
        DangKyGoiTap,
        on_delete=models.PROTECT,
        db_column="MaDK",
        related_name="cac_buoi_tap_pt",
    )

    huan_luyen_vien = models.ForeignKey(
        HuanLuyenVien,
        on_delete=models.PROTECT,
        db_column="MaPT",
        related_name="cac_buoi_tap_pt",
    )

    le_tan = models.ForeignKey(
        LeTan,
        on_delete=models.PROTECT,
        db_column="MaLT",
        related_name="cac_buoi_tap_pt_da_sap_xep",
    )

    ngay_tap = models.DateField(
        db_column="NgayTap",
    )

    gio_bat_dau = models.TimeField(
        db_column="GioBatDau",
    )

    gio_ket_thuc = models.TimeField(
        db_column="GioKetThuc",
    )

    trang_thai = models.CharField(
        max_length=20,
        choices=TrangThai.choices,
        default=TrangThai.DA_LEN_LICH,
        db_column="TrangThai",
    )

    ghi_chu = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="GhiChu",
    )

    class Meta:
        db_table = "BuoiTapPT"
        ordering = ("-ngay_tap", "-gio_bat_dau", "ma_buoi")

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    gio_ket_thuc__gt=models.F("gio_bat_dau")
                ),
                name="CK_BuoiTapPT_GioTap",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    trang_thai__in=[
                        "DaLenLich",
                        "HoanThanh",
                        "Vang",
                        "Huy",
                    ]
                ),
                name="CK_BuoiTapPT_TrangThai",
            ),
        ]

    def clean(self):
        super().clean()

        errors = {}

        if (
            self.gio_bat_dau
            and self.gio_ket_thuc
            and self.gio_ket_thuc <= self.gio_bat_dau
        ):
            errors["gio_ket_thuc"] = (
                "Giờ kết thúc phải lớn hơn giờ bắt đầu."
            )

        if self.dang_ky_id:
            dang_ky = self.dang_ky

            if dang_ky.so_buoi_pt_dang_ky <= 0:
                errors["dang_ky"] = (
                    "Đăng ký này không có buổi tập PT."
                )

            if self.ngay_tap:
                if self.ngay_tap < dang_ky.ngay_dang_ky:
                    errors["ngay_tap"] = (
                        "Ngày tập không được trước ngày đăng ký gói PT."
                    )

                elif self.ngay_tap > dang_ky.ngay_ket_thuc:
                    errors["ngay_tap"] = (
                        "Ngày tập không được sau ngày kết thúc "
                        "của đăng ký PT."
                    )

                co_quyen_vao_phong_tap = (
                    DangKyGoiTap.objects.filter(
                        hoi_vien_id=dang_ky.hoi_vien_id,
                        ngay_bat_dau__lte=self.ngay_tap,
                        ngay_ket_thuc__gte=self.ngay_tap,
                    ).exists()
                )

                if not co_quyen_vao_phong_tap:
                    errors["ngay_tap"] = (
                        "Tại ngày tập, hội viên không có gói tập "
                        "còn hiệu lực để vào phòng gym."
                    )

            if self.trang_thai in [
                self.TrangThai.DA_LEN_LICH,
                self.TrangThai.HOAN_THANH,
            ]:
                cac_buoi_khac = BuoiTapPT.objects.filter(
                    dang_ky_id=self.dang_ky_id,
                    trang_thai__in=[
                        self.TrangThai.DA_LEN_LICH,
                        self.TrangThai.HOAN_THANH,
                    ],
                ).exclude(pk=self.pk)

                if (
                    cac_buoi_khac.count()
                    >= dang_ky.so_buoi_pt_dang_ky
                ):
                    errors["dang_ky"] = (
                        "Đăng ký này không còn buổi PT "
                        "có thể xếp lịch."
                    )

        if (
            self.ngay_tap
            and self.gio_bat_dau
            and self.gio_ket_thuc
            and self.trang_thai != self.TrangThai.HUY
        ):
            buoi_trung_pt = BuoiTapPT.objects.filter(
                huan_luyen_vien_id=self.huan_luyen_vien_id,
                ngay_tap=self.ngay_tap,
                gio_bat_dau__lt=self.gio_ket_thuc,
                gio_ket_thuc__gt=self.gio_bat_dau,
            ).exclude(
                pk=self.pk,
            ).exclude(
                trang_thai=self.TrangThai.HUY,
            )

            if buoi_trung_pt.exists():
                errors["huan_luyen_vien"] = (
                    "Huấn luyện viên đã có buổi tập "
                    "trong thời gian này."
                )

            if self.dang_ky_id:
                buoi_trung_hoi_vien = BuoiTapPT.objects.filter(
                    dang_ky__hoi_vien_id=self.dang_ky.hoi_vien_id,
                    ngay_tap=self.ngay_tap,
                    gio_bat_dau__lt=self.gio_ket_thuc,
                    gio_ket_thuc__gt=self.gio_bat_dau,
                ).exclude(
                    pk=self.pk,
                ).exclude(
                    trang_thai=self.TrangThai.HUY,
                )

                if buoi_trung_hoi_vien.exists():
                    errors["dang_ky"] = (
                        "Hội viên đã có buổi tập PT "
                        "trong thời gian này."
                    )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.ma_buoi} - "
            f"{self.ngay_tap} "
            f"{self.gio_bat_dau}"
        )

class DiemDanh(models.Model):
    ma_dd = models.CharField(
        max_length=10,
        primary_key=True,
        db_column="MaDD",
    )

    hoi_vien = models.ForeignKey(
        HoiVien,
        on_delete=models.PROTECT,
        db_column="MaHV",
        related_name="cac_lan_diem_danh",
    )

    le_tan = models.ForeignKey(
        LeTan,
        on_delete=models.PROTECT,
        db_column="MaLT",
        related_name="cac_lan_diem_danh_da_ghi_nhan",
    )

    thoi_gian_diem_danh = models.DateTimeField(
        default=timezone.now,
        db_column="ThoiGianDiemDanh",
    )

    ghi_chu = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="GhiChu",
    )

    class Meta:
        db_table = "DiemDanh"
        ordering = ("-thoi_gian_diem_danh", "ma_dd")

    def cap_nhat_trang_thai_dang_ky(self):
        if not self.hoi_vien_id:
            return

        cac_dang_ky = DangKyGoiTap.objects.filter(
            hoi_vien_id=self.hoi_vien_id,
        )

        for dang_ky in cac_dang_ky:
            trang_thai_cu = dang_ky.trang_thai

            dang_ky.gan_du_lieu_tu_dong()

            if dang_ky.trang_thai != trang_thai_cu:
                DangKyGoiTap.objects.filter(
                    pk=dang_ky.pk,
                ).update(
                    trang_thai=dang_ky.trang_thai,
                )

    def clean(self):
        super().clean()

        if not self.hoi_vien_id:
            return

        co_goi_hoat_dong = DangKyGoiTap.objects.filter(
            hoi_vien_id=self.hoi_vien_id,
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        ).exists()

        if not co_goi_hoat_dong:
            raise ValidationError(
                {
                    "hoi_vien": (
                        "Hội viên không có gói tập đang hoạt động."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.cap_nhat_trang_thai_dang_ky()
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.ma_dd} - "
            f"{self.hoi_vien} - "
            f"{self.thoi_gian_diem_danh}"
        )