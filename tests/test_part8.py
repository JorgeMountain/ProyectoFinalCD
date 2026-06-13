import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np

from common.ecc import encode_reed_solomon
from common.packet import Packet, decode_packet, encode_packet, packet_payload_capacity, split_payload
from receiver.sequence_decoder import assemble_packets, decode_sequence_folder, decode_video_stream
from transmitter.sequence import generate_frame_sequence


class PacketProtocolTests(unittest.TestCase):
    def test_packet_capacity_depends_on_modulation(self):
        self.assertEqual(packet_payload_capacity(modulation="ook"), 56)
        self.assertEqual(packet_payload_capacity(modulation="4ask"), 123)

    def test_packet_header_rejects_modulation_mismatch(self):
        packet = Packet(sequence=0, total_packets=1, payload=b"datos", is_end=True)
        encoded = encode_packet(packet, modulation="4ask")

        self.assertEqual(decode_packet(encoded, expected_modulation="4ask"), packet)
        with self.assertRaisesRegex(ValueError, "modulation"):
            decode_packet(encoded, expected_modulation="ook")

    def test_packet_round_trip(self):
        packet = Packet(sequence=1, total_packets=3, payload=b"datos", is_end=False)

        decoded = decode_packet(encode_packet(packet))

        self.assertEqual(decoded, packet)

    def test_payload_capacity_is_byte_aligned(self):
        self.assertGreaterEqual(packet_payload_capacity(), 50)

    def test_split_payload(self):
        chunks = split_payload(b"a" * (packet_payload_capacity() + 1))

        self.assertEqual(len(chunks), 2)


