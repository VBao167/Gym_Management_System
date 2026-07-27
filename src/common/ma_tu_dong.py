import re

from django.db import models


def sinh_ma_tiep_theo(model, ten_truong, tien_to):
    """
    Sinh mã theo dạng: <tiền tố><số thứ tự>.

    Ví dụ:
    Goi01 -> Goi02
    HD09 -> HD10

    Những mã không đúng định dạng sẽ bị bỏ qua.
    Ví dụ GOITEST không ảnh hưởng đến dãy Goi01, Goi02...
    """
    mau_ma = re.compile(
        rf"^{re.escape(tien_to)}(\d+)$"
    )
    so_lon_nhat = 0

    cac_ma_hien_co = model.objects.filter(
        **{f"{ten_truong}__startswith": tien_to}
    ).values_list(
        ten_truong,
        flat=True,
    )

    for ma_hien_tai in cac_ma_hien_co:
        ket_qua = mau_ma.fullmatch(ma_hien_tai or "")

        if ket_qua:
            so_lon_nhat = max(
                so_lon_nhat,
                int(ket_qua.group(1)),
            )

    return f"{tien_to}{so_lon_nhat + 1:02d}"


class MaTuDongMixin(models.Model):
    """
    Mixin tự sinh khóa chính nếu bản ghi chưa có mã.
    """

    MA_PREFIX = ""

    class Meta:
        abstract = True

    def gan_ma_tu_dong(self):
        ten_truong_ma = self._meta.pk.attname

        # Bản ghi đã có mã thì giữ nguyên mã.
        if getattr(self, ten_truong_ma):
            return

        if not self.MA_PREFIX:
            raise ValueError(
                f"{type(self).__name__} chưa khai báo MA_PREFIX."
            )

        ma_moi = sinh_ma_tiep_theo(
            model=type(self),
            ten_truong=ten_truong_ma,
            tien_to=self.MA_PREFIX,
        )

        setattr(
            self,
            ten_truong_ma,
            ma_moi,
        )

    def save(self, *args, **kwargs):
        self.gan_ma_tu_dong()
        return super().save(*args, **kwargs)