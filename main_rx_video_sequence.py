import argparse
import time

from receiver.sequence_decoder import decode_video_stream


def main() -> None:
    parser = argparse.ArgumentParser(description="Recibe una transmision multi-frame desde webcam.")
    parser.add_argument("--camera", type=int, default=0, help="Indice de camara OpenCV.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon usados.")
    parser.add_argument("--crop", help="Recorte opcional x,y,width,height antes de perspectiva.")
    parser.add_argument("--no-auto-perspective", action="store_true", help="Desactiva correccion automatica.")
    parser.add_argument("--max-frames", type=int, default=900, help="Limite de frames de camara a intentar.")
    args = parser.parse_args()

    started_at = time.perf_counter()
    result = decode_video_stream(
        camera_index=args.camera,
        error_correction_bytes=args.ecc,
        crop=args.crop,
        auto_perspective=not args.no_auto_perspective,
        max_frames=args.max_frames,
    )
    elapsed = time.perf_counter() - started_at

    print(f"Mensaje decodificado: {result.message}")
    print(f"Paquetes recibidos: {result.packets_received}/{result.total_packets}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Simbolos corregidos: {result.corrected_symbols}")
    print(f"Tiempo de recepcion: {elapsed:.2f} s")


if __name__ == "__main__":
    main()
