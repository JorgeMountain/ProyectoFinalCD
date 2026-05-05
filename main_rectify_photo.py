import argparse
from pathlib import Path

import cv2

from receiver.photo_decoder import parse_crop
from receiver.perspective import rectify_frame_image


def main() -> None:
    parser = argparse.ArgumentParser(description="Detecta la pantalla y guarda una imagen rectificada.")
    parser.add_argument("image", help="Ruta de la foto/captura original.")
    parser.add_argument("--output", default="data/captures/rectified.png", help="Ruta de salida.")
    parser.add_argument("--crop", help="Recorte opcional previo en formato x,y,width,height.")
    args = parser.parse_args()

    image = cv2.imread(args.image, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {args.image}")

    crop = parse_crop(args.crop)
    if crop is not None:
        x, y, width, height = crop
        image = image[y : y + height, x : x + width]

    result = rectify_frame_image(image)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), result.image)

    print(f"Imagen rectificada: {output}")
    print(f"Esquinas detectadas: {result.corners}")


if __name__ == "__main__":
    main()

