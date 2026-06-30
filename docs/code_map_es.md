# Mapa del codigo y puntos de modificacion

Este README sirve para responder preguntas del tipo: "donde se hace esto?", "que archivo modifico si quiero cambiar X?"
y "que puede pasar si cambio tal cosa?". Esta enfocado en los archivos `.py` mas importantes del proyecto.

## Resumen rapido por pregunta

**Donde cambio el tamano de la imagen o la grilla?**

`common/frame_config.py`

**Donde cambio que celdas son datos, pilotos o marcadores?**

`common/frame_layout.py`

**Donde cambio OOK o 4-ASK?**

`common/modulation.py`

**Donde se agrega o quita ECC?**

`common/ecc.py`, y se activa desde `main_tx_sequence.py` / `main_rx_video_sequence.py` con `--ecc`.

**Donde se define el formato de cada paquete?**

`common/packet.py`

**Donde se generan los frames del transmisor?**

`transmitter/generator.py` para un frame, `transmitter/sequence.py` para varios frames.

**Donde se detecta la pantalla en la camara?**

`receiver/perspective.py`

**Donde se leen las celdas y se demodula?**

`receiver/decoder.py`

**Donde se reciben paquetes por camara y se reconstruye el mensaje?**

`receiver/sequence_decoder.py`

**Donde estan los comandos principales?**

`main_tx_sequence.py` para emisor, `main_rx_video_sequence.py` para receptor.

## Archivos principales de entrada

### `main_tx_sequence.py`

Es el script principal del emisor multi-frame. Lee el mensaje, genera los frames y opcionalmente los muestra en
pantalla.

Se usa con comandos como:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 30
```

Que controla:

- `--message` y `--message-file`: texto a transmitir.
- `--ecc`: bytes de Reed-Solomon.
- `--modulation`: `ook` o `4ask`.
- `--show`: muestra la secuencia.
- `--duration-ms`: duracion de cada frame.
- `--repeat`: repeticiones de la secuencia.
- `--windowed`, `--window-width`, `--window-height`, `--window-x`, `--window-y`: ventana del transmisor.

Si modificas este archivo:

- Cambias la interfaz de uso del emisor.
- Puedes romper comandos que ya estan en los README.
- Si cambias defaults como `--duration-ms`, cambia la velocidad de transmision.
- Si cambias como se llama a `generate_frame_sequence`, puedes afectar todos los frames generados.

### `main_rx_video_sequence.py`

Es el script principal del receptor por camara. Abre la camara, llama al decodificador en vivo y muestra el resultado.

Se usa con comandos como:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0
```

Que controla:

- `--camera`: indice de camara.
- `--backend`: backend de OpenCV (`any`, `dshow`, `msmf`).
- `--scan-cameras`: prueba camaras disponibles.
- `--ecc`: debe coincidir con el emisor.
- `--modulation`: debe coincidir con el emisor.
- `--preview`: muestra vista previa.
- `--preview-window`: posicion y tamano de ventana.
- `--max-frames 0`: espera sin limite.
- `--best-effort-after-seconds`: entrega el mejor resultado si ECC falla.
- `--expected-message` o `--expected-message-file`: calcula BER.

Si modificas este archivo:

- Cambias la interfaz del receptor.
- Puedes afectar como se reporta BER.
- Puedes afectar `--scan-cameras`.
- Si cambias los argumentos enviados a `decode_video_stream`, puede cambiar la recepcion en vivo.

### `main_rx_sequence_offline.py`

Decodifica una carpeta de PNGs ya generados, sin camara. Sirve para validar que el protocolo funciona antes de probar
con camara real.

Uso tipico:

```powershell
python main_rx_sequence_offline.py --input-dir data/generated/sequence --ecc 16 --modulation 4ask --expected-file mensaje_500.txt
```

Si modificas este archivo:

- Cambias pruebas offline.
- Puedes afectar calculo de BER offline.
- No deberia afectar la camara directamente, pero si puede ocultar errores si el offline deja de validar bien.

### `main_analyze_performance.py`

