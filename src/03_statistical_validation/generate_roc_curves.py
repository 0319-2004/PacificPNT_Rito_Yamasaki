import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from sklearn.metrics import roc_curve, auc
except ImportError as e:
    raise SystemExit(
        "scikit-learn is required to generate ROC curves (pip install scikit-learn)."
    ) from e


def compute_roc(y_true, scores, flip=False):
    """Return fpr, tpr, auc_value. If flip=True, multiply scores by -1."""
    s = -scores if flip else scores
    fpr, tpr, _ = roc_curve(y_true, s)
    return fpr, tpr, auc(fpr, tpr)


def main():
    parser = argparse.ArgumentParser(
        description="Generate overlaid ROC curves from phase2_final_merged.csv"
    )
    parser.add_argument(
        "--csv",
        default="phase2_final_merged.csv",
        help="Input CSV (default: phase2_final_merged.csv)",
    )
    parser.add_argument(
        "--out",
        default="roc_curves_all.png",
        help="Output image filename (default: roc_curves_all.png)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="High-risk threshold on err_p95_m (default: 5.0; label is err_p95_m > threshold)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)

    # Ground-truth label (matches the common setup in this project where many low-risk sites are at 5.0m)
    if "err_p95_m" not in df.columns:
        raise SystemExit("err_p95_m column not found in the CSV.")
    y = (df["err_p95_m"].astype(float) > float(args.threshold)).astype(int).values

    # Scores to plot (edit here if you want to add/remove curves)
    curves = []

    # Phase 1 (building-only)
    if "risk_horizon" in df.columns:
        curves.append(("Phase 1 (risk_horizon)", df["risk_horizon"].astype(float).values, False))

    # Phase 2 (hybrid override)
    if "overhead_flag" in df.columns and "risk_horizon" in df.columns:
        hybrid = np.where(df["overhead_flag"].astype(int).values == 1, 1.0, df["risk_horizon"].astype(float).values)
        curves.append(("Phase 2 (hybrid override)", hybrid, False))

    # Phase 2 combined proxy (if available)
    if "risk_proxy_5m" in df.columns:
        curves.append(("risk_proxy_5m", df["risk_proxy_5m"].astype(float).values, False))

    # SVF proxy (in this dataset SVF behaves like an inverse-risk proxy)
    if "svf_proxy_5m" in df.columns:
        curves.append(("svf_proxy_5m", df["svf_proxy_5m"].astype(float).values, True))

    # HDOP (lower is better => flip)
    if "hdop_cut_a_median" in df.columns:
        curves.append(("HDOP (hdop_cut_a_median)", df["hdop_cut_a_median"].astype(float).values, True))

    if len(curves) == 0:
        raise SystemExit("No known score columns found to plot.")

    plt.figure(figsize=(6.5, 5.0))

    for name, score, flip in curves:
        fpr, tpr, aucv = compute_roc(y, score, flip=flip)
        plt.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC={aucv:.3f})")

    plt.plot([0, 1], [0, 1], "k--", linewidth=1, label="Chance")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC curves (overlaid)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(args.out, dpi=300)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()
