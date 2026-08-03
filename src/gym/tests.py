from datetime import date, time, timedelta
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
)
from gym.services.buoi_tap_pt import (
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


class TaoNguoiDungServiceTests(TestCase):
    def test_tao_hoi_vien_kem_tai_khoan(self):
        hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên kiểm thử",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0901000001",
            email="hoi.vien@example.com",
            dia_chi="TP.HCM",
        )

        self.assertRegex(hoi_vien.ma_hv, r"^HV\d+$")
        self.assertFalse(hoi_vien.trang_thai)

        tai_khoan = hoi_vien.tai_khoan

        self.assertRegex(tai_khoan.ma_tk, r"^TK\d+$")
        self.assertEqual(tai_khoan.username, hoi_vien.ma_hv)
        self.assertEqual(
            tai_khoan.vai_tro,
            TaiKhoan.VaiTro.HOI_VIEN,
        )
        self.assertTrue(tai_khoan.is_active)
        self.assertTrue(tai_khoan.check_password("1"))

    def test_tao_le_tan_va_huan_luyen_vien(self):
        le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0901000002",
            email="le.tan@example.com",
            dia_chi="TP.HCM",
        )

        huan_luyen_vien = tao_huan_luyen_vien(
            ho_ten="PT kiểm thử",
            gioi_tinh="Nam",
            ngay_sinh=date(1999, 3, 3),
            sdt="0901000003",
            email="pt@example.com",
            dia_chi="TP.HCM",
        )

        self.assertRegex(le_tan.ma_lt, r"^LT\d+$")
        self.assertEqual(
            le_tan.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.LE_TAN,
        )
        self.assertTrue(le_tan.tai_khoan.is_active)
        self.assertTrue(le_tan.tai_khoan.check_password("1"))

        self.assertRegex(
            huan_luyen_vien.ma_pt,
            r"^PT\d+$",
        )
        self.assertEqual(
            huan_luyen_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.PT,
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan.is_active
        )
        self.assertTrue(
            huan_luyen_vien.tai_khoan.check_password("1")
        )

    def test_du_lieu_hoi_vien_loi_duoc_rollback(self):
        with self.assertRaises(ValidationError):
            tao_hoi_vien(
                ho_ten="Hội viên lỗi",
                gioi_tinh="Nam",
                ngay_sinh=date(2000, 4, 4),
                sdt="0901000004",
                email="email-khong-hop-le",
                dia_chi="TP.HCM",
            )

        self.assertEqual(HoiVien.objects.count(), 0)
        self.assertEqual(TaiKhoan.objects.count(), 0)

    def test_ma_ho_so_duoc_sinh_khac_nhau(self):
        hoi_vien_1 = tao_hoi_vien(
            ho_ten="Hội viên thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 5, 5),
            sdt="0901000005",
            email="hoi.vien.1@example.com",
            dia_chi="TP.HCM",
        )

        hoi_vien_2 = tao_hoi_vien(
            ho_ten="Hội viên thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 6, 6),
            sdt="0901000006",
            email="hoi.vien.2@example.com",
            dia_chi="TP.HCM",
        )

        self.assertNotEqual(
            hoi_vien_1.ma_hv,
            hoi_vien_2.ma_hv,
        )
        self.assertNotEqual(
            hoi_vien_1.tai_khoan_id,
            hoi_vien_2.tai_khoan_id,
        )

class DangKyGoiVaHoaDonServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên đăng ký gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0911000001",
            email="dang.ky@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân lập hóa đơn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0911000002",
            email="lap.hoa.don@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử",
            thoi_han_ngay=30,
            gia_tien=500000,
            co_pt=True,
            so_buoi_pt=5,
            mo_ta="Kiểm thử đăng ký và hóa đơn",
            trang_thai=True,
        )

    def test_tao_dang_ky_va_hoa_don_thanh_cong(self):
        dang_ky, hoa_don = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertRegex(dang_ky.ma_dk, r"^DK\d+$")
        self.assertRegex(hoa_don.ma_hd, r"^HD\d+$")

        self.assertEqual(
            dang_ky.ngay_ket_thuc,
            self.hom_nay + timedelta(days=29),
        )
        self.assertEqual(dang_ky.so_buoi_pt_dang_ky, 5)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        self.assertEqual(hoa_don.dang_ky, dang_ky)
        self.assertEqual(hoa_don.le_tan, self.le_tan)
        self.assertEqual(
            hoa_don.tong_tien,
            self.goi_tap.gia_tien,
        )

        self.hoi_vien.refresh_from_db()
        self.assertTrue(self.hoi_vien.trang_thai)

    def test_gia_hoa_don_duoc_luu_theo_thoi_diem_dang_ky(self):
        _, hoa_don = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.CHUYEN_KHOAN
            ),
        )

        tong_tien_ban_dau = hoa_don.tong_tien

        self.goi_tap.gia_tien = 750000
        self.goi_tap.save()

        hoa_don.refresh_from_db()

        self.assertEqual(
            hoa_don.tong_tien,
            tong_tien_ban_dau,
        )
        self.assertNotEqual(
            hoa_don.tong_tien,
            self.goi_tap.gia_tien,
        )

    def test_hoa_don_loi_thi_dang_ky_duoc_rollback(self):
        with self.assertRaises(ValidationError):
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_tap,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan="KhongHopLe",
            )

        self.assertEqual(DangKyGoiTap.objects.count(), 0)
        self.assertEqual(HoaDon.objects.count(), 0)

        self.hoi_vien.refresh_from_db()
        self.assertFalse(self.hoi_vien.trang_thai)

class GiaHanGoiServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên gia hạn",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0921000001",
            email="gia.han@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân gia hạn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0921000002",
            email="le.tan.gia.han@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói gia hạn kiểm thử",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Kiểm thử gia hạn",
            trang_thai=True,
        )

    def test_chua_co_goi_thi_bat_dau_tu_ngay_dang_ky(self):
        dang_ky, hoa_don = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertEqual(
            dang_ky.ngay_bat_dau,
            self.hom_nay,
        )
        self.assertEqual(
            dang_ky.ngay_ket_thuc,
            self.hom_nay + timedelta(days=9),
        )
        self.assertEqual(hoa_don.dang_ky, dang_ky)

    def test_goi_moi_noi_tiep_sau_goi_hien_tai(self):
        dang_ky_hien_tai, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        dang_ky_gia_han, _ = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.CHUYEN_KHOAN
            ),
        )

        self.assertEqual(
            dang_ky_gia_han.ngay_bat_dau,
            dang_ky_hien_tai.ngay_ket_thuc
            + timedelta(days=1),
        )
        self.assertEqual(
            dang_ky_hien_tai.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertEqual(
            dang_ky_gia_han.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )

    def test_goi_cu_da_het_thi_mua_lai_tu_hom_nay(self):
        ngay_bat_dau_cu = self.hom_nay - timedelta(days=20)

        dang_ky_cu, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_bat_dau_cu,
            ngay_bat_dau=ngay_bat_dau_cu,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        dang_ky_moi, _ = gia_han_goi(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.assertLess(
            dang_ky_cu.ngay_ket_thuc,
            self.hom_nay,
        )
        self.assertEqual(
            dang_ky_moi.ngay_bat_dau,
            self.hom_nay,
        )

        self.hoi_vien.refresh_from_db()
        self.assertTrue(self.hoi_vien.trang_thai)

class TrangThaiVaDiemDanhServiceTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên điểm danh",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 1, 1),
            sdt="0931000001",
            email="diem.danh@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân điểm danh",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0931000002",
            email="le.tan.diem.danh@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap = GoiTap.objects.create(
            ten_goi="Gói điểm danh kiểm thử",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Kiểm thử trạng thái và điểm danh",
            trang_thai=True,
        )

    def tao_dang_ky(self, ngay_bat_dau):
        dang_ky, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_bat_dau,
            ngay_bat_dau=ngay_bat_dau,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        return dang_ky

    def test_dong_bo_goi_dang_hieu_luc(self):
        dang_ky = self.tao_dang_ky(self.hom_nay)

        DangKyGoiTap.objects.filter(
            pk=dang_ky.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
        )

        HoiVien.objects.filter(
            pk=self.hoi_vien.pk,
        ).update(
            trang_thai=False,
        )

        ket_qua = cap_nhat_trang_thai_hoi_vien(
            self.hoi_vien,
        )

        dang_ky.refresh_from_db()
        self.hoi_vien.refresh_from_db()

        self.assertTrue(ket_qua)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertTrue(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_dong_bo_goi_het_han_khong_khoa_tai_khoan(self):
        ngay_bat_dau = self.hom_nay - timedelta(days=20)
        dang_ky = self.tao_dang_ky(ngay_bat_dau)

        DangKyGoiTap.objects.filter(
            pk=dang_ky.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        HoiVien.objects.filter(
            pk=self.hoi_vien.pk,
        ).update(
            trang_thai=True,
        )

        ket_qua = cap_nhat_trang_thai_hoi_vien(
            self.hoi_vien,
        )

        dang_ky.refresh_from_db()
        self.hoi_vien.refresh_from_db()

        self.assertFalse(ket_qua)
        self.assertEqual(
            dang_ky.trang_thai,
            DangKyGoiTap.TrangThai.HET_HAN,
        )
        self.assertFalse(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_hoi_vien_con_han_duoc_diem_danh(self):
        self.tao_dang_ky(self.hom_nay)

        diem_danh = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan,
            ghi_chu="Điểm danh hợp lệ",
        )

        self.assertRegex(diem_danh.ma_dd, r"^DD\d+$")
        self.assertEqual(
            diem_danh.hoi_vien,
            self.hoi_vien,
        )
        self.assertEqual(
            diem_danh.le_tan,
            self.le_tan,
        )
        self.assertEqual(DiemDanh.objects.count(), 1)

    def test_dong_bo_trang_thai_toan_bo_hoi_vien(self):
        dang_ky_dang_hoat_dong = self.tao_dang_ky(
            self.hom_nay
        )

        hoi_vien_het_han = tao_hoi_vien(
            ho_ten="Hội viên đã hết hạn",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0931000011",
            email="hoi.vien.het.han@example.com",
            dia_chi="TP.HCM",
        )

        dang_ky_het_han, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien_het_han,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay - timedelta(days=20),
            ngay_bat_dau=self.hom_nay - timedelta(days=20),
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        hoi_vien_tuong_lai = tao_hoi_vien(
            ho_ten="Hội viên có gói tương lai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0931000012",
            email="hoi.vien.tuong.lai@example.com",
            dia_chi="TP.HCM",
        )

        dang_ky_tuong_lai, _ = tao_dang_ky_va_hoa_don(
            hoi_vien=hoi_vien_tuong_lai,
            goi_tap=self.goi_tap,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay + timedelta(days=5),
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        hoi_vien_chua_co_goi = tao_hoi_vien(
            ho_ten="Hội viên chưa có gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2003, 3, 3),
            sdt="0931000013",
            email="hoi.vien.chua.co.goi@example.com",
            dia_chi="TP.HCM",
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_dang_hoat_dong.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HET_HAN,
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_het_han.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        DangKyGoiTap.objects.filter(
            pk=dang_ky_tuong_lai.pk,
        ).update(
            trang_thai=DangKyGoiTap.TrangThai.HOAT_DONG,
        )

        HoiVien.objects.update(trang_thai=True)

        so_hoi_vien = cap_nhat_trang_thai_toan_bo()

        dang_ky_dang_hoat_dong.refresh_from_db()
        dang_ky_het_han.refresh_from_db()
        dang_ky_tuong_lai.refresh_from_db()

        self.hoi_vien.refresh_from_db()
        hoi_vien_het_han.refresh_from_db()
        hoi_vien_tuong_lai.refresh_from_db()
        hoi_vien_chua_co_goi.refresh_from_db()

        self.assertEqual(so_hoi_vien, 4)

        self.assertEqual(
            dang_ky_dang_hoat_dong.trang_thai,
            DangKyGoiTap.TrangThai.HOAT_DONG,
        )
        self.assertTrue(self.hoi_vien.trang_thai)

        self.assertEqual(
            dang_ky_het_han.trang_thai,
            DangKyGoiTap.TrangThai.HET_HAN,
        )
        self.assertFalse(hoi_vien_het_han.trang_thai)

        self.assertEqual(
            dang_ky_tuong_lai.trang_thai,
            DangKyGoiTap.TrangThai.CHUA_KICH_HOAT,
        )
        self.assertFalse(hoi_vien_tuong_lai.trang_thai)

        self.assertFalse(hoi_vien_chua_co_goi.trang_thai)

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_het_han.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_tuong_lai.tai_khoan.is_active
        )
        self.assertTrue(
            hoi_vien_chua_co_goi.tai_khoan.is_active
        )

    def test_hoi_vien_het_han_bi_chan_diem_danh(self):
        ngay_bat_dau = self.hom_nay - timedelta(days=20)
        self.tao_dang_ky(ngay_bat_dau)

        with self.assertRaises(ValidationError):
            tao_diem_danh(
                hoi_vien=self.hoi_vien,
                le_tan=self.le_tan,
            )

        self.hoi_vien.refresh_from_db()

        self.assertEqual(DiemDanh.objects.count(), 0)
        self.assertFalse(self.hoi_vien.trang_thai)
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_tai_khoan_le_tan_bi_khoa_thi_khong_diem_danh(self):
        self.tao_dang_ky(self.hom_nay)

        self.le_tan.tai_khoan.is_active = False
        self.le_tan.tai_khoan.save(
            update_fields=["is_active"],
        )

        with self.assertRaises(ValidationError):
            tao_diem_danh(
                hoi_vien=self.hoi_vien,
                le_tan=self.le_tan,
            )

        self.assertEqual(DiemDanh.objects.count(), 0)

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

class PhanQuyenVaiTroTests(TestCase):
    def setUp(self):
        self.tai_khoan_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_admin",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.ADMIN,
                ),
            TaiKhoan.VaiTro.LE_TAN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_le_tan",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.LE_TAN,
                ),
            TaiKhoan.VaiTro.PT:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_pt",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.PT,
                ),
            TaiKhoan.VaiTro.HOI_VIEN:
                TaiKhoan.objects.create_user(
                    username="kiem_thu_hoi_vien",
                    password="1",
                    vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
                ),
        }

        self.khu_vuc_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN: (
                "gym:trang_quan_tri",
                "Tổng quan hệ thống",
            ),
            TaiKhoan.VaiTro.LE_TAN: (
                "gym:trang_le_tan",
                "Khu vực Lễ tân.",
            ),
            TaiKhoan.VaiTro.PT: (
                "gym:trang_pt",
                "Khu vực Huấn luyện viên.",
            ),
            TaiKhoan.VaiTro.HOI_VIEN: (
                "gym:trang_hoi_vien",
                "Khu vực Hội viên.",
            ),
        }

    def test_chua_dang_nhap_bi_chuyen_den_trang_dang_nhap(self):
        dang_nhap_url = reverse("accounts:dang_nhap")

        for ten_url, _ in self.khu_vuc_theo_vai_tro.values():
            with self.subTest(ten_url=ten_url):
                khu_vuc_url = reverse(ten_url)

                response = self.client.get(khu_vuc_url)

                self.assertRedirects(
                    response,
                    f"{dang_nhap_url}?next={khu_vuc_url}",
                )

    def test_trang_chu_dieu_huong_dung_theo_vai_tro(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                response = self.client.get(
                    reverse("accounts:trang_chu")
                )

                self.assertRedirects(
                    response,
                    reverse(ten_url),
                )

    def test_moi_vai_tro_truy_cap_duoc_khu_vuc_cua_minh(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, noi_dung = (
                    self.khu_vuc_theo_vai_tro[vai_tro]
                )

                response = self.client.get(
                    reverse(ten_url)
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, noi_dung)

    def test_truy_cap_khu_vuc_khac_bi_tu_choi(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            self.client.force_login(tai_khoan)

            for vai_tro_muc_tieu, (
                ten_url,
                _,
            ) in self.khu_vuc_theo_vai_tro.items():
                if vai_tro_muc_tieu == vai_tro:
                    continue

                with self.subTest(
                    vai_tro=vai_tro,
                    vai_tro_muc_tieu=vai_tro_muc_tieu,
                ):
                    response = self.client.get(
                        reverse(ten_url)
                    )

                    self.assertEqual(
                        response.status_code,
                        403,
                    )

    def test_moi_khu_vuc_su_dung_dung_template(self):
        template_theo_vai_tro = {
            TaiKhoan.VaiTro.ADMIN:
                "users/quan_tri.html",
            TaiKhoan.VaiTro.LE_TAN:
                "users/le_tan.html",
            TaiKhoan.VaiTro.PT:
                "users/pt.html",
            TaiKhoan.VaiTro.HOI_VIEN:
                "users/hoi_vien.html",
        }

        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                response = self.client.get(
                    reverse(ten_url)
                )

                self.assertTemplateUsed(
                    response,
                    template_theo_vai_tro[vai_tro],
                )
                self.assertTemplateUsed(
                    response,
                    "base.html",
                )

    def test_moi_trang_chinh_goi_dong_bo_toan_bo(self):
        for vai_tro, tai_khoan in (
            self.tai_khoan_theo_vai_tro.items()
        ):
            with self.subTest(vai_tro=vai_tro):
                self.client.force_login(tai_khoan)

                ten_url, _ = self.khu_vuc_theo_vai_tro[
                    vai_tro
                ]

                with patch(
                    "gym.views.cap_nhat_trang_thai_toan_bo"
                ) as ham_dong_bo:
                    response = self.client.get(
                        reverse(ten_url)
                    )

                self.assertEqual(response.status_code, 200)
                ham_dong_bo.assert_called_once_with()

class DashboardQuanTriTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.admin = TaiKhoan.objects.create_user(
            username="admin_dashboard",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân Dashboard",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0941000001",
            email="le.tan.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_tap_dang_kinh_doanh = GoiTap.objects.create(
            ten_goi="Gói Dashboard hoạt động",
            thoi_han_ngay=10,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói đang kinh doanh",
            trang_thai=True,
        )

        GoiTap.objects.create(
            ten_goi="Gói Dashboard ngừng kinh doanh",
            thoi_han_ngay=10,
            gia_tien=200000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói đã ngừng kinh doanh",
            trang_thai=False,
        )

        self.hoi_vien_dang_hoat_dong = tao_hoi_vien(
            ho_ten="Hội viên đang hoạt động",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0941000002",
            email="hoi.vien.hoat.dong@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_het_han = tao_hoi_vien(
            ho_ten="Hội viên hết hạn",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0941000003",
            email="hoi.vien.het.han.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        tao_hoi_vien(
            ho_ten="Hội viên chưa có gói",
            gioi_tinh="Nam",
            ngay_sinh=date(2003, 3, 3),
            sdt="0941000004",
            email="hoi.vien.chua.co.goi.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            goi_tap=self.goi_tap_dang_kinh_doanh,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        ngay_cu = self.hom_nay - timedelta(days=20)

        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_het_han,
            goi_tap=self.goi_tap_dang_kinh_doanh,
            le_tan=self.le_tan,
            ngay_dang_ky=ngay_cu,
            ngay_bat_dau=ngay_cu,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        tao_diem_danh(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            le_tan=self.le_tan,
        )

        diem_danh_hom_qua = tao_diem_danh(
            hoi_vien=self.hoi_vien_dang_hoat_dong,
            le_tan=self.le_tan,
        )

        DiemDanh.objects.filter(
            pk=diem_danh_hom_qua.pk,
        ).update(
            thoi_gian_diem_danh=(
                timezone.now() - timedelta(days=1)
            ),
        )

    def test_dashboard_hien_thi_dung_so_lieu(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:trang_quan_tri")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri.html",
        )

        self.assertEqual(
            response.context["tong_hoi_vien"],
            3,
        )
        self.assertEqual(
            response.context["hoi_vien_dang_hoat_dong"],
            1,
        )
        self.assertEqual(
            response.context["goi_tap_dang_kinh_doanh"],
            1,
        )
        self.assertEqual(
            response.context["diem_danh_hom_nay"],
            1,
        )

        self.assertContains(
            response,
            "Tổng quan hệ thống",
        )

class DanhSachHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_danh_sach_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.tai_khoan_le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_co_quyen",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien_1 = tao_hoi_vien(
            ho_ten="Nguyễn Văn An",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 1, 1),
            sdt="0951000001",
            email="nguyen.van.an@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_2 = tao_hoi_vien(
            ho_ten="Trần Thị Bình",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 2, 2),
            sdt="0951000002",
            email="tran.thi.binh@example.com",
            dia_chi="TP.HCM",
        )

    def test_admin_xem_duoc_danh_sach_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/danh_sach_hoi_vien.html",
        )

        cac_hoi_vien = list(
            response.context["cac_hoi_vien"]
        )

        self.assertEqual(len(cac_hoi_vien), 2)
        self.assertEqual(
            [hoi_vien.ma_hv for hoi_vien in cac_hoi_vien],
            sorted(
                [
                    self.hoi_vien_1.ma_hv,
                    self.hoi_vien_2.ma_hv,
                ]
            ),
        )

        self.assertContains(response, "Nguyễn Văn An")
        self.assertContains(response, "Trần Thị Bình")

    def test_danh_sach_rong_hien_thi_thong_bao(self):
        HoiVien.objects.all().delete()

        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Chưa có hội viên trong hệ thống.",
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.tai_khoan_le_tan)

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 403)

    def test_danh_sach_dong_bo_trang_thai_truoc_khi_hien_thi(self):
        self.client.force_login(self.admin)

        with patch(
            "gym.views.cap_nhat_trang_thai_toan_bo"
        ) as ham_dong_bo:
            response = self.client.get(
                reverse("gym:danh_sach_hoi_vien")
            )

        self.assertEqual(response.status_code, 200)
        ham_dong_bo.assert_called_once_with()

class TaoHoiVienTuGiaoDienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_tao_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_tao_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.url = reverse("gym:tao_hoi_vien_moi")

        self.du_lieu_hop_le = {
            "ho_ten": "Nguyễn Minh Khang",
            "gioi_tinh": "Nam",
            "ngay_sinh": "2002-01-01",
            "sdt": "0961000001",
            "email": "minh.khang@example.com",
            "dia_chi": "TP.HCM",
        }

    def test_admin_xem_duoc_form_tao_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "users/quan_tri/tao_hoi_vien.html",
        )
        self.assertContains(
            response,
            "Thông tin hội viên mới",
        )

    def test_admin_tao_hoi_vien_kem_tai_khoan_thanh_cong(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            self.du_lieu_hop_le,
        )

        self.assertRedirects(
            response,
            reverse("gym:danh_sach_hoi_vien"),
        )

        self.assertEqual(HoiVien.objects.count(), 1)

        hoi_vien = HoiVien.objects.select_related(
            "tai_khoan"
        ).get()

        self.assertEqual(
            hoi_vien.ho_ten,
            "Nguyễn Minh Khang",
        )
        self.assertFalse(hoi_vien.trang_thai)

        self.assertEqual(
            hoi_vien.tai_khoan.username,
            hoi_vien.ma_hv,
        )
        self.assertEqual(
            hoi_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.HOI_VIEN,
        )
        self.assertTrue(hoi_vien.tai_khoan.is_active)
        self.assertTrue(
            hoi_vien.tai_khoan.check_password("1")
        )

    def test_du_lieu_khong_hop_le_khong_tao_hoi_vien(self):
        self.client.force_login(self.admin)

        du_lieu_loi = self.du_lieu_hop_le.copy()
        du_lieu_loi["email"] = "email-khong-hop-le"

        response = self.client.post(
            self.url,
            du_lieu_loi,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context["form"].is_valid()
        )
        self.assertIn(
            "email",
            response.context["form"].errors,
        )
        self.assertEqual(HoiVien.objects.count(), 0)

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(self):
        self.client.force_login(self.le_tan)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)