Calcula metricas estimadas: cantidad de frames, tiempo, tasa util y muestras de camara por frame.

Uso tipico:

```powershell
python main_analyze_performance.py --message-file mensaje_500.txt --ecc 16 --modulation 4ask --duration-ms 500 --repeat 30
```

Si modificas este archivo:

- Cambias calculos de presentacion y estimacion.
- No cambia la transmision real, pero puede dar numeros incorrectos para la sustentacion.

### `main_tx_static.py`, `main_rx_offline.py`, `main_display_frame.py`, `main_capture_photo.py`, `main_rx_photo.py`, `main_rectify_photo.py`

Son scripts de etapas anteriores o pruebas individuales:

- `main_tx_static.py`: genera un solo frame estatico.
- `main_rx_offline.py`: decodifica un frame PNG estatico.
- `main_display_frame.py`: muestra un frame estatico en pantalla.
- `main_capture_photo.py`: captura una foto desde webcam.
- `main_rx_photo.py`: decodifica una foto.
- `main_rectify_photo.py`: guarda la imagen rectificada para inspeccion.

Si los modificas:

- Puedes afectar las pruebas por partes del proyecto.
- No necesariamente cambias el flujo multi-frame principal, pero si cambias funciones compartidas llamadas por ellos,
  puede afectar todo.

## Carpeta `common/`

Esta carpeta contiene la logica compartida. Si el profesor pregunta por la base teorica o el protocolo, normalmente
la respuesta apunta a esta carpeta.

### `common/frame_config.py`

Define la configuracion base de la imagen:

```text
image_width = 1280
image_height = 720
grid_cols = 32
grid_rows = 18
marker_cells = 3
pilot_cells = 8
```

Aqui se define el tamano de cada celda con:

```text
cell_width = image_width / grid_cols
cell_height = image_height / grid_rows
```

Si modificas este archivo:

- Cambia la geometria completa del sistema.
- El transmisor generara frames distintos.
- El receptor esperara una grilla distinta.
- Si cambias `grid_cols` o `grid_rows`, cambia la capacidad.
- Si cambias `marker_cells`, puede fallar la deteccion de esquinas.
- Si cambias `pilot_cells`, puede cambiar la calibracion y la capacidad.

Regla importante: emisor y receptor deben usar la misma configuracion.

### `common/frame_layout.py`

Define que celdas son:

- marcadores de esquina,
- pilotos,
- datos.

Funciones clave:

- `marker_origins`: posiciones de los cuatro marcadores.
- `marker_cells`: celdas reservadas para marcadores.
- `pilot_cells`: celdas reservadas para pilotos.
- `pilot_cells_with_symbols`: pilotos esperados para OOK o 4-ASK.
- `data_cells`: celdas que llevan informacion.
- `data_capacity_bits`: capacidad del frame.

Si modificas este archivo:

- Puedes cambiar donde estan los pilotos.
- Puedes cambiar cuantas celdas quedan para datos.
- Puedes romper la calibracion si el transmisor y receptor no coinciden.
- Puedes cambiar la cantidad de paquetes necesarios para un mensaje.

### `common/modulation.py`

Contiene las modulaciones digitales:

- `ook_modulate` y `ook_demodulate`.
- `ask4_modulate` y `ask4_demodulate`.
- `bits_per_symbol`.
- `modulation_id` y `modulation_from_id`.

Tambien define:

```text
MODULATION_CHOICES = ("ook", "4ask")
ASK4_LEVELS = (16, 96, 176, 245)
ASK4_BITS = ((0, 0), (0, 1), (1, 1), (1, 0))
```

Si modificas este archivo:

- Cambias como se convierten bits a brillo.
- Si cambias `ASK4_LEVELS`, el transmisor usara otros niveles de gris.
- Si cambias `ASK4_BITS`, cambias el mapeo Gray.
- Si cambias `modulation_id`, puedes romper compatibilidad con paquetes generados antes.
- Si agregas otra modulacion, tambien debes actualizar transmisor, receptor y tests.

### `common/packet.py`

Define el protocolo multi-frame. Cada frame lleva un paquete con:

