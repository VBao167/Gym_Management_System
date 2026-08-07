from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import TaiKhoan
from gym.models import (
    BuoiTapPT,
    DiemDanh,
    GoiTap,
    HoaDon,
)
from gym.services.bao_cao import (
    lay_thong_ke_bao_cao,
)
from gym.services.buoi_tap_pt import (
    tao_buoi_tap_pt,
)
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)
from gym.services.diem_danh import (
    tao_diem_danh,
)
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)


class BaoCaoThongKeTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()
        self.ngay_mai = (
            self.hom_nay + timedelta(days=1)
        )
        self.ngay_sau = (
            self.hom_nay + timedelta(days=2)
        )

        self.admin = TaiKhoan.objects.create_user(
            username="admin_bao_cao",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân báo cáo",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0951000001",
            email="le.tan.bao.cao@example.com",
            dia_chi="TP.HCM",
        )

        self.huan_luyen_vien = (
            tao_huan_luyen_vien(
                ho_ten="PT báo cáo",
                gioi_tinh="Nam",
                ngay_sinh=date(1998, 2, 2),
                sdt="0951000002",
                email="pt.bao.cao@example.com",
                dia_chi="TP.HCM",
            )
        )

        self.hoi_vien_1 = tao_hoi_vien(
            ho_ten="Hội viên báo cáo thứ nhất",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 3, 3),
            sdt="0951000003",
            email="hoi.vien.bao.cao.1@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien_2 = tao_hoi_vien(
            ho_ten="Hội viên báo cáo thứ hai",
            gioi_tinh="Nữ",
            ngay_sinh=date(2001, 4, 4),
            sdt="0951000004",
            email="hoi.vien.bao.cao.2@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_pt = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử báo cáo",
            thoi_han_ngay=30,
            gia_tien=900000,
            co_pt=True,
            so_buoi_pt=10,
            mo_ta="Dữ liệu kiểm thử báo cáo",
            trang_thai=True,
        )

        self.dang_ky_trong_khoang, (
            self.hoa_don_trong_khoang
        ) = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_1,
            goi_tap=self.goi_pt,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        self.dang_ky_ngoai_khoang, (
            self.hoa_don_ngoai_khoang
        ) = tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_2,
            goi_tap=self.goi_pt,
            le_tan=self.le_tan,
            ngay_dang_ky=self.ngay_sau,
            ngay_bat_dau=self.ngay_sau,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.CHUYEN_KHOAN
            ),
        )

        thoi_diem_ngoai_khoang = (
            timezone.make_aware(
                datetime.combine(
                    self.ngay_sau,
                    time(10, 0),
                ),
                timezone.get_current_timezone(),
            )
        )

        HoaDon.objects.filter(
            pk=self.hoa_don_ngoai_khoang.pk,
        ).update(
            ngay_lap=thoi_diem_ngoai_khoang,
        )

        self.diem_danh_trong_khoang = (
            tao_diem_danh(
                hoi_vien=self.hoi_vien_1,
                le_tan=self.le_tan,
                ghi_chu="Trong khoảng báo cáo",
            )
        )

        self.diem_danh_ngoai_khoang = (
            tao_diem_danh(
                hoi_vien=self.hoi_vien_1,
                le_tan=self.le_tan,
                ghi_chu="Ngoài khoảng báo cáo",
            )
        )

        DiemDanh.objects.filter(
            pk=self.diem_danh_ngoai_khoang.pk,
        ).update(
            thoi_gian_diem_danh=(
                thoi_diem_ngoai_khoang
            ),
        )

        self.buoi_da_len_lich = (
            self._tao_buoi_pt(
                gio_bat_dau=time(8, 0),
                gio_ket_thuc=time(9, 0),
            )
        )

        self.buoi_hoan_thanh = (
            self._tao_buoi_pt(
                gio_bat_dau=time(9, 0),
                gio_ket_thuc=time(10, 0),
                trang_thai=(
                    BuoiTapPT.TrangThai.HOAN_THANH
                ),
            )
        )

        self.buoi_vang = self._tao_buoi_pt(
            gio_bat_dau=time(10, 0),
            gio_ket_thuc=time(11, 0),
            trang_thai=(
                BuoiTapPT.TrangThai.VANG
            ),
        )

        self.buoi_huy = self._tao_buoi_pt(
            gio_bat_dau=time(11, 0),
            gio_ket_thuc=time(12, 0),
            trang_thai=(
                BuoiTapPT.TrangThai.HUY
            ),
        )

        self.buoi_ngoai_khoang = (
            tao_buoi_tap_pt(
                dang_ky=self.dang_ky_ngoai_khoang,
                huan_luyen_vien=(
                    self.huan_luyen_vien
                ),
                le_tan=self.le_tan,
                ngay_tap=self.ngay_sau,
                gio_bat_dau=time(13, 0),
                gio_ket_thuc=time(14, 0),
            )
        )

        self.url = reverse(
            "gym:bao_cao_thong_ke"
        )

    def _tao_buoi_pt(
        self,
        *,
        gio_bat_dau,
        gio_ket_thuc,
        trang_thai=None,
    ):
        buoi_tap = tao_buoi_tap_pt(
            dang_ky=self.dang_ky_trong_khoang,
            huan_luyen_vien=(
                self.huan_luyen_vien
            ),
            le_tan=self.le_tan,
            ngay_tap=self.ngay_mai,
            gio_bat_dau=gio_bat_dau,
            gio_ket_thuc=gio_ket_thuc,
        )

        if trang_thai is not None:
            BuoiTapPT.objects.filter(
                pk=buoi_tap.pk,
            ).update(
                trang_thai=trang_thai,
            )

            buoi_tap.refresh_from_db()

        return buoi_tap

    def test_service_tong_hop_dung_du_lieu_trong_khoang(
        self
    ):
        thong_ke = lay_thong_ke_bao_cao(
            tu_ngay=self.hom_nay,
            den_ngay=self.ngay_mai,
        )

        self.assertEqual(
            thong_ke["tong_doanh_thu"],
            Decimal("900000.00"),
        )
        self.assertEqual(
            thong_ke["so_dang_ky_goi"],
            1,
        )
        self.assertEqual(
            thong_ke["so_luot_diem_danh"],
            1,
        )
        self.assertEqual(
            thong_ke["tong_buoi_pt"],
            4,
        )
        self.assertEqual(
            thong_ke["so_buoi_da_len_lich"],
            1,
        )
        self.assertEqual(
            thong_ke["so_buoi_hoan_thanh"],
            1,
        )
        self.assertEqual(
            thong_ke["so_buoi_vang"],
            1,
        )
        self.assertEqual(
            thong_ke["so_buoi_huy"],
            1,
        )

    def test_service_chan_tu_ngay_sau_den_ngay(
        self
    ):
        with self.assertRaisesMessage(
            ValueError,
            "Từ ngày không được sau Đến ngày.",
        ):
            lay_thong_ke_bao_cao(
                tu_ngay=self.ngay_mai,
                den_ngay=self.hom_nay,
            )

    def test_admin_xem_bao_cao_mac_dinh_thang_hien_tai(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertTemplateUsed(
            response,
            "gym/bao_cao/bao_cao_thong_ke.html",
        )
        self.assertEqual(
            response.context["tu_ngay"],
            self.hom_nay.replace(day=1),
        )
        self.assertEqual(
            response.context["den_ngay"],
            self.hom_nay,
        )
        self.assertIsNotNone(
            response.context["thong_ke"]
        )

        self.assertContains(
            response,
            "Tổng doanh thu",
        )
        self.assertContains(
            response,
            "Đăng ký gói",
        )
        self.assertContains(
            response,
            "Lượt điểm danh",
        )
        self.assertContains(
            response,
            "Tổng buổi PT",
        )

    def test_admin_loc_bao_cao_theo_khoang_ngay(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {
                "tu_ngay": (
                    self.hom_nay.isoformat()
                ),
                "den_ngay": (
                    self.ngay_mai.isoformat()
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["tu_ngay"],
            self.hom_nay,
        )
        self.assertEqual(
            response.context["den_ngay"],
            self.ngay_mai,
        )

        thong_ke = response.context[
            "thong_ke"
        ]

        self.assertEqual(
            thong_ke["tong_doanh_thu"],
            Decimal("900000.00"),
        )
        self.assertEqual(
            thong_ke["so_dang_ky_goi"],
            1,
        )
        self.assertEqual(
            thong_ke["so_luot_diem_danh"],
            1,
        )
        self.assertEqual(
            thong_ke["tong_buoi_pt"],
            4,
        )

    def test_khoang_ngay_nguoc_khong_tinh_bao_cao(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {
                "tu_ngay": (
                    self.ngay_mai.isoformat()
                ),
                "den_ngay": (
                    self.hom_nay.isoformat()
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIsNone(
            response.context["thong_ke"]
        )
        self.assertEqual(
            response.context["thong_bao_loi"],
            (
                "Từ ngày không được sau "
                "Đến ngày."
            ),
        )
        self.assertContains(
            response,
            "Từ ngày không được sau Đến ngày.",
        )

    def test_ngay_khong_hop_le_khong_tinh_bao_cao(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(
            self.url,
            {
                "tu_ngay": "khong-phai-ngay",
                "den_ngay": (
                    self.hom_nay.isoformat()
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertIsNone(
            response.context["thong_ke"]
        )
        self.assertEqual(
            response.context["thong_bao_loi"],
            "Từ ngày không hợp lệ.",
        )
        self.assertContains(
            response,
            "Từ ngày không hợp lệ.",
        )

    def test_chi_admin_duoc_xem_bao_cao(
        self
    ):
        cac_tai_khoan_khong_duoc_phep = [
            self.le_tan.tai_khoan,
            self.huan_luyen_vien.tai_khoan,
            self.hoi_vien_1.tai_khoan,
        ]

        for tai_khoan in (
            cac_tai_khoan_khong_duoc_phep
        ):
            with self.subTest(
                vai_tro=tai_khoan.vai_tro
            ):
                self.client.force_login(
                    tai_khoan
                )

                response = self.client.get(
                    self.url
                )

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_chua_dang_nhap_bi_chuyen_den_dang_nhap(
        self
    ):
        response = self.client.get(self.url)

        dang_nhap_url = reverse(
            "accounts:dang_nhap"
        )

        self.assertRedirects(
            response,
            (
                f"{dang_nhap_url}"
                f"?next={self.url}"
            ),
        )

    def test_menu_admin_co_duong_dan_bao_cao(
        self
    ):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            self.url,
        )
        self.assertContains(
            response,
            "Báo cáo",
        )