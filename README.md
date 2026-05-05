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

## Parte 5

Flujo con foto real de la pantalla:

1. Generar el frame.

```bash
python main_tx_static.py
```

2. Mostrarlo en pantalla completa.

```bash
python main_display_frame.py
```

3. Capturar una foto con la webcam del receptor.

```bash
python main_capture_photo.py --output data/captures/capture.jpg
```

4. Decodificar la foto.

```bash
python main_rx_photo.py data/captures/capture.jpg
```

Si la pantalla ocupa solo una parte de la foto, usar recorte manual:

```bash
python main_rx_photo.py data/captures/capture.jpg --crop x,y,width,height
```

Ejemplo:

```bash
python main_rx_photo.py data/captures/capture.jpg --crop 120,80,900,520
```

En esta parte el recorte todavia es manual. La deteccion automatica de pantalla y correccion de perspectiva quedan para la Parte 6.

## Parte 6

El receptor puede detectar automaticamente los marcadores de esquina, estimar la homografia y rectificar
la foto antes de decodificar.

Decodificar con correccion automatica de perspectiva:

```bash
python main_rx_photo.py data/captures/capture.jpg --auto-perspective
```

Guardar una imagen rectificada para inspeccion visual:

```bash
python main_rectify_photo.py data/captures/capture.jpg --output data/captures/rectified.png
```

Si la foto tiene mucho fondo, se puede combinar un recorte aproximado con la deteccion automatica:

```bash
python main_rx_photo.py data/captures/capture.jpg --crop 80,40,1100,700 --auto-perspective
```
