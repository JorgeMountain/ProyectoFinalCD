import argparse

import cv2

from common.modulation import MODULATION_CHOICES
from receiver.sequence_decoder import decode_video_stream


def main() -> None:
    parser = argparse.ArgumentParser(description="Recibe una transmision multi-frame desde webcam.")
    parser.add_argument("--camera", type=int, default=0, help="Indice de camara OpenCV.")
    parser.add_argument("--source-url", help="URL de video, por ejemplo el stream HTTP de DroidCam.")
    parser.add_argument("--screen-crop", help="Captura una region de pantalla x,y,width,height como fuente de video.")
    parser.add_argument("--backend", choices=["any", "dshow", "msmf"], default="any", help="Backend de camara OpenCV.")
    parser.add_argument("--scan-cameras", action="store_true", help="Prueba indices de camara y muestra una vista previa.")
    parser.add_argument("--scan-max", type=int, default=6, help="Indice maximo para --scan-cameras.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon usados.")
    parser.add_argument("--modulation", choices=MODULATION_CHOICES, default="ook", help="Esquema de modulacion visual.")
    parser.add_argument("--crop", help="Recorte opcional x,y,width,height antes de perspectiva.")
    parser.add_argument("--no-auto-perspective", action="store_true", help="Desactiva correccion automatica.")
    parser.add_argument("--legacy-markers", action="store_true", help="Permite detectar marcadores antiguos blanco/negro.")
    parser.add_argument("--preview", action="store_true", help="Muestra la vista de camara durante la recepcion.")
    parser.add_argument("--preview-only", action="store_true", help="Solo muestra la camara, sin intentar decodificar.")
    parser.add_argument("--preview-window", help="Posicion/tamano de la ventana preview x,y,width,height.")
    parser.add_argument("--debug-detection", action="store_true", help="Muestra mascara y candidatos de deteccion de esquinas.")
    parser.add_argument("--max-frames", type=int, default=900, help="Limite de frames de camara a intentar. Usa 0 para esperar sin limite.")
    args = parser.parse_args()

    if args.scan_cameras:
        scan_cameras(args.scan_max, args.backend)
        return

    try:
        result = decode_video_stream(
            camera_index=args.camera,
            source_url=args.source_url,
            screen_crop=args.screen_crop,
            camera_backend=args.backend,
            error_correction_bytes=args.ecc,
            crop=args.crop,
            auto_perspective=not args.no_auto_perspective,
            legacy_markers=args.legacy_markers,
            preview=args.preview,
            preview_only=args.preview_only,
            preview_window=args.preview_window,
            debug_detection=args.debug_detection,
            max_frames=args.max_frames,
            modulation=args.modulation,
        )
    except TimeoutError:
        if args.preview_only:
            print("Vista previa cerrada. No se intento decodificar porque usaste --preview-only.")
            return
        print("No se recibieron todos los paquetes. Revisa que el transmisor este visible y que aparezca el rectangulo de deteccion.")
        return

    print(f"Mensaje decodificado: {result.message}")
    print(f"Paquetes recibidos: {result.packets_received}/{result.total_packets}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Simbolos corregidos: {result.corrected_symbols}")
    print(f"Modulacion: {result.modulation}")
    print(f"Tiempo de recepcion desde deteccion: {result.reception_seconds:.2f} s")


def scan_cameras(max_index: int, backend: str) -> None:
    backend_id = _backend_id(backend)
    print("Probando camaras. Presiona cualquier tecla en cada ventana para continuar.")
    for index in range(max_index + 1):
        capture = cv2.VideoCapture(index) if backend_id is None else cv2.VideoCapture(index, backend_id)
        if not capture.isOpened():
            print(f"Camara {index}: no abre")
            continue

        ok, frame = capture.read()
        capture.release()
        if not ok or frame is None:
            print(f"Camara {index}: abre, pero no entrega imagen")
            continue

        print(f"Camara {index}: OK {frame.shape[1]}x{frame.shape[0]}")
        cv2.putText(frame, f"Camara {index} - backend {backend}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)
        cv2.imshow(f"Camara {index}", frame)
        cv2.waitKey(0)
        cv2.destroyWindow(f"Camara {index}")


def _backend_id(backend: str) -> int | None:
    if backend == "dshow":
        return cv2.CAP_DSHOW
    if backend == "msmf":
        return cv2.CAP_MSMF
    return None


if __name__ == "__main__":
    main()
