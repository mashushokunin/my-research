"""OpenCV camera capture wrapper for Jetson runtime."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterator

import cv2


@dataclass(frozen=True)
class CameraFrame:
    """One frame captured from the camera."""

    # image は OpenCV が返す BGR形式の numpy 配列です。
    image: object
    # 起動後に何枚目として取得したかを表す連番です。
    frame_index: int
    # time.monotonic() を基準にした、キャプチャ開始からの経過秒です。
    timestamp_sec: float


class OpenCVCamera:
    """Open a Jetson camera through OpenCV and yield timestamped frames."""

    def __init__(
        self,
        device: int | str,
        width: int,
        height: int,
        fps: float,
        backend: str = "auto",
        gst_pipeline: str | None = None,
    ) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.backend = backend
        self.gst_pipeline = gst_pipeline
        self._capture: cv2.VideoCapture | None = None
        self._start_time: float | None = None
        self._frame_index = 0

    def open(self) -> None:
        """Open the configured camera and apply basic capture properties."""

        # 通常のUSBカメラは device=0 のような番号で開きます。
        # CSIカメラなどでGStreamerが必要な場合は gst_pipeline をそのままVideoCaptureへ渡します。
        source: int | str = self.device
        api_preference = cv2.CAP_ANY
        if self.gst_pipeline:
            source = self.gst_pipeline
            api_preference = cv2.CAP_GSTREAMER
        elif self.backend == "v4l2":
            api_preference = cv2.CAP_V4L2
        elif self.backend == "gstreamer":
            api_preference = cv2.CAP_GSTREAMER

        capture = cv2.VideoCapture(source, api_preference)
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open camera source: {source}")

        # カメラ側が必ず指定値を受け入れるとは限りませんが、ここで希望解像度/FPSを伝えます。
        # 実機確認時は、必要に応じて capture.get(...) で実際の値を確認します。
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        capture.set(cv2.CAP_PROP_FPS, self.fps)

        self._capture = capture
        self._start_time = time.monotonic()
        self._frame_index = 0

    def close(self) -> None:
        """Release the OpenCV capture device."""

        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def frames(self, max_frames: int | None = None, duration_sec: float | None = None) -> Iterator[CameraFrame]:
        """Yield frames until max_frames, duration_sec, or camera failure stops capture."""

        if self._capture is None:
            self.open()

        assert self._capture is not None
        assert self._start_time is not None

        while True:
            # フレーム数または経過時間で停止できるようにして、短時間の動作確認をしやすくしています。
            elapsed_sec = time.monotonic() - self._start_time
            if max_frames is not None and self._frame_index >= max_frames:
                break
            if duration_sec is not None and elapsed_sec >= duration_sec:
                break

            # OpenCVから1枚取得します。失敗した場合は、壊れた画像を保存せず明示的に止めます。
            ok, image = self._capture.read()
            if not ok:
                raise RuntimeError("Failed to read frame from camera")

            yield CameraFrame(
                image=image,
                frame_index=self._frame_index,
                timestamp_sec=elapsed_sec,
            )
            self._frame_index += 1

    def __enter__(self) -> "OpenCVCamera":
        self.open()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
