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
    HuanLuyenVien,
    LeTan,
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


class DanhSachHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_danh_sach_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân xem danh sách hội viên",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 3, 3),
            sdt="0951000003",
            email="le.tan.danh.sach@example.com",
            dia_chi="TP.HCM",
        )
        self.tai_khoan_le_tan_khong_co_ho_so = (
            TaiKhoan.objects.create_user(
                username="le_tan_khong_co_ho_so",
                password="1",
                vai_tro=TaiKhoan.VaiTro.LE_TAN,
            )
        )
        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_xem_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
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
            "gym/hoi_vien/danh_sach_hoi_vien.html",
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

    def test_le_tan_xem_duoc_danh_sach_hoi_vien(self):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nguyễn Văn An")
        self.assertContains(response, "Trần Thị Bình")
        self.assertContains(response, "Thêm hội viên")

    def test_le_tan_khong_co_ho_so_bi_tu_choi(self):
        self.client.force_login(
            self.tai_khoan_le_tan_khong_co_ho_so
        )

        response = self.client.get(
            reverse("gym:danh_sach_hoi_vien")
        )

        self.assertEqual(response.status_code, 403)

    def test_pt_khong_duoc_xem_danh_sach_hoi_vien(self):
        self.client.force_login(
            self.tai_khoan_pt
        )

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

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân tạo hội viên",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 2, 2),
            sdt="0961000002",
            email="le.tan.tao.hoi.vien@example.com",
            dia_chi="TP.HCM",
        )

        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_tao_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
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

    def test_le_tan_tao_hoi_vien_kem_tai_khoan_thanh_cong(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

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
        self.assertEqual(
            hoi_vien.tai_khoan.vai_tro,
            TaiKhoan.VaiTro.HOI_VIEN,
        )
        self.assertTrue(
            hoi_vien.tai_khoan.is_active
        )

    def test_le_tan_ngung_lam_viec_khong_duoc_tao_hoi_vien(
        self
    ):
        self.le_tan.trang_thai = False
        self.le_tan.save(
            update_fields=["trang_thai"],
        )
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(HoiVien.objects.count(), 0)

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
            "gym/hoi_vien/tao_hoi_vien.html",
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

    def test_pt_khong_duoc_tao_hoi_vien(self):
        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)


class ChiTietHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_chi_tiet_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân xem chi tiết hội viên",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 3, 3),
            sdt="0961000003",
            email="le.tan.chi.tiet@example.com",
            dia_chi="TP.HCM",
        )

        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_xem_chi_tiet_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Nguyễn Minh Khang",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0961000001",
            email="minh.khang.chi.tiet@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:chi_tiet_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

    def test_admin_xem_duoc_chi_tiet_hoi_vien(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/hoi_vien/chi_tiet_hoi_vien.html",
        )
        self.assertEqual(
            response.context["hoi_vien"],
            self.hoi_vien,
        )

        self.assertContains(response, "Nguyễn Minh Khang")
        self.assertContains(response, self.hoi_vien.ma_hv)
        self.assertContains(
            response,
            self.hoi_vien.tai_khoan.username,
        )
        self.assertContains(
            response,
            "Khóa tài khoản",
        )

    def test_chi_tiet_dong_bo_trang_thai_truoc_khi_hien_thi(self):
        self.client.force_login(self.admin)

        with patch(
            "gym.views.cap_nhat_trang_thai_toan_bo"
        ) as ham_dong_bo:
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        ham_dong_bo.assert_called_once_with()

    def test_ma_hoi_vien_khong_ton_tai_tra_ve_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=["HV999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_pt_khong_duoc_xem_chi_tiet_hoi_vien(
        self
    ):
        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_le_tan_xem_duoc_chi_tiet_nhung_khong_duoc_khoa(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Nguyễn Minh Khang",
        )
        self.assertContains(
            response,
            "Chỉnh sửa",
        )
        self.assertNotContains(
            response,
            "Khóa tài khoản",
        )
        self.assertNotContains(
            response,
            "Mở khóa tài khoản",
        )


class ChinhSuaHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_chinh_sua_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = tao_le_tan(
            ho_ten="Lễ tân chỉnh sửa hội viên",
            gioi_tinh="Nữ",
            ngay_sinh=date(2000, 4, 4),
            sdt="0962000002",
            email="le.tan.chinh.sua@example.com",
            dia_chi="TP.HCM",
        )

        self.tai_khoan_pt = TaiKhoan.objects.create_user(
            username="pt_khong_duoc_chinh_sua_hoi_vien",
            password="1",
            vai_tro=TaiKhoan.VaiTro.PT,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Nguyễn Minh Khang",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0962000001",
            email="minh.khang.chinh.sua@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:chinh_sua_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

        self.du_lieu_cap_nhat = {
            "ho_ten": "Nguyễn Minh Khang",
            "gioi_tinh": "Nam",
            "ngay_sinh": "2002-01-01",
            "sdt": "0962000010",
            "email": "minh.khang.chinh.sua@example.com",
            "dia_chi": "Bình Chánh, TP.HCM",
        }

    def test_admin_xem_duoc_form_chinh_sua(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "gym/hoi_vien/tao_hoi_vien.html",
        )
        self.assertEqual(
            response.context["form"].instance,
            self.hoi_vien,
        )
        self.assertContains(
            response,
            "Cập nhật thông tin hội viên",
        )

    def test_admin_chinh_sua_hoi_vien_thanh_cong(self):
        self.client.force_login(self.admin)

        ma_hv_ban_dau = self.hoi_vien.ma_hv
        ma_tk_ban_dau = self.hoi_vien.tai_khoan_id
        username_ban_dau = self.hoi_vien.tai_khoan.username
        trang_thai_ban_dau = self.hoi_vien.trang_thai

        response = self.client.post(
            self.url,
            self.du_lieu_cap_nhat,
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[ma_hv_ban_dau],
            ),
        )

        self.hoi_vien.refresh_from_db()
        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertEqual(
            self.hoi_vien.sdt,
            "0962000010",
        )
        self.assertEqual(
            self.hoi_vien.dia_chi,
            "Bình Chánh, TP.HCM",
        )

        self.assertEqual(
            self.hoi_vien.ma_hv,
            ma_hv_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan_id,
            ma_tk_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan.username,
            username_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.trang_thai,
            trang_thai_ban_dau,
        )

    def test_du_lieu_khong_hop_le_khong_duoc_cap_nhat(self):
        self.client.force_login(self.admin)

        du_lieu_loi = self.du_lieu_cap_nhat.copy()
        du_lieu_loi["email"] = "email-khong-hop-le"

        response = self.client.post(
            self.url,
            du_lieu_loi,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "email",
            response.context["form"].errors,
        )

        self.hoi_vien.refresh_from_db()

        self.assertEqual(
            self.hoi_vien.sdt,
            "0962000001",
        )
        self.assertEqual(
            self.hoi_vien.dia_chi,
            "TP.HCM",
        )

    def test_ma_hoi_vien_khong_ton_tai_tra_ve_404(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                "gym:chinh_sua_hoi_vien",
                args=["HV999999"],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_pt_khong_duoc_chinh_sua_hoi_vien(
        self
    ):
        self.client.force_login(
            self.tai_khoan_pt
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_le_tan_chinh_sua_hoi_vien_thanh_cong(
        self
    ):
        self.client.force_login(
            self.le_tan.tai_khoan
        )

        ma_hv_ban_dau = self.hoi_vien.ma_hv
        ma_tk_ban_dau = self.hoi_vien.tai_khoan_id
        username_ban_dau = (
            self.hoi_vien.tai_khoan.username
        )
        trang_thai_ban_dau = (
            self.hoi_vien.trang_thai
        )

        response = self.client.post(
            self.url,
            self.du_lieu_cap_nhat,
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[ma_hv_ban_dau],
            ),
        )

        self.hoi_vien.refresh_from_db()
        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertEqual(
            self.hoi_vien.sdt,
            "0962000010",
        )
        self.assertEqual(
            self.hoi_vien.dia_chi,
            "Bình Chánh, TP.HCM",
        )
        self.assertEqual(
            self.hoi_vien.ma_hv,
            ma_hv_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan_id,
            ma_tk_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.tai_khoan.username,
            username_ban_dau,
        )
        self.assertEqual(
            self.hoi_vien.trang_thai,
            trang_thai_ban_dau,
        )


class TrangThaiTaiKhoanHoiVienTests(TestCase):
    def setUp(self):
        self.admin = TaiKhoan.objects.create_user(
            username="admin_trang_thai_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.ADMIN,
        )

        self.le_tan = TaiKhoan.objects.create_user(
            username="le_tan_khong_duoc_khoa_tai_khoan",
            password="1",
            vai_tro=TaiKhoan.VaiTro.LE_TAN,
        )

        self.hoi_vien = tao_hoi_vien(
            ho_ten="Hội viên kiểm thử tài khoản",
            gioi_tinh="Nam",
            ngay_sinh=date(2002, 1, 1),
            sdt="0971000001",
            email="tai.khoan.hoi.vien@example.com",
            dia_chi="TP.HCM",
        )

        self.url = reverse(
            "gym:doi_trang_thai_tai_khoan_hoi_vien",
            args=[self.hoi_vien.ma_hv],
        )

    def test_admin_khoa_tai_khoan_hoi_vien(self):
        self.client.force_login(self.admin)

        trang_thai_hoi_vien_ban_dau = (
            self.hoi_vien.trang_thai
        )

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[self.hoi_vien.ma_hv],
            ),
        )

        self.hoi_vien.refresh_from_db()
        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertFalse(
            self.hoi_vien.tai_khoan.is_active
        )
        self.assertEqual(
            self.hoi_vien.trang_thai,
            trang_thai_hoi_vien_ban_dau,
        )

    def test_admin_mo_khoa_tai_khoan_hoi_vien(self):
        self.hoi_vien.tai_khoan.is_active = False
        self.hoi_vien.tai_khoan.save(
            update_fields=["is_active"],
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "mo_khoa",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "gym:chi_tiet_hoi_vien",
                args=[self.hoi_vien.ma_hv],
            ),
        )

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_hanh_dong_khong_hop_le_bi_tu_choi(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "xoa",
            },
        )

        self.assertEqual(response.status_code, 400)

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_get_khong_duoc_dung_de_thay_doi_trang_thai(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

        self.hoi_vien.tai_khoan.refresh_from_db()

        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )

    def test_tai_khoan_khong_phai_admin_bi_tu_choi(
        self
    ):
        self.client.force_login(self.le_tan)

        response = self.client.post(
            self.url,
            {
                "hanh_dong": "khoa",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.hoi_vien.tai_khoan.refresh_from_db()
        self.assertTrue(
            self.hoi_vien.tai_khoan.is_active
        )
