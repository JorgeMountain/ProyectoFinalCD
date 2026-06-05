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
    return rectify_frame_image_from_corners(grayscale_image, corners, config=config)


def rectify_frame_image_from_corners(
    grayscale_image: np.ndarray,
    corners: tuple[Point, Point, Point, Point],
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
) -> RectificationResult:
    """Warp a grayscale frame using previously detected outer corners."""
    if grayscale_image.ndim != 2:
        raise ValueError("Expected a grayscale image")

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


def detect_colored_frame_corners(color_image: np.ndarray) -> tuple[Point, Point, Point, Point]:
    """Detect frame outer corners from saturated color corner markers."""
    candidates = _find_colored_marker_candidates(color_image)
    if len(candidates) < 4:
        raise ValueError(f"Expected at least 4 colored marker candidates, found {len(candidates)}")

    return _select_colored_frame_corners(candidates, color_image.shape[:2])


def debug_colored_marker_detection(color_image: np.ndarray) -> tuple[np.ndarray, list[tuple[Point, Point, Point, Point]]]:
    """Return the color marker mask and candidate boxes for preview diagnostics."""
    candidates = _find_colored_marker_candidates(color_image)
    return _colored_marker_mask(color_image), [candidate.box_points for candidate in candidates]


def detect_frame_corners(grayscale_image: np.ndarray) -> tuple[Point, Point, Point, Point]:
    """Detect frame outer corners from the four high-contrast corner markers."""
    candidates = _find_marker_candidates(grayscale_image)
    if len(candidates) < 4:
        raise ValueError(f"Expected at least 4 marker candidates, found {len(candidates)}")

    return _select_frame_corners(candidates, grayscale_image.shape[:2])


def _select_frame_corners(
    candidates: list["_MarkerCandidate"],
    image_shape: tuple[int, int],
) -> tuple[Point, Point, Point, Point]:
    image_height, image_width = image_shape
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


def _select_colored_frame_corners(
    candidates: list["_MarkerCandidate"],
    image_shape: tuple[int, int],
) -> tuple[Point, Point, Point, Point]:
    image_height, image_width = image_shape
    center_x = image_width / 2
    center_y = image_height / 2
    quadrants: dict[str, list[_MarkerCandidate]] = {"tl": [], "tr": [], "br": [], "bl": []}

    for candidate in candidates:
        x, y = candidate.center
        if x < center_x and y < center_y:
            quadrants["tl"].append(candidate)
        elif x >= center_x and y < center_y:
            quadrants["tr"].append(candidate)
        elif x >= center_x and y >= center_y:
            quadrants["br"].append(candidate)
        else:
            quadrants["bl"].append(candidate)

    if all(quadrants.values()):
        selected = {
            name: max(bucket, key=lambda candidate: candidate.area)
            for name, bucket in quadrants.items()
        }
        return (
            _outer_corner(selected["tl"].box_points, "tl"),
            _outer_corner(selected["tr"].box_points, "tr"),
            _outer_corner(selected["br"].box_points, "br"),
            _outer_corner(selected["bl"].box_points, "bl"),
        )

    return _select_frame_corners(candidates, image_shape)


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
    patterned_candidates: list[_MarkerCandidate] = []
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
        candidate = _MarkerCandidate(
            center=(float(center_x), float(center_y)),
            area=area,
            box_points=box_points,  # type: ignore[arg-type]
        )
        candidates.append(candidate)
        if _looks_like_corner_marker(grayscale_image, rect):
            patterned_candidates.append(candidate)

    if len(patterned_candidates) >= 4:
        candidates = patterned_candidates
    if len(candidates) > 24:
        candidates = sorted(candidates, key=lambda candidate: candidate.area, reverse=True)[:24]
    return candidates


