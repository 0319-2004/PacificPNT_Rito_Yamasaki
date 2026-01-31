exec(r"""
import processing
from qgis.core import QgsProject

# ========= 設定 =========
BLDG_LAYER_NAME = "bld_2d"      # 建物レイヤ（元は EPSG:6668）
AOI_LAYER_NAME  = "aoi"         # AOI（EPSG:6677）
HEIGHT_FIELD    = "measuredHeight"
PIXEL_SIZE      = 5.0           # ★★ ここだけ 5m にした！ ★★


# ========= レイヤ取得 =========
proj = QgsProject.instance()

bld = proj.mapLayersByName(BLDG_LAYER_NAME)[0]
aoi = proj.mapLayersByName(AOI_LAYER_NAME)[0]

layer_dir = os.path.dirname(bld.source().split("|")[0]) # レイヤのフォルダ特定
repo_root = os.path.abspath(os.path.join(layer_dir, "../../")) # ルート特定
output_dir = os.path.join(repo_root, "experiments", "qgis_output")
os.makedirs(output_dir, exist_ok=True)

OUTPUT_RASTER = os.path.join(output_dir, "bld_height_5m.tif")
print(f"▶ 元建物レイヤ: {BLDG_LAYER_NAME}  EPSG:{bld.crs().postgisSrid()}")
print(f"▶ AOIレイヤ   : {AOI_LAYER_NAME}  EPSG:{aoi.crs().postgisSrid()}")

# ========= 建物レイヤ → AOI の CRS（6677）に合わせる =========
if bld.crs() != aoi.crs():
    print("▶ 建物レイヤを AOI の CRS に再投影します...")
    reproject_params = {
        "INPUT": bld,
        "TARGET_CRS": aoi.crs(),
        "OUTPUT": "memory:bld_6677"
    }
    bld = processing.run("native:reprojectlayer", reproject_params)["OUTPUT"]
    print(f"▶ 使用建物レイヤ: bld_6677 EPSG:{bld.crs().postgisSrid()}")

# ========= AOI から範囲を取得 =========
extent = aoi.extent()
xmin, xmax = extent.xMinimum(), extent.xMaximum()
ymin, ymax = extent.yMinimum(), extent.yMaximum()

print(f"▶ 使う範囲: {xmin},{xmax},{ymin},{ymax} [EPSG:{aoi.crs().postgisSrid()}]")

# ========= 行列数を計算 =========
cols = int((xmax - xmin) / PIXEL_SIZE)
rows = int((ymax - ymin) / PIXEL_SIZE)

print(f"▶ AOIサイズ: {xmax-xmin:.2f}m × {ymax-ymin:.2f}m")
print(f"▶ ピクセル数: {cols} 列 × {rows} 行（解像度={PIXEL_SIZE}m）")

# ========= ラスタ化実行 =========
params = {
    "INPUT": bld,
    "FIELD": HEIGHT_FIELD,
    "UNITS": 1,  # georeferenced units
    "WIDTH": PIXEL_SIZE,
    "HEIGHT": PIXEL_SIZE,
    "EXTENT": f"{xmin},{xmax},{ymin},{ymax} [{aoi.crs().authid()}]",
    "NODATA": -9999,
    "DATA_TYPE": 5,  # Float32
    "OUTPUT": OUTPUT_RASTER
}

print("▶ ラスタ化を実行中...")
result = processing.run("gdal:rasterize", params)

print("✅ 完了: 5mラスタを追加しました")
print(f"   パス: {OUTPUT_RASTER}")

iface.addRasterLayer(OUTPUT_RASTER, "bld_height_5m")
""")