```text
magic: "OM"
sequence
total_packets
payload_length
flags
modulation_id
payload
```

Funciones clave:

- `Packet`: estructura de un paquete.
- `packet_payload_capacity`: bytes utiles por frame.
- `encode_packet`: paquete -> bits.
- `decode_packet`: bits -> paquete.
- `split_payload`: divide el mensaje en chunks.

Si modificas este archivo:

- Cambias el formato del protocolo.
- Puedes romper compatibilidad entre emisor y receptor.
- Si aumentas la cabecera, baja la capacidad util por frame.
- Si quitas validaciones, el receptor podria aceptar paquetes corruptos.
- Si cambias `PACKET_HEADER_BYTES`, revisa todos los calculos de capacidad.

Este archivo responde preguntas como:

- "Donde se sabe que paquete es el 3 de 6?"
- "Donde se guarda la modulacion dentro del paquete?"
- "Donde se valida que la secuencia sea correcta?"

### `common/ecc.py`

Encapsula Reed-Solomon.

Funciones esperadas:

- codificar payload con paridad,
- decodificar payload recibido,
- reportar cuantos simbolos fueron corregidos.

Si modificas este archivo:

- Cambias la correccion de errores del sistema.
- Si cambias la forma de codificar, transmisor y receptor deben cambiar juntos.
- Si el valor `--ecc` no coincide entre emisor y receptor, la decodificacion puede fallar.

Pregunta tipica:

```text
Con N bytes de ECC se corrigen aproximadamente N/2 bytes erroneos.
```

### `common/bit_utils.py`

Contiene utilidades para conversion:

- texto a bits,
- bits a texto,
- bytes a bits,
- bits a bytes,
- prefijo de longitud para frames estaticos.

Si modificas este archivo:

- Puedes romper la conversion base de informacion.
- Afecta tanto transmisor como receptor.
- Un error aqui puede cambiar todos los mensajes, incluso si la camara funciona bien.

### `common/metrics.py`

Calcula errores y BER.

Sirve para comparar mensaje esperado contra mensaje recibido.

Si modificas este archivo:

- Cambia como se reportan errores.
- No cambia la transmision, pero puede cambiar las metricas de evaluacion.

### `common/performance.py`

Calcula estimaciones de rendimiento:

- frames necesarios,
- tiempo estimado,
- throughput,
- muestras de camara por frame.

Si modificas este archivo:

- Cambian los valores que se muestran en analisis.
- No cambia directamente la transmision real.
- Puede afectar argumentos durante la sustentacion si da estimaciones incorrectas.

### `common/png_writer.py` y `common/png_reader.py`

Manejan lectura y escritura de imagenes PNG en escala de grises.

Si modificas estos archivos:

- Puedes afectar generacion offline de frames.
- Puedes afectar pruebas offline.
- Si cambias formato o dimensiones, el receptor puede rechazar imagenes.

## Carpeta `transmitter/`

Contiene la logica del emisor.

### `transmitter/generator.py`

Genera un frame visual a partir de bits.

Funciones clave:

- `message_to_frame_bits`: texto -> bits con prefijo y ECC para modo estatico.
- `build_frame_grid`: crea la grilla con marcadores, pilotos y datos.
- `render_grid_to_pixels`: convierte celdas en pixeles.
- `generate_static_frame`: guarda un frame PNG.
- `_place_markers`: dibuja marcadores.
- `_place_pilots`: dibuja pilotos.
- `_place_data`: coloca datos modulados.

Si modificas este archivo:

- Cambias como se ve cada frame.
- Si cambias marcadores, puede fallar `receiver/perspective.py`.
- Si cambias pilotos, puede fallar `receiver/calibration.py`.
- Si cambias niveles de datos, puede afectar OOK/4-ASK.
- Si cambias la ubicacion de datos, debe coincidir con `common/frame_layout.py`.

Pregunta tipica:

```text
Donde se pintan las celdas claras/oscuras?
```

Respuesta: en `transmitter/generator.py`, especialmente `_place_data`, `_place_pilots` y `_place_markers`.

### `transmitter/sequence.py`

