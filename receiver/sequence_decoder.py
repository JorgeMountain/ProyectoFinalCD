"""Decode and assemble multi-frame packet transmissions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import ImageGrab

from common.ecc import decode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.packet import Packet, decode_packet
from common.png_reader import read_grayscale_png
from receiver.decoder import decode_data_bits
from receiver.perspective import (
    debug_colored_marker_detection,
    detect_colored_frame_corners,
    rectify_frame_image,
    rectify_frame_image_from_corners,
)
from receiver.photo_decoder import parse_crop


@dataclass(frozen=True)
class DecodedSequence:
    """Decoded multi-frame message and transmission metadata."""

    message: str
    packets_received: int
    total_packets: int
    payload_bytes: int
    corrected_symbols: int


def decode_packet_from_pixels(
    pixels: list[list[int]],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float | None = None,
) -> Packet:
    """Decode one rectified frame image into a packet."""
    decoded_bits = decode_data_bits(pixels, config=config, threshold=threshold)
    return decode_packet(decoded_bits.bits)


def decode_packet_from_image(
    image_path: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    threshold: float | None = None,
) -> Packet:
    """Decode one canonical PNG packet frame."""
    return decode_packet_from_pixels(read_grayscale_png(image_path), config=config, threshold=threshold)


def decode_sequence_folder(
    input_dir: str | Path,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
) -> DecodedSequence:
    """Decode all PNG frames in a folder and reconstruct the message."""
    paths = sorted(Path(input_dir).glob("*.png"))
    if not paths:
        raise ValueError(f"No PNG frames found in {input_dir}")

    packets = [decode_packet_from_image(path, config=config) for path in paths]
    return assemble_packets(packets, error_correction_bytes=error_correction_bytes)


def assemble_packets(
    packets: list[Packet],
    error_correction_bytes: int = 0,
) -> DecodedSequence:
    """Assemble packets into the original message."""
    if not packets:
        raise ValueError("No packets to assemble")

    total_packets = packets[0].total_packets
    packet_map: dict[int, Packet] = {}
    for packet in packets:
        if packet.total_packets != total_packets:
            raise ValueError("Inconsistent packet total count")
        packet_map[packet.sequence] = packet

    missing = [sequence for sequence in range(total_packets) if sequence not in packet_map]
    if missing:
        raise ValueError(f"Missing packet sequences: {missing}")

    transmitted_payload = b"".join(packet_map[sequence].payload for sequence in range(total_packets))
    corrected_symbols = 0
    if error_correction_bytes > 0:
        decoded = decode_reed_solomon(transmitted_payload, error_correction_bytes)
        payload = decoded.payload
        corrected_symbols = decoded.corrected_symbols
    else:
        payload = transmitted_payload

    return DecodedSequence(
        message=payload.decode("utf-8"),
        packets_received=len(packet_map),
        total_packets=total_packets,
        payload_bytes=len(payload),
        corrected_symbols=corrected_symbols,
    )


def decode_video_stream(
    camera_index: int = 0,
    source_url: str | None = None,
    screen_crop: str | None = None,
    camera_backend: str = "any",
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
    crop: str | None = None,
    auto_perspective: bool = True,
    legacy_markers: bool = False,
    preview: bool = False,
    preview_only: bool = False,
    preview_window: str | None = None,
    debug_detection: bool = False,
    max_frames: int = 900,
) -> DecodedSequence:
    """Capture camera frames until all packet sequences are received."""
    crop_rect = parse_crop(crop)
    screen_rect = parse_crop(screen_crop)
    preview_window_rect = parse_crop(preview_window)
    processed_window_rect = _below_window(preview_window_rect)
    debug_window_rect = _below_window(processed_window_rect or preview_window_rect)
    capture = _open_capture(camera_index, camera_backend, source_url, screen_rect)
    if not capture.isOpened():
        source_name = source_url or (f"pantalla {screen_crop}" if screen_crop else f"camara {camera_index}")
        raise RuntimeError(f"No se pudo abrir la fuente de video: {source_name}")

    packets: dict[int, Packet] = {}
    total_packets: int | None = None
    status = "Apunta la camara al frame del transmisor"
    frames_checked = 0
    try:
        while max_frames <= 0 or frames_checked < max_frames:
            frames_checked += 1
            ok, frame = capture.read()
            if not ok:
                continue

            preview_color = frame
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            preview_image = preview_color
            if crop_rect is not None:
                x, y, width, height = crop_rect
                preview_color = preview_color[y : y + height, x : x + width]
                gray = gray[y : y + height, x : x + width]
                preview_image = preview_color

            if preview_only:
                preview_corners = _try_detect_corners(preview_color, gray, legacy_markers)
                preview_status = (
                    "SOLO VISTA: esquinas detectadas, no decodifica"
                    if preview_corners is not None
                    else "SOLO VISTA: buscando esquinas, no decodifica"
                )
                camera_preview = _draw_detected_frame(preview_image, preview_corners)
                if debug_detection:
                    camera_preview = _draw_color_candidates(camera_preview, preview_color)
                _show_window("Camara receptor", _with_status(camera_preview, preview_status), preview_window_rect)
                if debug_detection:
                    _show_detection_debug(preview_color, debug_window_rect)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            detected_corners = None
            if auto_perspective:
                try:
                    try:
                        detected_corners = detect_colored_frame_corners(preview_color)
                        rectified = rectify_frame_image_from_corners(gray, detected_corners, config=config)
                        status = "Esquinas de color OK - intentando decodificar"
                    except Exception:
                        if not legacy_markers:
                            raise
                        rectified = rectify_frame_image(gray, config=config)
                        detected_corners = rectified.corners
                        status = "Marcadores blanco/negro OK - intentando decodificar"
                    gray = rectified.image
                except Exception:
                    status = "Buscando 4 esquinas de color"
                    if preview:
                        _show_window("Camara receptor", _with_status(preview_image, status), preview_window_rect)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            break
                    continue
            else:
                gray = cv2.resize(gray, (config.image_width, config.image_height), interpolation=cv2.INTER_AREA)
                detected_corners = _try_detect_corners(preview_color, gray, legacy_markers)
                status = "Modo directo de camara - intentando decodificar"

            try:
                packet = decode_packet_from_pixels(gray.astype("uint8").tolist(), config=config)
            except Exception:
                status = "Frame visto, pero bits/paquete no validos"
                if preview:
                    _show_decode_preview(
                        preview_image,
                        preview_color,
                        gray,
                        detected_corners,
                        status,
                        auto_perspective,
                        debug_detection,
                        preview_window_rect,
                        processed_window_rect,
                        debug_window_rect,
                    )
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                continue

            packets[packet.sequence] = packet
            total_packets = packet.total_packets
            status = f"Paquete {packet.sequence + 1}/{packet.total_packets} recibido"
            print(status)
            if total_packets is not None and len(packets) == total_packets:
                return assemble_packets(list(packets.values()), error_correction_bytes=error_correction_bytes)
            if preview:
                _show_decode_preview(
                    preview_image,
                    preview_color,
                    gray,
                    detected_corners,
                    status,
                    auto_perspective,
                    debug_detection,
                    preview_window_rect,
                    processed_window_rect,
                    debug_window_rect,
                )
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        capture.release()
        if preview or preview_only:
            cv2.destroyAllWindows()

    raise TimeoutError(f"No se recibieron todos los paquetes. Recibidos: {sorted(packets)}")


def _open_capture(
    camera_index: int,
    camera_backend: str,
    source_url: str | None = None,
    screen_rect=None,
):
    if screen_rect is not None:
        return _ScreenCapture(screen_rect)
    if source_url:
        return cv2.VideoCapture(source_url)
    if camera_backend == "dshow":
        return cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if camera_backend == "msmf":
        return cv2.VideoCapture(camera_index, cv2.CAP_MSMF)
    return cv2.VideoCapture(camera_index)


class _ScreenCapture:
    def __init__(self, screen_rect):
        self.screen_rect = screen_rect
        self.closed = False

    def isOpened(self) -> bool:
        return not self.closed

    def read(self):
        if self.closed:
            return False, None

        x, y, width, height = self.screen_rect
        image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        rgb = np.array(image)
        return True, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    def release(self) -> None:
        self.closed = True


_CONFIGURED_WINDOWS: set[str] = set()


def _show_window(name: str, image, window_rect=None) -> None:
    if name not in _CONFIGURED_WINDOWS:
        cv2.namedWindow(name, cv2.WINDOW_NORMAL)
        if window_rect is not None:
            x, y, width, height = window_rect
            cv2.resizeWindow(name, width, height)
            cv2.moveWindow(name, x, y)
        _CONFIGURED_WINDOWS.add(name)
    cv2.imshow(name, image)


def _show_decode_preview(
    preview_image,
    preview_color,
    processed_gray,
    detected_corners,
    status: str,
    auto_perspective: bool,
    debug_detection: bool,
    preview_window_rect,
    processed_window_rect,
    debug_window_rect,
) -> None:
    camera_preview = _draw_detected_frame(preview_image, detected_corners)
    if debug_detection:
        camera_preview = _draw_color_candidates(camera_preview, preview_color)
    _show_window("Camara receptor", _with_status(camera_preview, status), preview_window_rect)
    if auto_perspective:
        _show_window("Frame procesado", _with_status(processed_gray, status), processed_window_rect)
    if debug_detection:
        _show_detection_debug(preview_color, debug_window_rect)


def _below_window(window_rect):
    if window_rect is None:
        return None
    x, y, width, height = window_rect
    return x, y + height + 40, width, height


def _with_status(image, status: str):
    """Return a display copy with a readable status label."""
    display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image.copy()
    cv2.rectangle(display, (0, 0), (display.shape[1], 34), (0, 0, 0), thickness=-1)
    cv2.putText(
        display,
        status,
        (10, 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return display


def _draw_detected_frame(image, corners):
    """Draw the detected transmitter frame over the camera preview."""
    display = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if image.ndim == 2 else image.copy()
    if corners is None:
        return display

    points = [tuple(int(round(value)) for value in point) for point in corners]
    for start, end in zip(points, points[1:] + points[:1]):
        cv2.line(display, start, end, (0, 255, 0), 3, cv2.LINE_AA)
    for point in points:
        cv2.circle(display, point, 8, (0, 255, 255), thickness=-1, lineType=cv2.LINE_AA)
    return display


def _draw_color_candidates(image, color_image):
    display = image.copy()
    _, candidate_boxes = debug_colored_marker_detection(color_image)
    for box in candidate_boxes:
        points = [tuple(int(round(value)) for value in point) for point in box]
        for start, end in zip(points, points[1:] + points[:1]):
            cv2.line(display, start, end, (255, 180, 0), 2, cv2.LINE_AA)
    return display


def _show_detection_debug(color_image, window_rect=None) -> None:
    mask, candidate_boxes = debug_colored_marker_detection(color_image)
    debug_view = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    for box in candidate_boxes:
        points = [tuple(int(round(value)) for value in point) for point in box]
        for start, end in zip(points, points[1:] + points[:1]):
            cv2.line(debug_view, start, end, (0, 255, 0), 2, cv2.LINE_AA)
    _show_window(
        "Mascara esquinas color",
        _with_status(debug_view, f"Candidatos de color: {len(candidate_boxes)}"),
        window_rect,
    )


def _try_detect_corners(color_image, grayscale_image, legacy_markers: bool = False):
    """Return detected frame corners for preview overlays, or None if not found."""
    try:
        return detect_colored_frame_corners(color_image)
    except Exception:
        pass
    if not legacy_markers:
        return None
    try:
        return rectify_frame_image(grayscale_image).corners
    except Exception:
        return None