def _find_colored_marker_candidates(color_image: np.ndarray) -> list[_MarkerCandidate]:
    if color_image.ndim != 3:
        raise ValueError("Expected a BGR color image")

    hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
    mask = _colored_marker_mask(color_image)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    image_area = color_image.shape[0] * color_image.shape[1]
    min_area = max(25.0, image_area * 0.00005)
    patterned_candidates: list[_MarkerCandidate] = []
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
        if aspect > 4.0:
            continue

        box = cv2.boxPoints(rect)
        box_points = tuple((float(point[0]), float(point[1])) for point in box)
        candidate = _MarkerCandidate(
            center=(float(center_x), float(center_y)),
            area=area,
            box_points=box_points,  # type: ignore[arg-type]
        )
        candidates.append(candidate)
        if _looks_like_colored_corner_marker(hsv, rect):
            patterned_candidates.append(candidate)

    if len(patterned_candidates) >= 4:
        candidates = patterned_candidates
    if len(candidates) > 24:
        candidates = sorted(candidates, key=lambda candidate: candidate.area, reverse=True)[:24]
    return candidates


def _colored_marker_mask(color_image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(color_image, cv2.COLOR_BGR2HSV)
    yellow_hsv = cv2.inRange(hsv, np.array([12, 70, 90]), np.array([45, 255, 255]))
    blue, green, red = cv2.split(color_image)
    yellow_bgr = (
        (red.astype("int16") > 120)
        & (green.astype("int16") > 110)
        & (blue.astype("int16") < 140)
        & ((red.astype("int16") - blue.astype("int16")) > 35)
        & ((green.astype("int16") - blue.astype("int16")) > 35)
    ).astype("uint8") * 255
    mask = cv2.bitwise_and(yellow_hsv, yellow_bgr)
    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


def _looks_like_corner_marker(grayscale_image: np.ndarray, rect) -> bool:
    """Return True for the transmitter marker pattern: bright square with dark center."""
    box = cv2.boxPoints(rect)
    x, y, width, height = cv2.boundingRect(box.astype("int32"))
    if width < 8 or height < 8:
        return False

    image_height, image_width = grayscale_image.shape[:2]
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(image_width, x + width)
    y1 = min(image_height, y + height)
    patch = grayscale_image[y0:y1, x0:x1]
    if patch.size == 0:
        return False

    patch_height, patch_width = patch.shape[:2]
    center_x0 = patch_width // 3
    center_y0 = patch_height // 3
    center_x1 = max(center_x0 + 1, (patch_width * 2) // 3)
    center_y1 = max(center_y0 + 1, (patch_height * 2) // 3)
    center = patch[center_y0:center_y1, center_x0:center_x1]

    border_mask = np.ones(patch.shape, dtype=bool)
    border_mask[center_y0:center_y1, center_x0:center_x1] = False
    border = patch[border_mask]
    if center.size == 0 or border.size == 0:
        return False

    return float(border.mean()) > 135.0 and float(center.mean()) < 120.0 and float(border.mean() - center.mean()) > 45.0


def _looks_like_colored_corner_marker(hsv_image: np.ndarray, rect) -> bool:
    box = cv2.boxPoints(rect)
    x, y, width, height = cv2.boundingRect(box.astype("int32"))
    if width < 8 or height < 8:
        return False

    image_height, image_width = hsv_image.shape[:2]
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(image_width, x + width)
    y1 = min(image_height, y + height)
    patch = hsv_image[y0:y1, x0:x1]
    if patch.size == 0:
        return False

    patch_height, patch_width = patch.shape[:2]
    center_x0 = patch_width // 3
    center_y0 = patch_height // 3
    center_x1 = max(center_x0 + 1, (patch_width * 2) // 3)
    center_y1 = max(center_y0 + 1, (patch_height * 2) // 3)
    center = patch[center_y0:center_y1, center_x0:center_x1]

    border_mask = np.ones((patch_height, patch_width), dtype=bool)
    border_mask[center_y0:center_y1, center_x0:center_x1] = False
    border = patch[border_mask]
    if center.size == 0 or border.size == 0:
        return False

    border_hue = float(border[:, 0].mean())
    border_saturation = float(border[:, 1].mean())
    border_value = float(border[:, 2].mean())
    center_value = float(center[:, :, 2].mean())
    return 12.0 <= border_hue <= 45.0 and border_saturation > 70.0 and border_value > 90.0 and center_value < border_value - 20.0


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