Genera y muestra transmisiones multi-frame.

Funciones clave:

- `generate_frame_sequence`: mensaje -> varios PNG.
- `display_frame_sequence`: muestra los frames en pantalla.
- `colorize_corner_markers`: colorea marcadores para facilitar deteccion en camara.

Si modificas este archivo:

- Cambias la transmision multi-frame principal.
- Si cambias `generate_frame_sequence`, cambia como se divide el mensaje.
- Si cambias `display_frame_sequence`, cambia la visualizacion en pantalla.
- Si cambias `colorize_corner_markers`, puede afectar deteccion de esquinas de color.
- Si cambias `frame_duration_ms`, cambia la velocidad percibida por la camara.

Pregunta tipica:

```text
Donde se repiten los frames?
```

Respuesta: en `display_frame_sequence`, dentro de los ciclos por `repeat` y por cada `frame_path`.

## Carpeta `receiver/`

Contiene la logica del receptor.

### `receiver/decoder.py`

Lee una imagen ya rectificada y extrae bits.

Funciones clave:

- `decode_static_frame`: decodifica un PNG estatico.
- `decode_static_pixels`: decodifica pixeles en memoria.
- `decode_data_bits`: lee celdas y demodula.
- `sample_grid_levels`: promedia el brillo de cada celda.

Si modificas este archivo:

- Cambias como se leen las celdas.
- Si cambias `sample_grid_levels`, cambias la forma de medir brillo.
- Si reduces margenes de muestreo, puedes leer bordes contaminados.
- Si cambias demodulacion, puedes afectar OOK y 4-ASK.
- Si cambias validacion de marcadores, podrian pasar frames incorrectos.

Pregunta tipica:

```text
Donde se decide si una celda es 0 o 1?
```

Respuesta: en `decode_data_bits`, llamando a `ook_demodulate` o `ask4_demodulate`.

### `receiver/calibration.py`

Estima umbrales y niveles usando pilotos y valida marcadores.

Funciones clave:

- `estimate_ook_calibration`: calcula umbral OOK con pilotos blanco/negro.
- `estimate_ask4_calibration`: calcula niveles para 4-ASK.
- `validate_markers`: revisa que los marcadores tengan el patron esperado.

Si modificas este archivo:

- Cambias como se adapta el receptor a brillo real.
- Si el umbral queda mal, OOK falla.
- Si los niveles de 4-ASK quedan mal, se confunden simbolos.
- Si `validate_markers` es muy estricto, rechaza frames buenos.
- Si `validate_markers` es muy permisivo, acepta frames malos.

### `receiver/perspective.py`

Detecta las esquinas de la pantalla y corrige perspectiva.

Funciones clave:

- `detect_colored_frame_corners`: detecta marcadores de color.
- `rectify_frame_image_from_corners`: aplica homografia.
- `rectify_frame_image`: flujo automatico para imagen en escala de grises.
- `debug_colored_marker_detection`: ayuda a diagnosticar deteccion.

Si modificas este archivo:

- Cambias la deteccion de pantalla.
- Si subes demasiado el area minima de candidatos, puede no detectar esquinas lejanas.
- Si bajas demasiado el area minima, puede detectar ruido.
- Si cambias la seleccion de esquinas, puede rectificar mal.
- Si la homografia queda mal, todo el frame se lee desplazado.

Pregunta tipica:

```text
Donde se corrige la imagen inclinada?
```

Respuesta: en `rectify_frame_image_from_corners`, usando `cv2.getPerspectiveTransform` y `cv2.warpPerspective`.

### `receiver/sequence_decoder.py`

Es el receptor multi-frame mas importante. Une camara, deteccion, paquetes, votacion, ECC y resultado final.

Funciones clave:

- `decode_packet_from_pixels`: frame rectificado -> paquete.
- `decode_packet_from_image`: PNG -> paquete.
- `decode_sequence_folder`: carpeta de PNGs -> mensaje.
- `assemble_packets`: lista de paquetes -> mensaje.
- `decode_video_stream`: camara/video/pantalla -> mensaje.
- `_assemble_packet_candidates`: prueba candidatos cuando ECC falla.
- `_assemble_best_effort`: entrega mejor esfuerzo si se activa timeout.
- `_open_capture`: abre camara, URL o captura de pantalla.
- `_show_window` y `_show_decode_preview`: ventanas de preview.

