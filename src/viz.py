import csv, collections
from pathlib import Path
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[1]
RES_CSV = BASE / "evals" / "results.csv"
OUT_IMG = BASE / "images" / "coverage_heatmap.png"

def load():
    rows = []
    with RES_CSV.open() as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    return rows

def main():
    rows = load()
    # Build matrix: attack x label counts
    attacks = sorted({r["attack"] for r in rows})
    # Dynamically derive labels so we don't miss new ones like coercion_attempt
    labels = sorted({r["label"] for r in rows})
    if "safe" in labels:
        labels = ["safe"] + [l for l in labels if l != "safe"]
    label_index = {lbl: i for i, lbl in enumerate(labels)}
    mat = [[0 for _ in labels] for _ in attacks]
    for r in rows:
        ai = attacks.index(r["attack"])
        li = label_index.get(r["label"], label_index.get("safe", 0))
        mat[ai][li] += 1

    # Plot heatmap-like with imshow
    fig = plt.figure(figsize=(6, 4))
    plt.imshow(mat, aspect='auto')
    plt.xticks(range(len(labels)), labels, rotation=30)
    plt.yticks(range(len(attacks)), attacks)
    for i in range(len(attacks)):
        for j in range(len(labels)):
            plt.text(j, i, str(mat[i][j]), ha='center', va='center')
    plt.title("Results by attack type")
    plt.colorbar()
    fig.tight_layout()
    fig.savefig(OUT_IMG, dpi=180)
    print("Saved", OUT_IMG)

if __name__ == "__main__":
    main()
