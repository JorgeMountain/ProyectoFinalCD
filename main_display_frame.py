import argparse
from pathlib import Path

import cv2

from transmitter.generator import generate_static_frame


def main() -> None:
    parser = argparse.ArgumentParser(description="Muestra el frame transmisor en pantalla completa.")
    parser.add_argument("--message", default="Hola mundo", help="Mensaje a codificar si se debe generar el frame.")
    parser.add_argument("--image", default="data/generated/frame_test.png", help="Imagen del frame transmisor.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon si genera el frame.")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        generate_static_frame(args.message, output_path=image_path, error_correction_bytes=args.ecc)

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"No se pudo leer la imagen: {image_path}")

    cv2.namedWindow("Transmisor", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Transmisor", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("Transmisor", image)
    print("Frame en pantalla completa. Presiona q o ESC para cerrar.")

    while True:
        key = cv2.waitKey(100) & 0xFF
        if key in (27, ord("q")):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
