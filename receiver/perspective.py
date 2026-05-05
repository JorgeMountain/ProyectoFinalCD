"""Automatic screen localization and perspective correction."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig


Point = tuple[float, float]


@dataclass(frozen=True)
class RectificationResult:
    """Result from automatic perspective correction."""

    image: np.ndarray
    corners: tuple[Point, Point, Point, Point]


def rectify_frame_image(
    grayscale_image: np.ndarray,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
) -> RectificationResult:
    """Find the transmitter frame in a photo and warp it to canonical size."""
    if grayscale_image.ndim != 2:
        raise ValueError("Expected a grayscale image")

    corners = detect_frame_corners(grayscale_image)
    source = np.array(corners, dtype=np.float32)
    destination = np.array(
        [
            [0, 0],
            [config.image_width - 1, 0],
            [config.image_width - 1, config.image_height - 1],
            [0, config.image_height - 1],
        ],
        dtype=np.float32,
    )
    homography = cv2.getPerspectiveTransform(source, destination)
    warped = cv2.warpPerspective(
        grayscale_image,
        homography,
        (config.image_width, config.image_height),
        flags=cv2.INTER_LINEAR,
    )
    return RectificationResult(image=warped, corners=corners)


def detect_frame_corners(grayscale_image: np.ndarray) -> tuple[Point, Point, Point, Point]:
    """Detect frame outer corners from the four high-contrast corner markers."""
    candidates = _find_marker_candidates(grayscale_image)
    if len(candidates) < 4:
        raise ValueError(f"Expected at least 4 marker candidates, found {len(candidates)}")

    image_height, image_width = grayscale_image.shape[:2]
    image_corners = (
        (0.0, 0.0),
        (float(image_width - 1), 0.0),
        (float(image_width - 1), float(image_height - 1)),
        (0.0, float(image_height - 1)),
    )

    selected: list[_MarkerCandidate] = []
    for image_corner in image_corners:
        available = [candidate for candidate in candidates if candidate not in selected]
        selected.append(min(available, key=lambda candidate: _distance(candidate.center, image_corner)))

    return (
        _outer_corner(selected[0].box_points, "tl"),
        _outer_corner(selected[1].box_points, "tr"),
        _outer_corner(selected[2].box_points, "br"),
        _outer_corner(selected[3].box_points, "bl"),
    )


@dataclass(frozen=True)
class _MarkerCandidate:
    center: Point
    area: float
    box_points: tuple[Point, Point, Point, Point]


def _find_marker_candidates(grayscale_image: np.ndarray) -> list[_MarkerCandidate]:
    blurred = cv2.GaussianBlur(grayscale_image, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = grayscale_image.shape[0] * grayscale_image.shape[1]
    min_area = max(100.0, image_area * 0.00015)
    candidates: list[_MarkerCandidate] = []

    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < min_area:
            continue

        rect = cv2.minAreaRect(contour)
        (center_x, center_y), (width, height), _ = rect
        if width <= 0 or height <= 0:
            continue

        aspect = max(width, height) / min(width, height)
        if aspect > 5.0:
            continue

        box = cv2.boxPoints(rect)
        box_points = tuple((float(point[0]), float(point[1])) for point in box)
        candidates.append(
            _MarkerCandidate(
                center=(float(center_x), float(center_y)),
                area=area,
                box_points=box_points,  # type: ignore[arg-type]
            )
        )

    if len(candidates) > 24:
        candidates = sorted(candidates, key=lambda candidate: candidate.area, reverse=True)[:24]
    return candidates


def _outer_corner(points: tuple[Point, Point, Point, Point], corner_name: str) -> Point:
    if corner_name == "tl":
        return min(points, key=lambda point: point[0] + point[1])
    if corner_name == "tr":
        return max(points, key=lambda point: point[0] - point[1])
    if corner_name == "br":
        return max(points, key=lambda point: point[0] + point[1])
    if corner_name == "bl":
        return min(points, key=lambda point: point[0] - point[1])
    raise ValueError(f"Unknown corner name: {corner_name}")


def _distance(point_a: Point, point_b: Point) -> float:
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5
