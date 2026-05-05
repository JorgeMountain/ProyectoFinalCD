import argparse

from receiver.sequence_decoder import decode_sequence_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Decodifica una carpeta de frames multi-frame.")
    parser.add_argument("--input-dir", default="data/generated/sequence", help="Carpeta con PNGs de la secuencia.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon usados.")
    args = parser.parse_args()

    result = decode_sequence_folder(args.input_dir, error_correction_bytes=args.ecc)

    print(f"Mensaje decodificado: {result.message}")
    print(f"Paquetes recibidos: {result.packets_received}/{result.total_packets}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Simbolos corregidos: {result.corrected_symbols}")


if __name__ == "__main__":
    main()

