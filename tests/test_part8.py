import tempfile
import unittest
from pathlib import Path

from common.packet import Packet, decode_packet, encode_packet, packet_payload_capacity, split_payload
from receiver.sequence_decoder import assemble_packets, decode_sequence_folder
from transmitter.sequence import generate_frame_sequence


class PacketProtocolTests(unittest.TestCase):
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

