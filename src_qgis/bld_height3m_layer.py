exec(r"""
from qgis.core import QgsProject, QgsRasterLayer
import processing
import math

# ===== 設定（レイヤ名は今のプロジェクトに合わせて） =====
SRC_BUILDING_LAYER_NAME = "bld_2d"   # 元の建物（EPSG:6668）
AOI_LAYER_NAME          = "aoi"      # 元の AOI（EPSG:6677）
CELL_SIZE               = 3.0        # m

# 1. 現在のプロジェクトフォルダ（.../data_qgis/raw）を取得
current_dir = QgsProject.instance().homePath()

# 2. 【重要】そこから2階層上がってルートディレクトリ（PacificPNT_GitHub）を特定
#    "../../" は「親の親」という意味です
root_dir = os.path.abspath(os.path.join(current_dir, "../../"))

# 3. ルート配下の experiments/qgis_output を指定
output_dir = os.path.join(root_dir, "experiments", "qgis_output")

# 4. フォルダ作成 & パス結合
os.makedirs(output_dir, exist_ok=True)
OUTPUT_PATH = os.path.join(output_dir, "bld_height_3m.tif")

RASTER_LAYER_NAME = "bld_height_3m"
print(f"Project Location: {current_dir}")
print(f"Output will be saved to: {OUTPUT_PATH}")
# ========================================================

proj = QgsProject.instance()

def get_layer(name):
    lst = proj.mapLayersByName(name)
    if not lst:
        raise RuntimeError(f"レイヤ '{name}' が見つかりません")
    return lst[0]

try:
    # --- レイヤ取得 ---
    bld_src = get_layer(SRC_BUILDING_LAYER_NAME)
    aoi = get_layer(AOI_LAYER_NAME)

    print("▶ 元建物レイヤ:", bld_src.name(), bld_src.crs().authid())
    print("▶ AOIレイヤ   :", aoi.name(), aoi.crs().authid())

    # --- 建物レイヤを AOI の CRS に再投影 ---
    if bld_src.crs() != aoi.crs():
        print("▶ 建物レイヤを AOI の CRS に再投影します...")
        reproj = processing.run(
            "native:reprojectlayer",
            {
                "INPUT": bld_src,
                "TARGET_CRS": aoi.crs(),
                "OUTPUT": "memory:bld_2d_6677"
            }
        )
        bld = reproj["OUTPUT"]
    else:
        print("▶ 既に同じ CRS なので、そのまま使います")
        bld = bld_src

    print("▶ 使用建物レイヤ:", bld.name(), bld.crs().authid())

    # --- AOI の範囲（メートル系） ---
    ext = aoi.extent()
    xmin, xmax = ext.xMinimum(), ext.xMaximum()
    ymin, ymax = ext.yMinimum(), ext.yMaximum()
    crs_auth = aoi.crs().authid()

    extent_str = f"{xmin},{xmax},{ymin},{ymax} [{crs_auth}]"
    print("▶ 使う範囲:", extent_str)

    # --- ピクセル数を計算（メートル単位） ---
    width_m  = xmax - xmin
    height_m = ymax - ymin

    cols = max(1, int(math.ceil(width_m  / CELL_SIZE)))
    rows = max(1, int(math.ceil(height_m / CELL_SIZE)))

    print(f"▶ AOIサイズ: {width_m:.2f}m × {height_m:.2f}m")
    print(f"▶ ピクセル数: {cols} 列 × {rows} 行 （理論セルサイズ≒{width_m/cols:.2f}m）")

    # --- 既存の同名ラスタを削除（あれば） ---
    for lid, lyr in list(proj.mapLayers().items()):
        if lyr.name() == RASTER_LAYER_NAME and isinstance(lyr, QgsRasterLayer):
            proj.removeMapLayer(lid)

    params = {
        "INPUT": bld,
        "FIELD": "measuredHeight",
        "BURN": 0,
        "USE_Z": False,
        "UNITS": 0,           # 0 = ピクセル数指定
        "WIDTH": cols,        # ピクセル数
        "HEIGHT": rows,       # ピクセル数
        "EXTENT": extent_str,
        "NODATA": -9999.0,
        "DATA_TYPE": 5,       # Float32
        "INIT": None,
        "INVERT": False,
        "OPTIONS": "",
        "EXTRA": "",
        "OUTPUT": OUTPUT_PATH,
    }

    print("▶ ラスタ化を実行中...")
    result = processing.run("gdal:rasterize", params)

    out_path = str(result["OUTPUT"])
    rast = QgsRasterLayer(out_path, RASTER_LAYER_NAME)

    if rast.isValid():
        proj.addMapLayer(rast)
        print("✅ 完了: ラスタを追加しました")
        print("   パス:", out_path)
    else:
        print("⚠ ラスタが無効です。出力パス:", out_path)

except Exception as e:
    print("❌ エラーが発生しました:", e)
""")