class MultiFrameSequenceTests(unittest.TestCase):
    def test_regeneration_removes_stale_sequence_frames(self):
        message = "A" * 500
        with tempfile.TemporaryDirectory() as tmpdir:
            generate_frame_sequence(
                message,
                output_dir=tmpdir,
                error_correction_bytes=16,
                modulation="ook",
            )
            generated = generate_frame_sequence(
                message,
                output_dir=tmpdir,
                error_correction_bytes=16,
                modulation="4ask",
            )

            self.assertEqual(len(list(Path(tmpdir).glob("frame_*.png"))), 5)
            self.assertEqual(len(generated.frame_paths), 5)

    def test_video_decodes_actual_4ask_frames(self):
        class FrameCapture:
            def __init__(self, frames):
                self.frames = list(frames)

            def isOpened(self):
                return True

            def read(self):
                if not self.frames:
                    return False, None
                return True, self.frames.pop(0)

            def release(self):
                pass

        message = "Prueba 4-ASK por video"
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = generate_frame_sequence(
                message,
                output_dir=tmpdir,
                error_correction_bytes=16,
                modulation="4ask",
            )
            frames = [
                cv2.imread(str(path), cv2.IMREAD_COLOR)
                for path in generated.frame_paths
            ]

            with patch(
                "receiver.sequence_decoder._open_capture",
                return_value=FrameCapture(frames),
            ):
                decoded = decode_video_stream(
                    auto_perspective=False,
                    error_correction_bytes=16,
                    modulation="4ask",
                    max_frames=len(frames),
                )

        self.assertEqual(decoded.message, message)
        self.assertGreaterEqual(decoded.reception_seconds, 0.0)

    def test_generate_and_decode_500_character_4ask_sequence_with_ecc(self):
        message = "A" * 500
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = generate_frame_sequence(
                message,
                output_dir=tmpdir,
                error_correction_bytes=16,
                modulation="4ask",
            )

            decoded = decode_sequence_folder(
                tmpdir,
                error_correction_bytes=16,
                modulation="4ask",
            )

            self.assertEqual(len(generated.frame_paths), 5)
            self.assertEqual(generated.packet_payload_capacity, 123)
            self.assertEqual(decoded.message, message)

    def test_video_retries_after_uncorrectable_packet_copy(self):
        class FakeCapture:
            def __init__(self):
                self.frames = [np.zeros((20, 20, 3), dtype=np.uint8) for _ in range(3)]

            def isOpened(self):
                return True

            def read(self):
                return True, self.frames.pop(0)

            def release(self):
                pass

        encoded = encode_reed_solomon(b"Hola mundo", 4)
        split_at = len(encoded) // 2
        first_chunk = encoded[:split_at]
        second_chunk = encoded[split_at:]
        corrupted_chunk = bytes(value ^ 0xFF for value in second_chunk)
        packets = [
            Packet(sequence=0, total_packets=2, payload=first_chunk, is_end=False),
            Packet(sequence=1, total_packets=2, payload=corrupted_chunk, is_end=True),
            Packet(sequence=1, total_packets=2, payload=second_chunk, is_end=True),
        ]

        with (
            patch("receiver.sequence_decoder._open_capture", return_value=FakeCapture()),
            patch("receiver.sequence_decoder.decode_packet_from_pixels", side_effect=packets),
            patch("receiver.sequence_decoder.time.perf_counter", side_effect=[100.0, 102.5]),
        ):
            decoded = decode_video_stream(
                auto_perspective=False,
                error_correction_bytes=4,
                max_frames=3,
            )

        self.assertEqual(decoded.message, "Hola mundo")
        self.assertEqual(decoded.reception_seconds, 2.5)

    def test_video_reception_time_starts_with_first_valid_packet(self):
        class FakeCapture:
            def __init__(self):
                self.frames = [np.zeros((20, 20, 3), dtype=np.uint8) for _ in range(3)]

            def isOpened(self):
                return True

            def read(self):
                return True, self.frames.pop(0)

            def release(self):
                pass

        packets = [
            ValueError("transmisor no detectado"),
            Packet(sequence=0, total_packets=2, payload=b"Hola ", is_end=False),
            Packet(sequence=1, total_packets=2, payload=b"mundo", is_end=True),
        ]

        with (
            patch("receiver.sequence_decoder._open_capture", return_value=FakeCapture()),
            patch("receiver.sequence_decoder.decode_packet_from_pixels", side_effect=packets),
            patch("receiver.sequence_decoder.time.perf_counter", side_effect=[100.0, 102.5]),
        ):
            decoded = decode_video_stream(auto_perspective=False, max_frames=3)

        self.assertEqual(decoded.message, "Hola mundo")
        self.assertEqual(decoded.reception_seconds, 2.5)

    def test_generate_and_decode_sequence_folder(self):
        message = "Hola mundo " * 20
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = generate_frame_sequence(message, output_dir=tmpdir)

            decoded = decode_sequence_folder(tmpdir)

            self.assertGreater(len(generated.frame_paths), 1)
            self.assertEqual(decoded.message, message)
            self.assertEqual(decoded.packets_received, decoded.total_packets)

    def test_generate_and_decode_500_character_sequence_with_ecc(self):
        message = "A" * 500
        with tempfile.TemporaryDirectory() as tmpdir:
            generated = generate_frame_sequence(message, output_dir=tmpdir, error_correction_bytes=16)

            decoded = decode_sequence_folder(tmpdir, error_correction_bytes=16)

            self.assertEqual(decoded.message, message)
            self.assertEqual(decoded.payload_bytes, 500)
            self.assertEqual(generated.error_correction_bytes, 16)
            self.assertLessEqual(len(generated.frame_paths), 10)

    def test_assemble_packets_accepts_out_of_order_packets(self):
        packets = [
            Packet(sequence=1, total_packets=2, payload=b"mundo", is_end=True),
            Packet(sequence=0, total_packets=2, payload=b"Hola ", is_end=False),
        ]

        decoded = assemble_packets(packets)

        self.assertEqual(decoded.message, "Hola mundo")


if __name__ == "__main__":
    unittest.main()

