from transmitter.generator import generate_static_frame


def main() -> None:
    message = "Hola mundo"
    result = generate_static_frame(message)

    print(f"Frame generado: {result.output_path}")
    print(f"Bits del mensaje: {result.payload_bits}")
    print(f"Bits transmitidos con prefijo: {result.transmitted_bits}")
    print(f"Capacidad del frame: {result.data_capacity_bits} bits")


if __name__ == "__main__":
    main()

