"""Transmission planning utilities for speed/robustness tuning."""

from __future__ import annotations

import math
from dataclasses import dataclass

from common.ecc import encode_reed_solomon
from common.frame_config import DEFAULT_FRAME_CONFIG, FrameConfig
from common.packet import packet_payload_capacity


@dataclass(frozen=True)
class TransmissionPlan:
    """Estimated transmission performance for one message/configuration."""

    message_bytes: int
    transmitted_bytes: int
    frame_count: int
    payload_capacity_bytes: int
    frame_duration_ms: int
    repeat: int
    estimated_seconds: float
    throughput_bps: float
    camera_samples_per_frame: float
    meets_time_goal: bool
    meets_sampling_goal: bool


def plan_transmission(
    message: str,
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    error_correction_bytes: int = 0,
    frame_duration_ms: int = 150,
    repeat: int = 1,
    camera_fps: float = 30.0,
    target_seconds: float = 10.0,
    min_camera_samples_per_frame: float = 3.0,
) -> TransmissionPlan:
    """Estimate frame count, duration, throughput, and sampling margin."""
    if frame_duration_ms <= 0:
        raise ValueError("frame_duration_ms must be positive")
    if repeat <= 0:
        raise ValueError("repeat must be positive")
    if camera_fps <= 0:
        raise ValueError("camera_fps must be positive")

    payload = message.encode("utf-8")
    transmitted_payload = payload
    if error_correction_bytes > 0:
        transmitted_payload = encode_reed_solomon(payload, error_correction_bytes)

    capacity = packet_payload_capacity(config)
    frame_count = max(1, math.ceil(len(transmitted_payload) / capacity))
    estimated_seconds = frame_count * repeat * frame_duration_ms / 1000.0
    throughput_bps = (len(payload) * 8 / estimated_seconds) if estimated_seconds > 0 else 0.0
    camera_samples_per_frame = frame_duration_ms * camera_fps / 1000.0

    return TransmissionPlan(
        message_bytes=len(payload),
        transmitted_bytes=len(transmitted_payload),
        frame_count=frame_count,
        payload_capacity_bytes=capacity,
        frame_duration_ms=frame_duration_ms,
        repeat=repeat,
        estimated_seconds=estimated_seconds,
        throughput_bps=throughput_bps,
        camera_samples_per_frame=camera_samples_per_frame,
        meets_time_goal=estimated_seconds <= target_seconds,
        meets_sampling_goal=camera_samples_per_frame >= min_camera_samples_per_frame,
    )


def longest_message_bytes_for_goal(
    config: FrameConfig = DEFAULT_FRAME_CONFIG,
    frame_duration_ms: int = 150,
    repeat: int = 1,
    target_seconds: float = 10.0,
) -> int:
    """Estimate maximum raw message bytes that fit in the time goal without ECC overhead."""
    if frame_duration_ms <= 0 or repeat <= 0:
        raise ValueError("frame_duration_ms and repeat must be positive")
    available_frames = math.floor(target_seconds * 1000 / (frame_duration_ms * repeat))
    return max(0, available_frames * packet_payload_capacity(config))

