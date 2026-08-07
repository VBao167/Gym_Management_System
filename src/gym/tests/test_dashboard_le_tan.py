from datetime import date, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import TaiKhoan
from gym.models import GoiTap, HoaDon
from gym.services.buoi_tap_pt import (
    tao_buoi_tap_pt,
)
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)
from gym.services.diem_danh import tao_diem_danh


class DashboardLeTanTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()
        self.ngay_mai = (
            self.hom_nay + timedelta(days=1)
        )

        self.le_tan_1 = tao_le_tan(
            ho_ten="Lễ tân xếp lịch",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0961000001",
            email="le.tan.dashboard.1@example.com",
            dia_chi="TP.HCM",
        )

        self.le_tan_2 = tao_le_tan(
            ho_ten="Lễ tân xem lịch",
            gioi_tinh="Nam",
            ngay_sinh=date(2000, 2, 2),
            sdt="0961000002",
            email="le.tan.dashboard.2@example.com",
            dia_chi="TP.HCM",
        )

        self.huan_luyen_vien = (
            tao_huan_luyen_vien(
                ho_ten="PT kiểm thử dashboard",
                gioi_tinh="Nam",
                ngay_sinh=date(1998, 3, 3),
                sdt="0961000003",
                email="pt.dashboard@example.com",
                dia_chi="TP.HCM",
            )
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên có lịch PT",
            gioi_tinh="Nữ",
            ngay_sinh=date(2001, 4, 4),
            sdt="0961000004",
            email="hoi.vien.dashboard@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_pt = GoiTap.objects.create(
            ten_goi="Gói PT kiểm thử dashboard",
            thoi_han_ngay=30,
            gia_tien=900000,
            co_pt=True,
            so_buoi_pt=10,
            mo_ta="Dùng để kiểm thử trang Lễ tân",
            trang_thai=True,
        )

        self.dang_ky, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_pt,
                le_tan=self.le_tan_1,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.diem_danh_1 = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan_1,
            ghi_chu="Điểm danh đầu tiên",
        )

        self.diem_danh_2 = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan_2,
            ghi_chu="Điểm danh gần nhất",
        )

        self.buoi_sang = tao_buoi_tap_pt(
            dang_ky=self.dang_ky,
            huan_luyen_vien=self.huan_luyen_vien,
            le_tan=self.le_tan_1,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(8, 0),
            gio_ket_thuc=time(9, 0),
            ghi_chu="Buổi sáng",
        )

        self.buoi_chieu = tao_buoi_tap_pt(
            dang_ky=self.dang_ky,
            huan_luyen_vien=self.huan_luyen_vien,
            le_tan=self.le_tan_1,
            ngay_tap=self.hom_nay,
            gio_bat_dau=time(14, 0),
            gio_ket_thuc=time(15, 0),
            ghi_chu="Buổi chiều",
        )

        self.buoi_ngay_mai = tao_buoi_tap_pt(
            dang_ky=self.dang_ky,
            huan_luyen_vien=self.huan_luyen_vien,
            le_tan=self.le_tan_1,
            ngay_tap=self.ngay_mai,
            gio_bat_dau=time(9, 0),
            gio_ket_thuc=time(10, 0),
            ghi_chu="Buổi ngày mai",
        )

        self.url = reverse("gym:trang_le_tan")

    def test_mac_dinh_hien_thi_lich_pt_hom_nay(
        self
    ):
        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/trang_chu/le_tan.html",
        )
        self.assertEqual(
            response.context["ngay_duoc_chon"],
            self.hom_nay,
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_trong_ngay"
                ]
            ),
            [
                self.buoi_sang,
                self.buoi_chieu,
            ],
        )

        self.assertContains(
            response,
            self.buoi_sang.ma_buoi,
        )
        self.assertContains(
            response,
            self.buoi_chieu.ma_buoi,
        )
        self.assertNotContains(
            response,
            self.buoi_ngay_mai.ma_buoi,
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_lan_diem_danh_gan_nhat"
                ]
            ),
            [
                self.diem_danh_2,
                self.diem_danh_1,
            ],
        )

        self.assertContains(
            response,
            self.diem_danh_1.ma_dd,
        )
        self.assertContains(
            response,
            self.diem_danh_2.ma_dd,
        )
        self.assertContains(
            response,
            "Điểm danh Hội viên",
        )

    def test_co_the_chon_ngay_khac_de_xem_lich(
        self
    ):
        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        response = self.client.get(
            self.url,
            {
                "ngay": self.ngay_mai.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["ngay_duoc_chon"],
            self.ngay_mai,
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_trong_ngay"
                ]
            ),
            [self.buoi_ngay_mai],
        )
        self.assertContains(
            response,
            self.buoi_ngay_mai.ma_buoi,
        )
        self.assertNotContains(
            response,
            self.buoi_sang.ma_buoi,
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_lan_diem_danh_gan_nhat"
                ]
            ),
            [],
        )

        self.assertNotContains(
            response,
            self.diem_danh_1.ma_dd,
        )
        self.assertNotContains(
            response,
            self.diem_danh_2.ma_dd,
        )

    def test_ngay_khong_hop_le_quay_ve_hom_nay(
        self
    ):
        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        response = self.client.get(
            self.url,
            {
                "ngay": "khong-phai-ngay",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.context[
                "ngay_khong_hop_le"
            ]
        )
        self.assertEqual(
            response.context["ngay_duoc_chon"],
            self.hom_nay,
        )
        self.assertContains(
            response,
            "Ngày được nhập không hợp lệ.",
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_lan_diem_danh_gan_nhat"
                ]
            ),
            [
                self.diem_danh_2,
                self.diem_danh_1,
            ],
        )

        self.assertContains(
            response,
            self.buoi_sang.ma_buoi,
        )
        self.assertContains(
            response,
            self.diem_danh_2.ma_dd,
        )

    def test_le_tan_khac_thay_lich_do_le_tan_truoc_xep(
        self
    ):
        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertContains(
            response,
            self.buoi_sang.ma_buoi,
        )
        self.assertContains(
            response,
            reverse(
                "gym:chi_tiet_buoi_tap_pt",
                args=[self.buoi_sang.ma_buoi],
            ),
        )
        self.assertContains(
            response,
            reverse("gym:tao_diem_danh_moi"),
        )

    def test_le_tan_khong_co_ho_so_bi_tu_choi(
        self
    ):
        tai_khoan = TaiKhoan.objects.create_user(
            username="le_tan_khong_co_ho_so_dashboard",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.client.force_login(tai_khoan)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_chi_hien_thi_nam_luot_diem_danh_gan_nhat(
        self
    ):
        for thu_tu in range(4):
            tao_diem_danh(
                hoi_vien=self.hoi_vien,
                le_tan=self.le_tan_1,
                ghi_chu=(
                    f"Điểm danh bổ sung {thu_tu}"
                ),
            )

        self.client.force_login(
            self.le_tan_2.tai_khoan
        )

        response = self.client.get(self.url)

        cac_lan_gan_nhat = list(
            response.context[
                "cac_lan_diem_danh_gan_nhat"
            ]
        )

        self.assertEqual(
            len(cac_lan_gan_nhat),
            5,
        )
        self.assertNotIn(
            self.diem_danh_1,
            cac_lan_gan_nhat,
        )