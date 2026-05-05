# Proyecto Final Comunicaciones Digitales

Implementacion por partes de un modem optico pantalla-camara en Python.

## Parte 1

La base actual incluye:

- Conversion texto -> bits -> texto.
- Prefijo de longitud para saber donde termina el mensaje.
- Configuracion inicial de grilla visual.
- Modulacion OOK, BPSK y codificacion Manchester.

## Verificacion

```bash
python -m unittest discover -s tests
python main_part1.py
```

