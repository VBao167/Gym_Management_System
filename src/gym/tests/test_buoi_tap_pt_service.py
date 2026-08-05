from datetime import date, datetime, time, timedelta
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import TaiKhoan
from gym.models import (
    BuoiTapPT,
    DangKyGoiTap,
    DiemDanh,
    GoiTap,
    HoaDon,
    HoiVien,
    HuanLuyenVien,
    LeTan,
)
from gym.services.buoi_tap_pt import (
    cap_nhat_ket_qua_buoi_tap_pt,
    tao_buoi_tap_pt,
    tao_buoi_tap_pt_tu_doi_tuong,
)
from gym.services.dang_ky_goi import tao_dang_ky_va_hoa_don
from gym.services.diem_danh import tao_diem_danh
from gym.services.gia_han_goi import gia_han_goi
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)
from gym.services.trang_thai_hoi_vien import (
    cap_nhat_trang_thai_hoi_vien,
    cap_nhat_trang_thai_toan_bo,
)


class BuoiTapPTServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân xếp lịch PT",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0941000001",
            email="le.tan.pt@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_1 = tao_huan_luyen_vien(
            ho_ten="PT thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(1998, 2, 2),
            sdt="0941000002",
            email="pt.1@example.com",
            dia_chi="TP.HCM",
        )

        self.pt_2 = tao_huan_luyen_vien(
            ho_ten="PT thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(1999, 3, 3),
            sdt="0941000003",
            email="pt.2@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_1 = tao_hoi_vien(
            ho_ten="Hội viên dùng PT sớm",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 4, 4),
            sdt="0941000004",
            email="hoi.vien.pt.1@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_2 = tao_hoi_vien(
            ho_ten="Hội viên PT thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 5, 5),
            sdt="0941000005",
            email="hoi.vien.pt.2@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_vao_gym = GoiTap.objects.create(
            ten_goi="Gói vào gym kiểm thử",
            thoi_han_ngay=30,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói bảo đảm quyền vào gym",
            trang_thai=True,
        )

        self.goi_pt = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử",
            thoi_han_ngay=10,
            gia_tien=500000,
            co_pt=True,
            so_buoi_pt=2,
            mo_ta="Gói có hai buổi PT",
            trang_thai=True,
        )

        dang_ky_vao_gym, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_1,
            goi_tap=self.goi_vao_gym,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.dang_ky_pt_tuong_lai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_1,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=(
                    dang_ky_vao_gym.ngay_ket_thuc
                    + timedelta(days=1)
                ),
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.dang_ky_pt_hien_tai, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_2,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

    def assert_loi_truong(self, truong, ham):
        with self.assertRaises(ValidationError) as context:
            ham()

        self.assertIn(
            truong,
            context.exception.message_dict,
        )

    def test_duoc_dung_som_buoi_pt_khi_co_quyen_vao_gym(self):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assertRegex(buoi_tap.ma_buoi, r"^Buoi\d+$")
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )
        self.assertEqual(
            self.dang_ky_pt_tuong_lai.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )

    def test_chan_trung_lich_hoi_vien(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assert_loi_truong(
            "dang_ky",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_tuong_lai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(8, 30),
                gio_ket_thuc=time(9, 30),
            ),
        )

    def test_chan_trung_lich_huan_luyen_vien(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(8, 30),
                gio_ket_thuc=time(9, 30),
            ),
        )

    def test_chan_vuot_so_buoi_pt(self):
        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
        )

        tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.assert_loi_truong(
            "dang_ky",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_tuong_lai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.assertEqual(BuoiTapPT.objects.count(), 2)

    def test_chan_pt_nghi_viec_hoac_bi_khoa(self):
        self.pt_2.trang_thai = False
        self.pt_2.save(update_fields=["trang_thai"])

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.pt_2.trang_thai = True
        self.pt_2.save(update_fields=["trang_thai"])
        self.pt_2.tai_khoan.is_active = False
        self.pt_2.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_2,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

    def test_chan_le_tan_nghi_viec_hoac_bi_khoa(self):
        self.le_tan.trang_thai = False
        self.le_tan.save(update_fields=["trang_thai"])

        self.assert_loi_truong(
            "le_tan",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

        self.le_tan.trang_thai = True
        self.le_tan.save(update_fields=["trang_thai"])
        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.assert_loi_truong(
            "le_tan",
            lambda: tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_hien_tai,
                huan_luyen_vien=self.pt_1,
                le_tan=self.le_tan,
                ngay_tap=self.hom_nay,
                gio_bat_dau=time(10, 0),
                gio_ket_thuc=time(11, 0),
            ),
        )

    def test_buoi_moi_bat_buoc_la_da_len_lich(self):
        buoi_tap = BuoiTapPT(
            dang_ky=self.dang_ky_pt_hien_tai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(11, 0),
            gio_ket_thuc=time(12, 0),
            trang_thai=BuoiTapPT.TrangThai.HOAN_THANH,
        )

        self.assert_loi_truong(
            "trang_thai",
            lambda: tao_buoi_tap_pt_tu_doi_tuong(
                buoi_tap
            ),
        )

        self.assertEqual(BuoiTapPT.objects.count(), 0)

    def test_chan_hoan_thanh_va_vang_truoc_khi_ket_thuc(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(8, 0),
            )
        )

        for trang_thai in (
            BuoiTapPT.TrangThai.HOAN_THANH,
            BuoiTapPT.TrangThai.VANG,
        ):
            with self.subTest(trang_thai=trang_thai):
                with patch(
                    (
                        "gym.services.buoi_tap_pt."
                        "timezone.now"
                    ),
                    return_value=thoi_diem_hien_tai,
                ):
                    self.assert_loi_truong(
                        "trang_thai",
                        lambda: (
                            cap_nhat_ket_qua_buoi_tap_pt(
                                buoi_tap=buoi_tap,
                                huan_luyen_vien=self.pt_1,
                                trang_thai=trang_thai,
                            )
                        ),
                    )

        buoi_tap.refresh_from_db()
        self.assertEqual(
            buoi_tap.trang_thai,
            BuoiTapPT.TrangThai.DA_LEN_LICH,
        )

    def test_cho_phep_hoan_thanh_sau_khi_ket_thuc(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        thoi_diem_hien_tai = timezone.make_aware(
            datetime.combine(
                self.hom_nay,
                time(10, 30),
            )
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_hien_tai,
        ):
            ket_qua = cap_nhat_ket_qua_buoi_tap_pt(
                buoi_tap=buoi_tap,
                huan_luyen_vien=self.pt_1,
                trang_thai=(
                    BuoiTapPT.TrangThai.HOAN_THANH
                ),
                ghi_chu="Đã hoàn thành buổi tập",
            )

        self.assertEqual(
            ket_qua.trang_thai,
            BuoiTapPT.TrangThai.HOAN_THANH,
        )
        self.assertEqual(
            ket_qua.ghi_chu,
            "Đã hoàn thành buổi tập",
        )

    def test_cho_phep_huy_truoc_khi_buoi_tap_ket_thuc(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        ket_qua = cap_nhat_ket_qua_buoi_tap_pt(
            buoi_tap=buoi_tap,
            huan_luyen_vien=self.pt_1,
            trang_thai=BuoiTapPT.TrangThai.HUY,
            ghi_chu="Hủy trước giờ tập",
        )

        self.assertEqual(
            ket_qua.trang_thai,
            BuoiTapPT.TrangThai.HUY,
        )

    def test_chan_pt_khac_cap_nhat_ket_qua(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        self.assert_loi_truong(
            "huan_luyen_vien",
            lambda: cap_nhat_ket_qua_buoi_tap_pt(
                buoi_tap=buoi_tap,
                huan_luyen_vien=self.pt_2,
                trang_thai=BuoiTapPT.TrangThai.HUY,
            ),
        )

    def test_chan_cap_nhat_lai_ket_qua_da_chot(
        self
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_pt_tuong_lai,
            huan_luyen_vien=self.pt_1,
            le_tan=self.le_tan,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
        )

        cap_nhat_ket_qua_buoi_tap_pt(
            buoi_tap=buoi_tap,
            huan_luyen_vien=self.pt_1,
            trang_thai=BuoiTapPT.TrangThai.HUY,
        )

        self.assert_loi_truong(
            "trang_thai",
            lambda: cap_nhat_ket_qua_buoi_tap_pt(
                buoi_tap=buoi_tap,
                huan_luyen_vien=self.pt_1,
                trang_thai=(
                    BuoiTapPT.TrangThai.HOAN_THANH
                ),
            ),
        )
