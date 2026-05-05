from common.bit_utils import bits_to_text, text_to_bits
from common.frame_config import DEFAULT_FRAME_CONFIG
from common.modulation import ook_demodulate, ook_modulate


def main() -> None:
    message = "Hola mundo"
    bits = text_to_bits(message)
    symbols = ook_modulate(bits)
    recovered_bits = ook_demodulate(symbols)
    recovered_message = bits_to_text(recovered_bits)

    print(f"Mensaje original: {message}")
    print(f"Bits generados: {len(bits)}")
    print(f"Mensaje recuperado: {recovered_message}")
    print(f"Capacidad OOK aproximada por frame: {DEFAULT_FRAME_CONFIG.data_capacity_bits_ook} bits")


if __name__ == "__main__":
    main()

