from receiver.decoder import decode_static_frame


def main() -> None:
    result = decode_static_frame()

    print(f"Mensaje decodificado: {result.message}")
    print(f"Bits del mensaje: {result.payload_bits}")
    print(f"Bits leidos con prefijo: {result.transmitted_bits}")
    print(f"Umbral adaptativo: {result.calibration.threshold:.2f}")
    print(f"Marcadores validos: {result.calibration.markers_valid}")


if __name__ == "__main__":
    main()
