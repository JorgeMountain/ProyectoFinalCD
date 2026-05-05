import argparse

from receiver.photo_decoder import decode_photo_frame, parse_crop


def main() -> None:
    parser = argparse.ArgumentParser(description="Decodifica una foto manualmente recortada del frame.")
    parser.add_argument("image", help="Ruta de la foto o captura a decodificar.")
    parser.add_argument(
        "--crop",
        help="Recorte manual en formato x,y,width,height. Si se omite, usa la imagen completa.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Umbral manual opcional. Si se omite, usa pilotos.",
    )
    args = parser.parse_args()

    result = decode_photo_frame(args.image, crop=parse_crop(args.crop), threshold=args.threshold)

    print(f"Mensaje decodificado: {result.message}")
    print(f"Bits del mensaje: {result.payload_bits}")
    print(f"Bits leidos con prefijo: {result.transmitted_bits}")
    print(f"Umbral adaptativo: {result.calibration.threshold:.2f}")
    print(f"Marcadores validos: {result.calibration.markers_valid}")


if __name__ == "__main__":
    main()

