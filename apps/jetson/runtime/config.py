"""Configuration loading for the Jetson runtime."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class JetsonConfig:
    """Resolved runtime configuration."""

    # YAMLから読んだ値を、そのまま使いやすい型に正規化して保持します。
    # Path系の値は load_config() 内で絶対パスへ変換されます。
    robot_id: str
    camera_device: int | str
    camera_width: int
    camera_height: int
    camera_fps: float
    camera_backend: str
    gst_pipeline: str | None
    max_frames: int | None
    duration_sec: float | None
    sequence_name: str
    output_dir: Path
    save_frames: bool
    run_orbslam: bool
    orbslam_root: Path
    pangolin_build: Path
    settings: Path
    vocabulary: Path
    binary: Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_path(value: str | Path, base_dir: Path) -> Path:
    # 設定ファイルでは相対パスを書けるようにし、実行時には絶対パスに直します。
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    return data[key] if key in data else default


def _get_nested(data: dict[str, Any], section: str, key: str, default: Any = None) -> Any:
    value = data.get(section, {})
    if isinstance(value, dict):
        return value.get(key, default)
    return default


def _optional_int(value: Any) -> int | None:
    return None if value is None else int(value)


def _optional_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _camera_device(value: Any) -> int | str:
    # YAMLで "0" と書かれても OpenCV がデバイス番号として扱えるよう int に直します。
    # /dev/video0 や GStreamer文字列のような値は文字列のまま残します。
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return value


def load_config(path: Path) -> JetsonConfig:
    """Load a YAML config and normalize legacy nested keys plus current top-level keys."""

    config_path = path.expanduser().resolve()
    with config_path.open(encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file) or {}

    # このアプリはリポジトリ直下から実行する想定なので、相対パスはrepo_root基準で解決します。
    repo_root = _repo_root()
    base_dir = repo_root

    # 以前の nested 形式も読めるようにしてあります。
    # 例: robot.id / camera.device / logging.output_dir
    robot_id = _get(raw, "robot_id", _get_nested(raw, "robot", "id", "jetson-01"))
    output_dir = _resolve_path(_get(raw, "output_dir", _get_nested(raw, "logging", "output_dir", "results/jetson")), base_dir)
    orbslam_root = _resolve_path(_get(raw, "orbslam_root", "../external-repos/ORB_SLAM3"), base_dir)
    pangolin_build = _resolve_path(_get(raw, "pangolin_build", "../external-repos/Pangolin/build"), base_dir)
    settings = _resolve_path(
        _get(raw, "settings", "configs/orbslam3/iphone_vertical_1080x1920_approx.yaml"),
        base_dir,
    )

    vocabulary = _resolve_path(_get(raw, "vocabulary", orbslam_root / "Vocabulary/ORBvoc.txt"), base_dir)
    binary = _resolve_path(_get(raw, "binary", orbslam_root / "Examples/Monocular/mono_tum"), base_dir)

    return JetsonConfig(
        robot_id=str(robot_id),
        camera_device=_camera_device(_get(raw, "camera_device", _get_nested(raw, "camera", "device", 0))),
        camera_width=int(_get(raw, "camera_width", _get_nested(raw, "camera", "width", 1280))),
        camera_height=int(_get(raw, "camera_height", _get_nested(raw, "camera", "height", 720))),
        camera_fps=float(_get(raw, "camera_fps", _get_nested(raw, "camera", "fps", 30.0))),
        camera_backend=str(_get(raw, "camera_backend", "auto")),
        gst_pipeline=_get(raw, "gst_pipeline"),
        max_frames=_optional_int(_get(raw, "max_frames")),
        duration_sec=_optional_float(_get(raw, "duration_sec")),
        sequence_name=str(_get(raw, "sequence_name", "jetson_live")),
        output_dir=output_dir,
        save_frames=bool(_get(raw, "save_frames", True)),
        run_orbslam=bool(_get(raw, "run_orbslam", False)),
        orbslam_root=orbslam_root,
        pangolin_build=pangolin_build,
        settings=settings,
        vocabulary=vocabulary,
        binary=binary,
    )
