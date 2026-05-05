import argparse

from transmitter.generator import generate_static_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera un frame estatico del transmisor.")
    parser.add_argument("--message", default="Hola mundo", help="Mensaje a codificar.")
    parser.add_argument("--output", default="data/generated/frame_test.png", help="Ruta PNG de salida.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon.")
    args = parser.parse_args()

    result = generate_static_frame(
        args.message,
        output_path=args.output,
        error_correction_bytes=args.ecc,
    )

    print(f"Frame generado: {result.output_path}")
    print(f"Bits del mensaje: {result.payload_bits}")
    print(f"Bits transmitidos con prefijo: {result.transmitted_bits}")
    print(f"Bytes Reed-Solomon: {result.error_correction_bytes}")
    print(f"Capacidad del frame: {result.data_capacity_bits} bits")


if __name__ == "__main__":
    main()