Si modificas este archivo:

- Puedes afectar directamente la prueba en vivo.
- Si cambias `decode_video_stream`, cambia la recepcion por camara.
- Si cambias `assemble_packets`, cambia reconstruccion offline y en vivo.
- Si cambias votacion, puede mejorar o empeorar robustez.
- Si cambias limite de reintentos, puede volver el lag cuando falla ECC.
- Si cambias preview, solo afecta visualizacion salvo que bloquees el loop de camara.

Preguntas tipicas:

```text
Donde se imprime "Paquete 3/6 recibido"?
```

Respuesta: en `decode_video_stream`, cuando se recibe un paquete valido.

```text
Donde se corrige con ECC?
```

Respuesta: en `assemble_packets`, llamando a `decode_reed_solomon`.

```text
Donde se evita el lag cuando ECC falla?
```

Respuesta: en `_assemble_packet_candidates`, `_bounded_candidate_combinations` y el control de reintentos en
`decode_video_stream`.

```text
Donde se cierra con q?
```

Respuesta: en `decode_video_stream`, con `cv2.waitKey(1)` cuando hay preview.

### `receiver/photo_decoder.py`

Contiene ayudas para decodificar fotos y parsear recortes.

Funcion importante:

- `parse_crop`: interpreta texto `x,y,width,height`.

Si modificas este archivo:

- Puedes afectar `--crop`, `--screen-crop` y `--preview-window`.
- Si parsea mal, los recortes y ventanas pueden ubicarse incorrectamente.

## Tests

La carpeta `tests/` protege el comportamiento del proyecto.

Archivos importantes:

- `tests/test_part1.py`: conversiones basicas.
- `tests/test_part2.py`: generacion de frame.
- `tests/test_part3.py`: decodificacion offline.
- `tests/test_part4.py`: pilotos y marcadores.
- `tests/test_part5.py`: foto/captura.
- `tests/test_part6.py`: perspectiva.
- `tests/test_part7.py`: ECC.
- `tests/test_part8.py`: multi-frame, 4-ASK, video simulado y reintentos.
- `tests/test_part9.py`: BER y performance.

Si modificas codigo importante, corre:

```powershell
python -m pytest tests
```

Si falla un test:

- No significa siempre que el cambio este mal.
- Pero si significa que cambiaste un contrato esperado.
- Debes actualizar codigo o test con una justificacion clara.

## Cambios comunes y donde hacerlos

### Cambiar velocidad de transmision

Archivo principal:

`main_tx_sequence.py`

Parametro:

```powershell
--duration-ms
```

Riesgo:

- Si es muy bajo, la camara salta frames.
- Si es muy alto, baja throughput.

### Cambiar robustez ECC

No hace falta editar codigo. Se cambia por comando:

```powershell
--ecc 16
--ecc 64
--ecc 128
```

Riesgo:

- Debe coincidir en emisor y receptor.
- Mas ECC aumenta paquetes y tiempo.

### Cambiar de OOK a 4-ASK

No hace falta editar codigo. Se cambia por comando:

```powershell
--modulation ook
--modulation 4ask
```

Riesgo:

- 4-ASK transmite mas, pero falla mas facil con mala imagen.
- Emisor y receptor deben coincidir.

### Cambiar cantidad de paquetes

Archivos relacionados:

- `common/packet.py`
- `common/frame_config.py`
- `common/frame_layout.py`
- `common/modulation.py`

Tambien cambia con:

- tamano del mensaje,
- valor de `--ecc`,
- modulacion.

Riesgo:

- Cambiar capacidad afecta calculos de performance.
- Puede romper comandos o expectativas del README.

### Cambiar deteccion de esquinas

Archivo:

`receiver/perspective.py`

Riesgo:

- Puede mejorar deteccion en tu camara.
- Pero tambien puede aceptar falsos positivos o dejar de detectar.

