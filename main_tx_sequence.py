import argparse

from common.modulation import MODULATION_CHOICES
from common.performance import plan_transmission
from transmitter.sequence import display_frame_sequence, generate_frame_sequence


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera y opcionalmente muestra una transmision multi-frame.")
    parser.add_argument("--message", default="Hola mundo", help="Mensaje a transmitir.")
    parser.add_argument("--message-file", help="Archivo de texto a transmitir.")
    parser.add_argument("--output-dir", default="data/generated/sequence", help="Carpeta de frames PNG.")
    parser.add_argument("--ecc", type=int, default=0, help="Bytes de paridad Reed-Solomon.")
    parser.add_argument("--modulation", choices=MODULATION_CHOICES, default="ook", help="Esquema de modulacion visual.")
    parser.add_argument("--show", action="store_true", help="Muestra los frames en pantalla completa.")
    parser.add_argument("--windowed", action="store_true", help="Muestra los frames en una ventana en vez de pantalla completa.")
    parser.add_argument("--window-width", type=int, default=960, help="Ancho de la ventana si usas --windowed.")
    parser.add_argument("--window-height", type=int, default=540, help="Alto de la ventana si usas --windowed.")
    parser.add_argument("--window-x", type=int, help="Posicion X de la ventana si usas --windowed.")
    parser.add_argument("--window-y", type=int, help="Posicion Y de la ventana si usas --windowed.")
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
        modulation=args.modulation,
    )
    plan = plan_transmission(
        message,
        error_correction_bytes=args.ecc,
        frame_duration_ms=args.duration_ms,
        repeat=args.repeat,
        modulation=args.modulation,
    )

    print(f"Frames generados: {len(result.frame_paths)}")
    print(f"Carpeta: {result.output_dir}")
    print(f"Bytes del mensaje: {result.payload_bytes}")
    print(f"Bytes transmitidos: {result.transmitted_bytes}")
    print(f"Bytes utiles por frame: {result.packet_payload_capacity}")
    print(f"Bytes Reed-Solomon: {result.error_correction_bytes}")
    print(f"Modulacion: {result.modulation}")
    print(f"Tiempo estimado al mostrar: {plan.estimated_seconds:.2f} s")
    print(f"Tasa util estimada: {plan.throughput_bps:.1f} bps")
    print(f"Muestras de camara por frame: {plan.camera_samples_per_frame:.2f}")

    if args.show:
        display_frame_sequence(
            result.frame_paths,
            frame_duration_ms=args.duration_ms,
            repeat=args.repeat,
            fullscreen=not args.windowed,
            window_size=(args.window_width, args.window_height),
            window_position=(args.window_x, args.window_y) if args.window_x is not None and args.window_y is not None else None,
        )


if __name__ == "__main__":
    main()
