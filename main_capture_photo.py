import argparse
from pathlib import Path

import cv2


def main() -> None:
    parser = argparse.ArgumentParser(description="Captura una foto desde la webcam para decodificacion offline.")
    parser.add_argument("--camera", type=int, default=0, help="Indice de camara OpenCV.")
    parser.add_argument(
        "--output",
        default="data/captures/capture.jpg",
        help="Ruta donde guardar la captura.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        raise RuntimeError(f"No se pudo abrir la camara {args.camera}")

    print("Presiona ESPACIO para guardar la foto. Presiona q o ESC para salir.")
    saved = False
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("No se pudo leer frame de la camara")

            cv2.imshow("Captura receptor", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(" ") or key == 13:
                cv2.imwrite(str(output), frame)
                print(f"Foto guardada: {output}")
                saved = True
                break
            if key in (27, ord("q")):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()

    if not saved:
        print("No se guardo ninguna foto.")


if __name__ == "__main__":
    main()

