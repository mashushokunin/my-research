#!/usr/bin/env python3
"""Create plots for pre-SLAM and communication-efficiency experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def sequence_group(sequence: str) -> str:
    return sequence.split("/", 1)[0] if "/" in sequence else "ungrouped"


def save_current(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


def plot_feature_budget(feature_budget_csv: Path, output_dir: Path) -> None:
    if not feature_budget_csv.exists():
        return
    data = pd.read_csv(feature_budget_csv)
    if data.empty:
        return
    data["group"] = data["sequence"].map(sequence_group)
    grouped = (
        data.groupby(["group", "nfeatures"], as_index=False)[
            [
                "avg_good_matches_to_previous",
                "avg_compact_packet_bytes_per_frame",
                "compact_packet_vs_jpeg_ratio",
            ]
        ]
        .mean()
        .sort_values(["group", "nfeatures"])
    )

    plt.figure(figsize=(8, 5))
    for group, group_data in grouped.groupby("group"):
        plt.plot(
            group_data["nfeatures"],
            group_data["avg_good_matches_to_previous"],
            marker="o",
            label=group,
        )
    plt.xlabel("ORB feature budget")
    plt.ylabel("Average good matches to previous frame")
    plt.title("Feature budget vs usable matches")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_current(output_dir / "feature_budget_good_matches.png")

    plt.figure(figsize=(8, 5))
    for group, group_data in grouped.groupby("group"):
        plt.plot(
            group_data["nfeatures"],
            group_data["compact_packet_vs_jpeg_ratio"],
            marker="o",
            label=group,
        )
    plt.xlabel("ORB feature budget")
    plt.ylabel("Feature packet / JPEG size")
    plt.title("Communication ratio against JPEG frames")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_current(output_dir / "feature_budget_communication_ratio.png")


def plot_preslam_geometry(preslam_group_csv: Path, output_dir: Path) -> None:
    if not preslam_group_csv.exists():
        return
    data = pd.read_csv(preslam_group_csv)
    if data.empty:
        return
    if "resize_scale" in data.columns:
        data = data[data["resize_scale"] == data["resize_scale"].max()]
    data = data.sort_values(["group", "frame_step"])

    plt.figure(figsize=(8, 5))
    for group, group_data in data.groupby("group"):
        plt.plot(
            group_data["frame_step"],
            group_data["avg_fundamental_inliers"],
            marker="o",
            label=group,
        )
    plt.xlabel("Frame step")
    plt.ylabel("Average fundamental-matrix RANSAC inliers")
    plt.title("Geometric inliers as frames get farther apart")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_current(output_dir / "preslam_fundamental_inliers_by_frame_step.png")

    plt.figure(figsize=(8, 5))
    for group, group_data in data.groupby("group"):
        plt.plot(
            group_data["frame_step"],
            group_data["avg_good_matches"],
            marker="o",
            label=group,
        )
    plt.xlabel("Frame step")
    plt.ylabel("Average good matches")
    plt.title("Descriptor matches as frames get farther apart")
    plt.grid(True, alpha=0.3)
    plt.legend()
    save_current(output_dir / "preslam_good_matches_by_frame_step.png")


def plot_feature_selection(selection_group_csv: Path, output_dir: Path) -> None:
    if not selection_group_csv.exists():
        return
    data = pd.read_csv(selection_group_csv)
    if data.empty:
        return

    for group, group_data in data.groupby("group"):
        plt.figure(figsize=(8, 5))
        for strategy, strategy_data in group_data.groupby("strategy"):
            strategy_data = strategy_data.sort_values("budget")
            plt.plot(
                strategy_data["budget"],
                strategy_data["avg_fundamental_inliers"],
                marker="o",
                label=strategy,
            )
        plt.xlabel("Transmitted feature budget per frame")
        plt.ylabel("Average fundamental-matrix RANSAC inliers")
        plt.title(f"Feature selection under communication budget: {group}")
        plt.grid(True, alpha=0.3)
        plt.legend()
        save_current(output_dir / f"feature_selection_inliers_{group}.png")

        plt.figure(figsize=(8, 5))
        for strategy, strategy_data in group_data.groupby("strategy"):
            strategy_data = strategy_data.sort_values("budget")
            plt.plot(
                strategy_data["budget"],
                strategy_data["avg_compact_packet_vs_jpeg_ratio"],
                marker="o",
                label=strategy,
            )
        plt.xlabel("Transmitted feature budget per frame")
        plt.ylabel("Feature packet / JPEG size")
        plt.title(f"Communication ratio by selection strategy: {group}")
        plt.grid(True, alpha=0.3)
        plt.legend()
        save_current(output_dir / f"feature_selection_communication_{group}.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--feature-budget-csv", type=Path, default=Path("results/feature_budgets/summary.csv"))
    parser.add_argument("--preslam-group-csv", type=Path, default=Path("results/preslam_geometry/group_summary.csv"))
    parser.add_argument("--selection-group-csv", type=Path, default=Path("results/feature_selection/group_summary.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/figures"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot_feature_budget(args.feature_budget_csv, args.output_dir)
    plot_preslam_geometry(args.preslam_group_csv, args.output_dir)
    plot_feature_selection(args.selection_group_csv, args.output_dir)
    print(f"Wrote plots to {args.output_dir}")


if __name__ == "__main__":
    main()