### Cambiar tamano de ventanas de preview

Archivos:

- `main_rx_video_sequence.py`
- `receiver/sequence_decoder.py`

Tambien se puede cambiar por comando:

```powershell
--preview-window x,y,width,height
```

Riesgo:

- Normalmente solo afecta visualizacion.
- Si se hace muy grande, puede incomodar la prueba.

### Cambiar niveles de 4-ASK

Archivo:

`common/modulation.py`

Constante:

```text
ASK4_LEVELS
```

Riesgo:

- Niveles muy cercanos aumentan errores.
- Niveles extremos pueden saturarse en camara.
- Debe seguir existiendo calibracion compatible en receptor.

### Cambiar pilotos

Archivos:

- `common/frame_layout.py`
- `transmitter/generator.py`
- `receiver/calibration.py`

Riesgo:

- Si transmisor y receptor no esperan los mismos pilotos, la calibracion falla.
- Mas pilotos mejora calibracion pero reduce capacidad.

### Cambiar marcadores de esquina

Archivos:

- `common/frame_layout.py`
- `transmitter/generator.py`
- `transmitter/sequence.py`
- `receiver/perspective.py`
- `receiver/calibration.py`

Riesgo:

- Puede fallar deteccion de pantalla.
- Puede fallar validacion de marcadores.
- Afecta directamente pruebas con camara.

## Guia para responder al profesor

**Profesor: Donde se define la grilla?**

En `common/frame_config.py`, con `image_width`, `image_height`, `grid_cols` y `grid_rows`.

**Profesor: Donde se codifica el texto?**

Para multi-frame, en `transmitter/sequence.py`, dentro de `generate_frame_sequence`, donde el mensaje pasa a bytes,
se aplica ECC y se divide en paquetes.

**Profesor: Donde se define el paquete?**

En `common/packet.py`, con la clase `Packet` y las funciones `encode_packet` / `decode_packet`.

**Profesor: Donde esta la modulacion?**

En `common/modulation.py`. OOK usa dos niveles; 4-ASK usa cuatro niveles y mapeo Gray.

**Profesor: Donde se detecta la pantalla?**

En `receiver/perspective.py`, especialmente `detect_colored_frame_corners`.

**Profesor: Donde se corrige perspectiva?**

En `receiver/perspective.py`, con `rectify_frame_image_from_corners`.

**Profesor: Donde se leen los bits de una imagen?**

En `receiver/decoder.py`, con `sample_grid_levels` y `decode_data_bits`.

**Profesor: Donde se reconstruye el mensaje?**

En `receiver/sequence_decoder.py`, con `assemble_packets`.

**Profesor: Donde se aplica Reed-Solomon?**

Se codifica en `transmitter/sequence.py` llamando a `encode_reed_solomon`, y se decodifica en
`receiver/sequence_decoder.py` dentro de `assemble_packets`, llamando a `decode_reed_solomon`.

**Profesor: Donde se calcula BER?**

En `common/metrics.py`, y se usa desde `main_rx_video_sequence.py` o `main_rx_sequence_offline.py`.

**Profesor: Donde se controla el tiempo de cada frame?**

En `main_tx_sequence.py` con `--duration-ms`, que llega a `display_frame_sequence` en `transmitter/sequence.py`.

**Profesor: Donde se evita que la camara se congele cuando falla ECC?**

En `receiver/sequence_decoder.py`, limitando combinaciones de candidatos y evitando recalcular si no llegaron copias
distintas.

## Recomendacion antes de modificar

Antes de tocar un archivo compartido, preguntarse:

1. Esto afecta solo visualizacion o afecta el protocolo?
2. El receptor y transmisor siguen usando la misma configuracion?
3. Cambia la capacidad por frame?
4. Cambia la forma de los paquetes?
5. Cambia la forma de demodular?
6. Hay tests que cubran el cambio?

Despues de modificar:

```powershell
python -m pytest tests
```

Si el cambio afecta camara real, ademas hacer una prueba con:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0
```

y en otra terminal:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 20
```
