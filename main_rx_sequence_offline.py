import argparse

from common.metrics import text_bit_error_rate
from common.modulation import MODULATION_CHOICES
from receiver.sequence_decoder import decode_sequence_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Decodifica una carpeta de frames multi-frame.")
    parser.add_argument("--input-dir", default="data/generated/sequence", help="Carpeta con PNGs de la secuencia.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon usados.")
    parser.add_argument("--modulation", choices=MODULATION_CHOICES, default="ook", help="Esquema de modulacion visual.")
    parser.add_argument("--expected", help="Mensaje esperado para calcular BER.")
    parser.add_argument("--expected-file", help="Archivo con el mensaje esperado para calcular BER.")
    args = parser.parse_args()

    result = decode_sequence_folder(
        args.input_dir,
        error_correction_bytes=args.ecc,
        modulation=args.modulation,
    )

    print(f"Mensaje decodificado: {result.message}")
    print(f"Paquetes recibidos: {result.packets_received}/{result.total_packets}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Simbolos corregidos: {result.corrected_symbols}")
    print(f"Modulacion: {result.modulation}")

    expected = args.expected
    if args.expected_file:
        with open(args.expected_file, "r", encoding="utf-8") as file:
            expected = file.read()
    if expected is not None:
        print(f"BER: {text_bit_error_rate(expected, result.message):.6g}")


if __name__ == "__main__":
    main()
