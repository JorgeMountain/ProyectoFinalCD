import argparse

from common.modulation import MODULATION_CHOICES
from receiver.calibration import Ask4Calibration
from receiver.decoder import decode_static_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Decodifica un frame PNG offline.")
    parser.add_argument("--image", default="data/generated/frame_test.png", help="Ruta del frame PNG.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon usados.")
    parser.add_argument("--threshold", type=float, default=None, help="Umbral manual opcional.")
    parser.add_argument("--modulation", choices=MODULATION_CHOICES, default="ook", help="Esquema de modulacion visual.")
    args = parser.parse_args()

    result = decode_static_frame(
        args.image,
        threshold=args.threshold,
        error_correction_bytes=args.ecc,
        modulation=args.modulation,
    )

    print(f"Mensaje decodificado: {result.message}")
    print(f"Bits del mensaje: {result.payload_bits}")
    print(f"Bits leidos con prefijo: {result.transmitted_bits}")
    print(f"Bytes Reed-Solomon: {result.error_correction_bytes}")
    print(f"Simbolos corregidos: {result.corrected_symbols}")
    print(f"Modulacion: {result.modulation}")
    if isinstance(result.calibration, Ask4Calibration):
        print("Niveles 4-ASK calibrados: " + ", ".join(f"{level:.2f}" for level in result.calibration.levels))
    else:
        print(f"Umbral adaptativo: {result.calibration.threshold:.2f}")
    print(f"Marcadores validos: {result.calibration.markers_valid}")


if __name__ == "__main__":
    main()
