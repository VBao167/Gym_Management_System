import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gym", "0005_lichtappt"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="lichtappt",
            name="CK_LichTapPT_GioTap",
        ),
        migrations.RemoveConstraint(
            model_name="lichtappt",
            name="CK_LichTapPT_TrangThai",
        ),

        migrations.RenameModel(
            old_name="LichTapPT",
            new_name="BuoiTapPT",
        ),

        migrations.RenameField(
            model_name="buoitappt",
            old_name="ma_lich",
            new_name="ma_buoi",
        ),

        migrations.AlterField(
            model_name="buoitappt",
            name="ma_buoi",
            field=models.CharField(
                max_length=10,
                primary_key=True,
                serialize=False,
                db_column="MaBuoi",
            ),
        ),

        migrations.AlterField(
            model_name="buoitappt",
            name="dang_ky",
            field=models.ForeignKey(
                to="gym.dangkygoitap",
                on_delete=django.db.models.deletion.PROTECT,
                db_column="MaDK",
                related_name="cac_buoi_tap_pt",
            ),
        ),

        migrations.AlterField(
            model_name="buoitappt",
            name="huan_luyen_vien",
            field=models.ForeignKey(
                to="gym.huanluyenvien",
                on_delete=django.db.models.deletion.PROTECT,
                db_column="MaPT",
                related_name="cac_buoi_tap_pt",
            ),
        ),

        migrations.AlterField(
            model_name="buoitappt",
            name="le_tan",
            field=models.ForeignKey(
                to="gym.letan",
                on_delete=django.db.models.deletion.PROTECT,
                db_column="MaLT",
                related_name="cac_buoi_tap_pt_da_sap_xep",
            ),
        ),

        migrations.AlterModelOptions(
            name="buoitappt",
            options={
                "ordering": (
                    "-ngay_tap",
                    "-gio_bat_dau",
                    "ma_buoi",
                ),
            },
        ),

        migrations.AlterModelTable(
            name="buoitappt",
            table="BuoiTapPT",
        ),

        migrations.AddConstraint(
            model_name="buoitappt",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    gio_ket_thuc__gt=models.F("gio_bat_dau")
                ),
                name="CK_BuoiTapPT_GioTap",
            ),
        ),
        migrations.AddConstraint(
            model_name="buoitappt",
            constraint=models.CheckConstraint(
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
        ),
    ]