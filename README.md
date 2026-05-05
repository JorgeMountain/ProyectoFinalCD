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

## Parte 2

El transmisor estatico genera una imagen PNG con una grilla visual codificada en OOK.

```bash
python main_tx_static.py
```

Salida generada:

```text
data/generated/frame_test.png
```

La imagen generada se ignora en Git porque es un artefacto reproducible.

## Parte 3

El receptor offline lee el PNG generado, promedia cada celda de la grilla,
demodula OOK y reconstruye el texto original.

```bash
python main_tx_static.py
python main_rx_offline.py
```

Salida esperada:

```text
Mensaje decodificado: Hola mundo
```

## Parte 4

El frame ahora tiene referencias explicitas para operar con fotos reales mas adelante:

- Marcadores en las cuatro esquinas para validar orientacion y preparar la deteccion de pantalla.
- Pilotos alternados blanco/negro para estimar el umbral de decision.
- Receptor offline con umbral adaptativo basado en pilotos.

Esto permite decodificar correctamente aunque la imagen tenga cambios simples de brillo y contraste.
