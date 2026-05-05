import argparse

from common.metrics import text_bit_error_rate
from common.performance import longest_message_bytes_for_goal, plan_transmission


def main() -> None:
    parser = argparse.ArgumentParser(description="Analiza velocidad y BER de una configuracion.")
    parser.add_argument("--message", default="A" * 500, help="Mensaje a analizar.")
    parser.add_argument("--message-file", help="Archivo de texto a analizar.")
    parser.add_argument("--ecc", type=int, default=16, help="Bytes de paridad Reed-Solomon.")
    parser.add_argument("--duration-ms", type=int, default=150, help="Duracion por frame.")
    parser.add_argument("--repeat", type=int, default=1, help="Repeticiones completas de la secuencia.")
    parser.add_argument("--camera-fps", type=float, default=30.0, help="FPS esperado de camara.")
    parser.add_argument("--target-seconds", type=float, default=10.0, help="Meta de tiempo.")
    parser.add_argument("--received", help="Mensaje recibido para calcular BER.")
    args = parser.parse_args()

    message = args.message
    if args.message_file:
        with open(args.message_file, "r", encoding="utf-8") as file:
            message = file.read()

    plan = plan_transmission(
        message,
        error_correction_bytes=args.ecc,
        frame_duration_ms=args.duration_ms,
        repeat=args.repeat,
        camera_fps=args.camera_fps,
        target_seconds=args.target_seconds,
    )

    print(f"Bytes del mensaje: {plan.message_bytes}")
    print(f"Bytes transmitidos: {plan.transmitted_bytes}")
    print(f"Frames necesarios: {plan.frame_count}")
    print(f"Bytes utiles por frame: {plan.payload_capacity_bytes}")
    print(f"Tiempo estimado: {plan.estimated_seconds:.2f} s")
    print(f"Tasa util estimada: {plan.throughput_bps:.1f} bps")
    print(f"Muestras de camara por frame: {plan.camera_samples_per_frame:.2f}")
    print(f"Cumple meta de tiempo: {plan.meets_time_goal}")
    print(f"Cumple margen de muestreo: {plan.meets_sampling_goal}")
    print(f"Bytes maximos sin ECC en {args.target_seconds:.1f}s: {longest_message_bytes_for_goal()}")

    if args.received is not None:
        print(f"BER vs recibido: {text_bit_error_rate(message, args.received):.6g}")


if __name__ == "__main__":
    main()

