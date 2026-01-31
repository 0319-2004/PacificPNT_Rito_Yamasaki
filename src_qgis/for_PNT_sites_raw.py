exec("""
from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsField,
    edit
)
from qgis.PyQt.QtCore import QVariant
import math

# ==== レイヤ名（必要なら自分の環境に合わせて変更）====
POINTS_NAME = 'PNT_sites_raw'
RISK_NAME   = 'risk_proxy_5m'
SVF_NAME    = 'svf_proxy_5m'

# ==== しきい値（既に計算済みの q30 / q70 をそのまま使用）====
Q30 = 0.07203729078173637
Q70 = 0.2442609965801239

proj = QgsProject.instance()

pts_list  = proj.mapLayersByName(POINTS_NAME)
risk_list = proj.mapLayersByName(RISK_NAME)
svf_list  = proj.mapLayersByName(SVF_NAME)

if not pts_list:
    raise RuntimeError(f\"points layer '{POINTS_NAME}' not found\")
if not risk_list:
    raise RuntimeError(f\"risk raster '{RISK_NAME}' not found\")
if not svf_list:
    raise RuntimeError(f\"svf raster '{SVF_NAME}' not found\")

pts_layer  = pts_list[0]
risk_layer = risk_list[0]
svf_layer  = svf_list[0]

print(f\"[OK] points : {pts_layer.name()} ({pts_layer.crs().authid()})\")
print(f\"[OK] risk   : {risk_layer.name()} ({risk_layer.crs().authid()})\")
print(f\"[OK] svf    : {svf_layer.name()} ({svf_layer.crs().authid()})\")

# ==== フィールドを用意（無ければ追加）====
prov = pts_layer.dataProvider()
fields = prov.fields()
names = [f.name() for f in fields]

to_add = []
if 'risk_raw' not in names:
    to_add.append(QgsField('risk_raw', QVariant.Double))
if 'svf_raw' not in names:
    to_add.append(QgsField('svf_raw', QVariant.Double))
if 'risk_class_pre' not in names:
    to_add.append(QgsField('risk_class_pre', QVariant.Int))
if 'risk_class_use' not in names:
    to_add.append(QgsField('risk_class_use', QVariant.Int))

if to_add:
    prov.addAttributes(to_add)
    pts_layer.updateFields()
    print('[+] added fields:', [f.name() for f in to_add])

# インデックスを取り直し
fields = pts_layer.fields()
idx_risk   = fields.indexFromName('risk_raw')
idx_svf    = fields.indexFromName('svf_raw')
idx_class  = fields.indexFromName('risk_class_pre')
idx_use    = fields.indexFromName('risk_class_use')  # まだ値は入れない

# ==== 座標変換（必要なら）====
crs_pts  = pts_layer.crs()
crs_risk = risk_layer.crs()
crs_svf  = svf_layer.crs()

if crs_pts != crs_risk:
    tr_risk = QgsCoordinateTransform(crs_pts, crs_risk, proj)
    print('[INFO] points -> risk CRS transform enabled')
else:
    tr_risk = None

if crs_pts != crs_svf:
    tr_svf = QgsCoordinateTransform(crs_pts, crs_svf, proj)
    print('[INFO] points -> svf CRS transform enabled')
else:
    tr_svf = None

risk_dp = risk_layer.dataProvider()
svf_dp  = svf_layer.dataProvider()

def sample(dp, pt, band=1):
    val, ok = dp.sample(pt, band)
    if (not ok) or val is None:
        return None
    try:
        v = float(val)
    except Exception:
        return None
    if math.isnan(v):
        return None
    return v

n_total = 0
n_valid_risk = 0
class_counts = {1:0, 2:0, 3:0}

with edit(pts_layer):
    for f in pts_layer.getFeatures():
        n_total += 1
        geom = f.geometry()
        if geom.isEmpty():
            continue
        pt = geom.asPoint()

        # risk 用座標
        pt_risk = pt
        if tr_risk is not None:
            pt_risk = tr_risk.transform(pt)

        # svf 用座標
        pt_svf = pt
        if tr_svf is not None:
            pt_svf = tr_svf.transform(pt)

        v_risk = sample(risk_dp, pt_risk, 1)
        v_svf  = sample(svf_dp,  pt_svf,  1)

        attrs = {}

        if v_risk is not None:
            attrs[idx_risk] = v_risk
            n_valid_risk += 1

            # ==== しきい値でクラス分け ====
            if v_risk <= Q30:
                cls = 1
            elif v_risk < Q70:
                cls = 2
            else:
                cls = 3
            attrs[idx_class] = cls
            class_counts[cls] += 1

        if v_svf is not None:
            attrs[idx_svf] = v_svf

        if attrs:
            f.setAttributes([attrs.get(i, f[i]) for i in range(len(fields))])
            pts_layer.updateFeature(f)

print(f\"[✓] updated {n_valid_risk} / {n_total} points with risk/svf\")
print('[✓] class counts (1=open,2=street,3=alley):', class_counts)
print('    risk_class_use フィールドは追加済み（値はまだNULLのまま）')
""")
