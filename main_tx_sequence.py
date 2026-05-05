import argparse

from transmitter.sequence import display_frame_sequence, generate_frame_sequence
from common.performance import plan_transmission


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera y opcionalmente muestra una transmision multi-frame.")
    parser.add_argument("--message", default="Hola mundo", help="Mensaje a transmitir.")
    parser.add_argument("--message-file", help="Archivo de texto a transmitir.")
    parser.add_argument("--output-dir", default="data/generated/sequence", help="Carpeta de frames PNG.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon.")
    parser.add_argument("--show", action="store_true", help="Muestra los frames en pantalla completa.")
    parser.add_argument("--duration-ms", type=int, default=150, help="Duracion de cada frame al mostrar.")
    parser.add_argument("--repeat", type=int, default=1, help="Repeticiones de la secuencia al mostrar.")
    args = parser.parse_args()

    message = args.message
    if args.message_file:
        with open(args.message_file, "r", encoding="utf-8") as file:
            message = file.read()

    result = generate_frame_sequence(
        message,
        output_dir=args.output_dir,
        error_correction_bytes=args.ecc,
    )
    plan = plan_transmission(
        message,
        error_correction_bytes=args.ecc,
        frame_duration_ms=args.duration_ms,
        repeat=args.repeat,
    )

    print(f"Frames generados: {len(result.frame_paths)}")
    print(f"Carpeta: {result.output_dir}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Bytes transmitidos: {result.transmitted_bytes}")
    print(f"Bytes utiles por frame: {result.packet_payload_capacity}")
    print(f"Bytes Reed-Solomon: {result.error_correction_bytes}")
    print(f"Tiempo estimado al mostrar: {plan.estimated_seconds:.2f} s")
    print(f"Tasa util estimada: {plan.throughput_bps:.1f} bps")
    print(f"Muestras de camara por frame: {plan.camera_samples_per_frame:.2f}")

    if args.show:
        display_frame_sequence(result.frame_paths, frame_duration_ms=args.duration_ms, repeat=args.repeat)


if __name__ == "__main__":
    main()
