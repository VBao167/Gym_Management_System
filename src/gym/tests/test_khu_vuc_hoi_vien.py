from datetime import date, datetime, time, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import TaiKhoan
from gym.models import BuoiTapPT, GoiTap, HoaDon
from gym.services.buoi_tap_pt import (
    cap_nhat_ket_qua_buoi_tap_pt,
    tao_buoi_tap_pt,
)
from gym.services.dang_ky_goi import (
    tao_dang_ky_va_hoa_don,
)
from gym.services.diem_danh import tao_diem_danh
from gym.services.nguoi_dung import (
    tao_hoi_vien,
    tao_huan_luyen_vien,
    tao_le_tan,
)


class TongQuanHoiVienTests(TestCase):
    def setUp(self):
        self.hom_nay = timezone.localdate()

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân kiểm thử khu vực Hội viên",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 1, 1),
            sdt="0971000001",
            email="le.tan.khu.vuc.hv@example.com",
            dia_chi="TP.HCM",
        )

        self.huan_luyen_vien = tao_huan_luyen_vien(
            ho_ten="PT kiểm thử khu vực Hội viên",
            gioi_tinh="Nam",
            ngay_sinh=date(1998, 2, 2),
            sdt="0971000002",
            email="pt.khu.vuc.hv@example.com",
            dia_chi="TP.HCM",
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên xem tổng quan",
            gioi_tinh="Nam",
            ngay_sinh=date(2001, 3, 3),
            sdt="0971000003",
            email="hoi.vien.tong.quan@example.com",
            dia_chi="Bình Chánh, TP.HCM",
        )

        self.hoi_vien_khac = tao_hoi_vien(
            ho_ten="Hội viên không được hiển thị",
            gioi_tinh="Nữ",
            ngay_sinh=date(2002, 4, 4),
            sdt="0971000004",
            email="hoi.vien.khac@example.com",
            dia_chi="TP.HCM",
        )

        self.goi_vao_gym = GoiTap.objects.create(
            ten_goi="Gói đang hiệu lực của Hội viên",
            thoi_han_ngay=30,
            gia_tien=300000,
            co_pt=False,
            so_buoi_pt=0,
            mo_ta="Gói bảo đảm quyền vào phòng gym",
            trang_thai=True,
        )

        self.goi_pt_tiep_theo = GoiTap.objects.create(
            ten_goi="Gói PT tiếp theo của Hội viên",
            thoi_han_ngay=30,
            gia_tien=900000,
            co_pt=True,
            so_buoi_pt=5,
            mo_ta="Gói PT nối tiếp",
            trang_thai=True,
        )

        self.dang_ky_dang_hoat_dong, (
            self.hoa_don_dang_hoat_dong
        ) = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_vao_gym,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.dang_ky_pt_tiep_theo, (
            self.hoa_don_pt_tiep_theo
        ) = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien,
                goi_tap=self.goi_pt_tiep_theo,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=(
                    self.dang_ky_dang_hoat_dong
                    .ngay_ket_thuc
                    + timedelta(days=1)
                ),
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.cac_buoi_pt = []

        for chi_so in range(1, 5):
            buoi_tap = tao_buoi_tap_pt(
                dang_ky=self.dang_ky_pt_tiep_theo,
                huan_luyen_vien=self.huan_luyen_vien,
                le_tan=self.le_tan,
                ngay_tap=(
                    self.hom_nay
                    + timedelta(days=chi_so)
                ),
                gio_bat_dau=time(8, 0),
                gio_ket_thuc=time(9, 0),
                ghi_chu=f"Buổi PT sắp tới {chi_so}",
            )

            self.cac_buoi_pt.append(buoi_tap)

        self.diem_danh = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan,
            ghi_chu="Điểm danh để kiểm thử tổng quan",
        )

        self.url = reverse("gym:trang_hoi_vien")

        self.url_goi_tap = reverse(
            "gym:goi_tap_cua_toi"
        )

        self.url_lich_pt = reverse(
            "gym:lich_tap_pt_cua_toi"
        )

        self.url_lich_su_diem_danh = reverse(
            "gym:lich_su_diem_danh_cua_toi"
        )

    def test_hoi_vien_xem_duoc_tong_quan_cua_minh(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/trang_chu/hoi_vien.html",
        )

        self.assertEqual(
            response.context["hoi_vien"],
            self.hoi_vien,
        )
        self.assertEqual(
            response.context["tong_so_dang_ky"],
            2,
        )
        self.assertEqual(
            response.context[
                "dang_ky_dang_hoat_dong"
            ],
            self.dang_ky_dang_hoat_dong,
        )
        self.assertEqual(
            response.context[
                "dang_ky_sap_kich_hoat"
            ],
            self.dang_ky_pt_tiep_theo,
        )
        self.assertEqual(
            response.context[
                "so_buoi_pt_da_len_lich"
            ],
            4,
        )
        self.assertEqual(
            response.context[
                "lan_diem_danh_gan_nhat"
            ],
            self.diem_danh,
        )

        self.assertContains(
            response,
            "Tổng quan Hội viên",
        )
        self.assertContains(
            response,
            self.hoi_vien.ho_ten,
        )
        self.assertContains(
            response,
            self.goi_vao_gym.ten_goi,
        )
        self.assertContains(
            response,
            self.goi_pt_tiep_theo.ten_goi,
        )
        self.assertNotContains(
            response,
            self.hoi_vien_khac.ho_ten,
        )

    def test_tong_quan_chi_hien_thi_ba_buoi_pt_sap_toi(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(self.url)

        cac_buoi_hien_thi = list(
            response.context[
                "cac_buoi_tap_pt_sap_toi"
            ]
        )

        self.assertEqual(
            cac_buoi_hien_thi,
            self.cac_buoi_pt[:3],
        )

        for buoi_tap in self.cac_buoi_pt[:3]:
            self.assertContains(
                response,
                buoi_tap.ma_buoi,
            )

        self.assertNotContains(
            response,
            self.cac_buoi_pt[3].ma_buoi,
        )

    def test_hoi_vien_chua_co_goi_van_xem_duoc_tong_quan(
        self
    ):
        self.client.force_login(
            self.hoi_vien_khac.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["hoi_vien"],
            self.hoi_vien_khac,
        )
        self.assertEqual(
            response.context["tong_so_dang_ky"],
            0,
        )
        self.assertIsNone(
            response.context[
                "dang_ky_dang_hoat_dong"
            ]
        )
        self.assertIsNone(
            response.context[
                "dang_ky_sap_kich_hoat"
            ]
        )
        self.assertEqual(
            response.context[
                "so_buoi_pt_da_len_lich"
            ],
            0,
        )
        self.assertIsNone(
            response.context[
                "lan_diem_danh_gan_nhat"
            ]
        )

        self.assertContains(
            response,
            (
                "Hiện tại bạn chưa có gói tập "
                "đang hiệu lực."
            ),
        )
        self.assertContains(
            response,
            "Bạn chưa có buổi tập PT sắp tới.",
        )

    def test_tai_khoan_hoi_vien_khong_co_ho_so_bi_tu_choi(
        self
    ):
        tai_khoan_khong_co_ho_so = (
            TaiKhoan.objects.create_user(
                username="hoi_vien_khong_co_ho_so",
                password="1",
                vai_tro=TaiKhoan.VaiTro.HOI_VIEN,
            )
        )

        self.client.force_login(
            tai_khoan_khong_co_ho_so
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_menu_hoi_vien_dan_den_cac_trang_ca_nhan(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "Gói tập của tôi",
        )
        self.assertContains(
            response,
            "Lịch tập PT",
        )
        self.assertContains(
            response,
            "Lịch sử điểm danh",
        )
        self.assertNotContains(
            response,
            reverse("gym:danh_sach_buoi_tap_pt"),
        )
        self.assertContains(
            response,
            self.url_lich_pt,
        )
        self.assertNotContains(
            response,
            reverse("gym:danh_sach_buoi_tap_pt"),
        )
        self.assertContains(
            response,
            self.url_lich_su_diem_danh,
        )

    def test_hoi_vien_xem_danh_sach_goi_theo_thu_tu_ma_dang_ky(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_goi_tap
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "gym/khu_vuc_hoi_vien/"
                "goi_tap_cua_toi.html"
            ),
        )

        self.assertEqual(
            list(response.context["cac_dang_ky"]),
            [
                self.dang_ky_dang_hoat_dong,
                self.dang_ky_pt_tiep_theo,
            ],
        )

        self.assertContains(
            response,
            self.dang_ky_dang_hoat_dong.ma_dk,
        )
        self.assertContains(
            response,
            self.dang_ky_pt_tiep_theo.ma_dk,
        )
        self.assertNotContains(
            response,
            self.hoa_don_dang_hoat_dong.ma_hd,
        )
        self.assertNotContains(
            response,
            self.hoa_don_pt_tiep_theo.ma_hd,
        )
        self.assertContains(
            response,
            "Gói tập của tôi",
        )
        self.assertContains(
            response,
            reverse(
                "gym:chi_tiet_goi_tap_cua_toi",
                args=[
                    self.dang_ky_dang_hoat_dong.ma_dk
                ],
            ),
        )
        self.assertContains(
            response,
            reverse(
                "gym:chi_tiet_goi_tap_cua_toi",
                args=[
                    self.dang_ky_pt_tiep_theo.ma_dk
                ],
            ),
        )
        self.assertContains(
            response,
            "Xem chi tiết",
            count=2,
        )

    def test_khong_hien_thi_dang_ky_cua_hoi_vien_khac(
        self
    ):
        dang_ky_khac, hoa_don_khac = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_khac,
                goi_tap=self.goi_vao_gym,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_goi_tap
        )

        self.assertNotContains(
            response,
            dang_ky_khac.ma_dk,
        )
        self.assertNotContains(
            response,
            hoa_don_khac.ma_hd,
        )
        self.assertNotContains(
            response,
            self.hoi_vien_khac.ho_ten,
        )

    def test_hoi_vien_chua_co_goi_xem_duoc_danh_sach_rong(
        self
    ):
        self.client.force_login(
            self.hoi_vien_khac.tai_khoan
        )

        response = self.client.get(
            self.url_goi_tap
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["cac_dang_ky"]),
            [],
        )
        self.assertContains(
            response,
            "Bạn chưa có đăng ký gói tập nào.",
        )

    def test_vai_tro_khac_khong_duoc_xem_goi_tap_cua_hoi_vien(
        self
    ):
        admin = TaiKhoan.objects.create_user(
            username="admin_thu_xem_goi_cua_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        for tai_khoan in (
            admin,
            self.le_tan.tai_khoan,
            self.huan_luyen_vien.tai_khoan,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)

                response = self.client.get(
                    self.url_goi_tap
                )

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_hoi_vien_xem_chi_tiet_goi_va_thanh_toan(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        url = reverse(
            "gym:chi_tiet_goi_tap_cua_toi",
            args=[
                self.dang_ky_pt_tiep_theo.ma_dk
            ],
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "gym/khu_vuc_hoi_vien/"
                "chi_tiet_goi_tap_cua_toi.html"
            ),
        )

        self.assertEqual(
            response.context["dang_ky"],
            self.dang_ky_pt_tiep_theo,
        )
        self.assertEqual(
            response.context["hoa_don"],
            self.hoa_don_pt_tiep_theo,
        )

        self.assertContains(
            response,
            self.dang_ky_pt_tiep_theo.ma_dk,
        )
        self.assertContains(
            response,
            self.goi_pt_tiep_theo.ten_goi,
        )
        self.assertContains(
            response,
            "Quyền lợi PT",
        )
        self.assertContains(
            response,
            "Thông tin thanh toán",
        )
        self.assertContains(
            response,
            str(
                int(
                    self.hoa_don_pt_tiep_theo
                    .tong_tien
                )
            ),
        )
        self.assertContains(
            response,
            (
                self.hoa_don_pt_tiep_theo
                .get_phuong_thuc_thanh_toan_display()
            ),
        )

        self.assertNotContains(
            response,
            "Hóa đơn",
        )

    def test_hoi_vien_khong_xem_duoc_chi_tiet_goi_cua_nguoi_khac(
        self
    ):
        dang_ky_khac, _ = (
            tao_dang_ky_va_hoa_don(
                hoi_vien=self.hoi_vien_khac,
                goi_tap=self.goi_vao_gym,
                le_tan=self.le_tan,
                ngay_dang_ky=self.hom_nay,
                ngay_bat_dau=self.hom_nay,
                phuong_thuc_thanh_toan=(
                    HoaDon.PhuongThucThanhToan.TIEN_MAT
                ),
            )
        )

        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_goi_tap_cua_toi",
                args=[dang_ky_khac.ma_dk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_ma_dang_ky_khong_ton_tai_tra_404(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            reverse(
                "gym:chi_tiet_goi_tap_cua_toi",
                args=["DK999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_hoi_vien_xem_duoc_lich_pt_cua_minh(
        self
    ):
        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_lich_pt
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "gym/khu_vuc_hoi_vien/"
                "lich_tap_pt_cua_toi.html"
            ),
        )

        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_sap_toi"
                ]
            ),
            self.cac_buoi_pt,
        )
        self.assertEqual(
            response.context["so_buoi_sap_toi"],
            4,
        )

        for buoi_tap in self.cac_buoi_pt:
            self.assertContains(
                response,
                buoi_tap.ma_buoi,
            )

    def test_buoi_hoan_thanh_duoc_dua_vao_lich_su(
        self
    ):
        buoi_tap = self.cac_buoi_pt[0]

        thoi_diem_sau_buoi_tap = (
            timezone.make_aware(
                datetime.combine(
                    buoi_tap.ngay_tap,
                    time(10, 0),
                )
            )
        )

        with patch(
            "gym.services.buoi_tap_pt.timezone.now",
            return_value=thoi_diem_sau_buoi_tap,
        ):
            cap_nhat_ket_qua_buoi_tap_pt(
                buoi_tap=buoi_tap,
                huan_luyen_vien=(
                    self.huan_luyen_vien
                ),
                trang_thai=(
                    BuoiTapPT.TrangThai.HOAN_THANH
                ),
                ghi_chu="Đã hoàn thành buổi PT",
            )

        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_lich_pt
        )

        self.assertNotIn(
            buoi_tap,
            list(
                response.context[
                    "cac_buoi_tap_sap_toi"
                ]
            ),
        )
        self.assertIn(
            buoi_tap,
            list(
                response.context[
                    "cac_buoi_tap_lich_su"
                ]
            ),
        )
        self.assertEqual(
            response.context["so_buoi_hoan_thanh"],
            1,
        )
        self.assertContains(
            response,
            "Đã hoàn thành buổi PT",
        )

    def test_hoi_vien_chua_co_buoi_pt_xem_trang_rong(
        self
    ):
        self.client.force_login(
            self.hoi_vien_khac.tai_khoan
        )

        response = self.client.get(
            self.url_lich_pt
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_sap_toi"
                ]
            ),
            [],
        )
        self.assertEqual(
            list(
                response.context[
                    "cac_buoi_tap_lich_su"
                ]
            ),
            [],
        )
        self.assertContains(
            response,
            "Bạn chưa có buổi tập PT sắp tới.",
        )
        self.assertContains(
            response,
            "Bạn chưa có lịch sử buổi tập PT.",
        )

    def test_vai_tro_khac_khong_duoc_xem_lich_pt_cua_hoi_vien(
        self
    ):
        admin = TaiKhoan.objects.create_user(
            username="admin_thu_xem_lich_pt_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        for tai_khoan in (
            admin,
            self.le_tan.tai_khoan,
            self.huan_luyen_vien.tai_khoan,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)

                response = self.client.get(
                    self.url_lich_pt
                )

                self.assertEqual(
                    response.status_code,
                    403,
                )

    def test_hoi_vien_xem_duoc_lich_su_diem_danh_cua_minh(
        self
    ):
        diem_danh_thu_hai = tao_diem_danh(
            hoi_vien=self.hoi_vien,
            le_tan=self.le_tan,
            ghi_chu="Lần điểm danh thứ hai",
        )

        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_lich_su_diem_danh
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            (
                "gym/khu_vuc_hoi_vien/"
                "lich_su_diem_danh.html"
            ),
        )

        self.assertEqual(
            response.context[
                "tong_so_lan_diem_danh"
            ],
            2,
        )
        self.assertEqual(
            response.context[
                "so_lan_diem_danh_hom_nay"
            ],
            2,
        )

        self.assertContains(
            response,
            self.diem_danh.ma_dd,
        )
        self.assertContains(
            response,
            diem_danh_thu_hai.ma_dd,
        )
        self.assertContains(
            response,
            "Điểm danh để kiểm thử tổng quan",
        )
        self.assertContains(
            response,
            "Lần điểm danh thứ hai",
        )

    def test_khong_hien_thi_diem_danh_cua_hoi_vien_khac(
        self
    ):
        tao_dang_ky_va_hoa_don(
            hoi_vien=self.hoi_vien_khac,
            goi_tap=self.goi_vao_gym,
            le_tan=self.le_tan,
            ngay_dang_ky=self.hom_nay,
            ngay_bat_dau=self.hom_nay,
            phuong_thuc_thanh_toan=(
                HoaDon.PhuongThucThanhToan.TIEN_MAT
            ),
        )

        diem_danh_khac = tao_diem_danh(
            hoi_vien=self.hoi_vien_khac,
            le_tan=self.le_tan,
            ghi_chu=(
                "Điểm danh của Hội viên khác"
            ),
        )

        self.client.force_login(
            self.hoi_vien.tai_khoan
        )

        response = self.client.get(
            self.url_lich_su_diem_danh
        )

        self.assertNotContains(
            response,
            diem_danh_khac.ma_dd,
        )
        self.assertNotContains(
            response,
            "Điểm danh của Hội viên khác",
        )
        self.assertNotContains(
            response,
            self.hoi_vien_khac.ho_ten,
        )

    def test_hoi_vien_chua_diem_danh_xem_duoc_trang_rong(
        self
    ):
        self.client.force_login(
            self.hoi_vien_khac.tai_khoan
        )

        response = self.client.get(
            self.url_lich_su_diem_danh
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(
                response.context[
                    "cac_lan_diem_danh"
                ]
            ),
            [],
        )
        self.assertEqual(
            response.context[
                "tong_so_lan_diem_danh"
            ],
            0,
        )
        self.assertEqual(
            response.context[
                "so_lan_diem_danh_hom_nay"
            ],
            0,
        )
        self.assertIsNone(
            response.context[
                "lan_diem_danh_gan_nhat"
            ]
        )

        self.assertContains(
            response,
            "Bạn chưa có lịch sử điểm danh.",
        )

    def test_vai_tro_khac_khong_duoc_xem_lich_su_diem_danh(
        self
    ):
        admin = TaiKhoan.objects.create_user(
            username=(
                "admin_thu_xem_lich_su_diem_danh"
            ),
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        for tai_khoan in (
            admin,
            self.le_tan.tai_khoan,
            self.huan_luyen_vien.tai_khoan,
        ):
            with self.subTest(
                username=tai_khoan.username
            ):
                self.client.force_login(tai_khoan)

                response = self.client.get(
                    self.url_lich_su_diem_danh
                )

                self.assertEqual(
                    response.status_code,
                    403,
                )