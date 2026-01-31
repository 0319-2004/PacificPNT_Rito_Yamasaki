import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.utils import resample
import warnings
warnings.filterwarnings("ignore")

# ==========================================
# 設定 (pipeline_analysis2.py と完全同期)
# ==========================================

# 1. ルートディレクトリの取得
#    src/03_statistical_validation/script.py -> parent(03) -> parent(src) -> parent(Root)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent

# 2. 入力データのパス設定
#    Phase 2 (step2_2) の出力結果があるフォルダを指定
#    (experiments/analysis_output/phase2_evaluate/merged_analysis2_final.csv)
INPUT_DIR = PROJECT_ROOT / 'experiments' / 'analysis_output' / 'phase2_evaluate'
DATA_FILE = INPUT_DIR / "merged_analysis2_final.csv"

# 3. 検証結果の出力先 (experiments/analysis_output/phase3_validation)
#    ※ 検証結果も隔離して保存します
OUTPUT_DIR = PROJECT_ROOT / 'experiments' / 'analysis_output' / 'phase3_validation'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
print(f"▶ Input Data : {DATA_FILE}")
print(f"▶ Output Dir : {OUTPUT_DIR}")

HIGH_ERROR_QUANTILE = 0.70
N_BOOTSTRAP = 1000

# 評価対象のモデル定義 (pipeline_analysis2.py の MODELS と同じ順序・構成)
MODELS = {
    "Phase2 (Combined)": "risk_proxy_5m",
    "Phase2 (Horizon)":  "risk_horizon",
    "Phase2 (Overhead)": "overhead_score",
    "Benchmark (HDOP)":  "hdop_cut_a_median"
}

# 順位を確認する重要地点
FOCUS_SITES = ["A11", "A06"]

# ---------------------------------------------------------
# 評価ロジック (pipeline_analysis2.py から移植)
# ---------------------------------------------------------
def calculate_safety_metrics(df, y_col, score_col, model_name):
    # 欠損値除去
    temp = df[[y_col, score_col, 'site_id', 'err_p95_m']].dropna()
    y = temp[y_col].values
    s = temp[score_col].values
    
    if len(np.unique(y)) < 2: return None

    # AUC計算
    auc_raw = roc_auc_score(y, s)
    
    # 反転ロジック (AUC < 0.5 なら反転)
    flipped = False
    if auc_raw < 0.5:
        auc_final = 1.0 - auc_raw
        s_used = -s # スコアの向きも反転 (低いほど危険)
        flipped = True
    else:
        auc_final = auc_raw
        s_used = s  # そのまま (高いほど危険)
        flipped = False

    # 結果辞書の作成
    res = {
        "Model": model_name,
        "Score": score_col,
        "AUC": auc_final,
        "Flipped": flipped
    }
    
    # ランク計算 (s_used が大きい順 = 危険な順)
    temp['_score_used'] = s_used
    temp_sorted = temp.sort_values('_score_used', ascending=False).reset_index(drop=True)
    
    for site in FOCUS_SITES:
        try:
            rank = temp_sorted[temp_sorted['site_id'] == site].index[0] + 1
            res[f"Rank({site})"] = rank
        except:
            res[f"Rank({site})"] = "-"
            
    return res

# ---------------------------------------------------------
# メイン処理
# ---------------------------------------------------------
def main():
    print("--- Bootstrap Analysis (All Models) ---")
    
    # 1. データ読み込み
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: {DATA_FILE} not found.")
        return

    # 正解ラベル作成 (Top 30% Error)
    thr_orig = df['err_p95_m'].quantile(HIGH_ERROR_QUANTILE)
    df['high_error'] = (df['err_p95_m'] >= thr_orig).astype(int)
    print(f"[*] Loaded {len(df)} sites. High Error Threshold: {thr_orig:.2f}m")

    # 2. オリジナルデータの評価 (全モデルループ)
    print("\n[Original Results (Matching pipeline_analysis2.py)]")
    
    # テーブルヘッダー出力
    header = f"| {'Model':<18} | {'Score':<18} | {'AUC':>8} | {'Flipped':<7} | {'Rank(A11)':>9} | {'Rank(A06)':>9} |"
    print("-" * len(header))
    print(header)
    print("-" * len(header))

    original_results = {}

    for name, col in MODELS.items():
        res = calculate_safety_metrics(df, 'high_error', col, name)
        if res:
            original_results[name] = res['AUC'] # ブートストラップ比較用に保存
            print(f"| {name:<18} | {col:<18} | {res['AUC']:0.6f} | {str(res['Flipped']):<7} | {res['Rank(A11)']:>9} | {res['Rank(A06)']:>9} |")
    print("-" * len(header))

    # 3. Bootstrap 実行 (Phase2 各モデル vs HDOP)
    print(f"\n[Running Bootstrap n={N_BOOTSTRAP} ...]")
    
    # 差分を格納する辞書 (Proposed - Benchmark)
    diffs = {
        "Phase2 (Combined)": [],
        "Phase2 (Horizon)": [],
        "Phase2 (Overhead)": []
    }
    
    for i in range(N_BOOTSTRAP):
        boot = resample(df, random_state=i)
        
        # 閾値再計算
        thr_boot = boot['err_p95_m'].quantile(HIGH_ERROR_QUANTILE)
        boot['high_error'] = (boot['err_p95_m'] >= thr_boot).astype(int)
        
        if len(boot['high_error'].unique()) < 2: continue

        # Benchmark (HDOP) の計算
        res_hdop = calculate_safety_metrics(boot, 'high_error', MODELS["Benchmark (HDOP)"], "Benchmark (HDOP)")
        if not res_hdop: continue
        auc_hdop = res_hdop['AUC']
        
        # Proposed 各モデルの計算と差分記録
        for name in diffs.keys():
            res_prop = calculate_safety_metrics(boot, 'high_error', MODELS[name], name)
            if res_prop:
                diffs[name].append(res_prop['AUC'] - auc_hdop)

    # 4. 統計検定結果の出力
    print("\n=== Final Statistical Results (p-value: Proposed > HDOP) ===")
    
    for name, diff_list in diffs.items():
        if len(diff_list) == 0:
            print(f"{name}: No valid bootstrap samples.")
            continue
            
        # p-value: 差分が0以下の割合
        p_val = np.mean([d <= 0 for d in diff_list])
        
        # オリジナルの差分
        orig_diff = original_results.get(name, 0) - original_results.get("Benchmark (HDOP)", 0)
        
        sig_mark = "✅" if p_val < 0.05 else " "
        print(f"{name:<18} | Diff: {orig_diff:+.4f} | p-value: {p_val:.4f} {sig_mark}")

if __name__ == "__main__":
    main()