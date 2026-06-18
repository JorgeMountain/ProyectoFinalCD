# Guia de sustentacion del modem optico pantalla-camara

Este documento explica como funciona el codigo del proyecto y sirve como guia para sustentar la implementacion.
El sistema implementa un modem optico: el transmisor convierte texto en frames visuales mostrados en una pantalla,
y el receptor usa una camara para capturar esos frames y reconstruir el mensaje original.

## Idea general

El proyecto transmite informacion usando cambios de brillo en una grilla visual. Cada frame es una imagen de
`1280x720` pixeles dividida en una matriz de `32x18` celdas. Algunas celdas no llevan datos porque se reservan
para marcadores de esquina y pilotos de calibracion. El resto de celdas transporta bits o simbolos.

Flujo completo:

```text
mensaje de texto
-> bytes UTF-8
-> correccion Reed-Solomon opcional
-> division en paquetes
-> bits del paquete
-> modulacion visual OOK o 4-ASK
-> frames PNG
-> pantalla
-> camara
-> deteccion de esquinas y rectificacion
-> demodulacion
-> reconstruccion de paquetes
-> correccion de errores
-> texto recuperado
```

## Estructura del codigo

El codigo esta separado por responsabilidades:

- `common/`: funciones compartidas entre emisor y receptor.
- `transmitter/`: genera los frames y los muestra en pantalla.
- `receiver/`: lee imagenes o camara, detecta la pantalla y decodifica paquetes.
- `main_*.py`: scripts ejecutables para probar cada parte.
- `tests/`: pruebas automaticas del protocolo, modulacion, ECC, transmision multi-frame y metricas.

Los archivos mas importantes son:

- `common/frame_config.py`: define tamano de imagen, grilla, marcadores y pilotos.
- `common/modulation.py`: contiene OOK y 4-ASK.
- `common/packet.py`: define el protocolo de paquetes multi-frame.
- `common/ecc.py`: integra Reed-Solomon para correccion de errores.
- `transmitter/sequence.py`: genera una secuencia de frames para mensajes largos.
- `receiver/sequence_decoder.py`: recibe frames desde carpeta, video o camara y reconstruye el mensaje.
- `main_tx_sequence.py`: script principal del emisor multi-frame.
- `main_rx_video_sequence.py`: script principal del receptor por camara.

## Configuracion visual del frame

La configuracion base esta en `common/frame_config.py`:

```text
imagen: 1280x720
grilla: 32 columnas x 18 filas
marcadores: 4 esquinas
pilotos: 8 celdas
```

Los marcadores de esquina permiten detectar la pantalla dentro de la imagen de la camara. Luego el receptor aplica
una correccion de perspectiva para convertir la imagen inclinada o tomada desde un angulo en una imagen rectangular
normalizada. Los pilotos ayudan a estimar niveles de brillo reales, lo cual es importante porque la camara no ve
exactamente los mismos valores que genera la pantalla.

## Modulaciones implementadas

El proyecto soporta dos modulaciones visuales.

### OOK

OOK significa On-Off Keying. Cada celda transporta 1 bit:

```text
0 -> celda oscura
1 -> celda clara
```

Es mas robusta porque solo distingue dos niveles de brillo, pero transporta menos informacion por frame.

### 4-ASK

4-ASK usa cuatro niveles de gris. Cada celda transporta 2 bits:

```text
00, 01, 11, 10
```

Usa mapeo Gray para que niveles cercanos solo cambien un bit. Es mas eficiente que OOK, pero tambien mas sensible
a iluminacion, enfoque, reflejos y compresion de la camara.

Capacidad aproximada con la grilla actual:

```text
OOK:   56 bytes utiles por frame
4-ASK: 123 bytes utiles por frame
```

Por eso un mensaje de 500 bytes con `--ecc 16` requiere aproximadamente:

```text
OOK:   10 frames
4-ASK: 5 frames
```

Si se aumenta mucho el ECC, pueden aparecer mas frames porque se transmiten mas bytes.

## Protocolo de paquetes

Cada frame no lleva solamente texto. Lleva un paquete con cabecera y payload. La cabecera esta definida en
`common/packet.py` y contiene:

- identificador del protocolo (`OM`),
- numero de secuencia del paquete,
- total de paquetes,
- longitud del payload,
- bandera de fin,
- modulacion usada.

Esto permite que el receptor sepa que paquete recibio, cuantos faltan y si el frame pertenece a OOK o 4-ASK.
Tambien permite reconstruir el mensaje aunque los paquetes lleguen en desorden.

Formula simplificada de cantidad de paquetes:

```text
paquetes = ceil((bytes_mensaje + bytes_ECC) / bytes_utiles_por_frame)
```

Ejemplo con 4-ASK:

```text
500 bytes / 123 bytes por frame = 4.06 -> 5 paquetes
```

Si se usa `--ecc 128`:

```text
(500 + 128) / 123 = 5.10 -> 6 paquetes
```

## Correccion de errores Reed-Solomon

La opcion `--ecc` agrega bytes de paridad Reed-Solomon antes de dividir el mensaje en paquetes. El mismo valor de
ECC debe usarse en emisor y receptor.

Regla practica:

```text
--ecc 16  corrige aprox 8 bytes danados
--ecc 32  corrige aprox 16 bytes danados
--ecc 64  corrige aprox 32 bytes danados
--ecc 128 corrige aprox 64 bytes danados
```

Mas ECC no siempre significa mejor resultado. Aumentar ECC tambien aumenta los bytes transmitidos, lo cual puede
crear mas paquetes y hacer mas larga la transmision. Si la imagen esta borrosa, cortada o con mala perspectiva,
subir ECC no soluciona la causa principal.

## Funcionamiento del transmisor

El transmisor principal es `main_tx_sequence.py`.

Pasos internos:

1. Lee el mensaje desde `--message` o `--message-file`.
2. Convierte el texto a bytes UTF-8.
3. Si `--ecc` es mayor que cero, agrega paridad Reed-Solomon.
4. Divide los bytes en chunks segun la capacidad de la modulacion.
5. Crea un `Packet` por cada chunk.
6. Codifica el paquete a bits.
7. Modula los bits como OOK o 4-ASK.
8. Renderiza cada frame como PNG.
9. Si se usa `--show`, muestra los frames en pantalla.

Comando tipico para transmitir:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 30
```

Parametros importantes:

- `--modulation ook` o `--modulation 4ask`: selecciona modulacion.
- `--ecc`: bytes de correccion de errores.
- `--duration-ms`: tiempo que cada frame queda en pantalla.
- `--repeat`: cuantas veces se repite la secuencia completa.
- `--windowed`: muestra en ventana en vez de pantalla completa.

## Funcionamiento del receptor

El receptor principal por camara es `main_rx_video_sequence.py`.

Pasos internos:

1. Abre la camara indicada con `--camera`.
2. Captura frames continuamente.
3. Detecta las cuatro esquinas de color del transmisor.
4. Rectifica la perspectiva para obtener una imagen normalizada.
5. Lee las celdas de la grilla.
6. Demodula OOK o 4-ASK.
7. Decodifica el paquete.
8. Guarda votos por paquete recibido.
9. Cuando tiene todos los paquetes, intenta ensamblar el mensaje.
10. Si hay ECC, intenta corregir errores.
11. Imprime mensaje, paquetes recibidos, bytes, simbolos corregidos y tiempo.

Comando tipico para recibir:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0
```

Parametros importantes:

- `--camera`: indice de la camara.
- `--backend dshow`: backend recomendado en Windows para camaras USB o virtuales.
- `--preview`: muestra ventanas de vista previa.
- `--max-frames 0`: espera sin limite hasta decodificar o cancelar.
- `--best-effort-after-seconds`: entrega el mejor mensaje posible si ECC falla despues de cierto tiempo.
- `--expected-message` o `--expected-message-file`: permite calcular BER contra el mensaje original.

## Votacion y recuperacion en recepcion en vivo

En camara real, el receptor puede leer varias copias del mismo paquete. El codigo guarda votos por secuencia.
Si recibe varias versiones del paquete 3, por ejemplo, conserva la version mas repetida y tambien puede probar
candidatos alternativos cuando ECC falla.

Para evitar lag, el receptor limita los reintentos pesados:

```text
maximo de combinaciones probadas: 96
```

Si ECC falla y no llegan paquetes nuevos o distintos, el receptor no repite el mismo calculo costoso en cada frame.
Esto mantiene la camara mas fluida mientras espera mejores copias.

## BER y metricas

BER significa Bit Error Rate o tasa de error de bit. El proyecto puede comparar el mensaje recibido contra un mensaje
esperado y contar errores.

Ejemplo:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0 --expected-message-file mensaje_500.txt
```

La salida puede incluir:

```text
Errores de bit: 0
Tasa de error (BER): 0
```

Tambien existe `main_analyze_performance.py`, que estima frames necesarios, duracion de transmision, tasa util y
muestras de camara por frame.

## Comandos recomendados para demostracion

Primero, identificar la camara:

```powershell
python main_rx_video_sequence.py --scan-cameras --scan-max 6 --backend dshow
```

Prueba corta con 4-ASK:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0
```

En otra terminal:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 20
```

Prueba de 500 caracteres:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation 4ask --preview --max-frames 0 --best-effort-after-seconds 10 --expected-message-file mensaje_500.txt
```

En otra terminal:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --show --duration-ms 500 --repeat 30
```

## Como interpretar mensajes de consola

Cuando aparece:

```text
Paquete 3/6 recibido (votos 2)
```

significa que el receptor recibio el paquete 3 de una transmision de 6 paquetes, y que la version mas repetida de
ese paquete lleva 2 votos.

Cuando aparece:

```text
ECC no pudo corregir la secuencia. Esperando otra copia de los paquetes.
```

significa que ya hay paquetes suficientes, pero algunos bytes estan danados y Reed-Solomon todavia no puede
recuperar el mensaje. El receptor sigue esperando mejores copias.

Cuando aparece:

```text
Simbolos corregidos: 78
```

significa que Reed-Solomon corrigio errores y aun asi logro recuperar el mensaje.

## Puntos clave para sustentar

- El proyecto es un canal optico pantalla-camara, no usa red ni cable de datos.
- La informacion se codifica como brillo en celdas de una grilla.
- OOK prioriza robustez; 4-ASK prioriza capacidad.
- Los marcadores de esquina permiten detectar y rectificar la pantalla.
- Los pilotos ayudan a compensar cambios de brillo de la camara.
- Reed-Solomon agrega redundancia para corregir errores reales del canal.
- El protocolo de paquetes permite transmitir mensajes mas largos que un solo frame.
- La recepcion en vivo usa votos y reintentos acotados para manejar lecturas ruidosas.
- El valor de ECC debe coincidir en emisor y receptor.
- Aumentar ECC ayuda hasta cierto punto, pero tambien aumenta la cantidad de bytes y paquetes.

## Limitaciones conocidas

- La camara debe ver la pantalla completa y con las cuatro esquinas detectables.
- 4-ASK es sensible a brillo, desenfoque y compresion.
- Si los frames pasan demasiado rapido, la camara puede saltarse paquetes.
- Si la pantalla esta inclinada o reflejada, la deteccion puede fallar.
- Subir ECC no corrige problemas de captura severos; en esos casos conviene bajar velocidad, centrar la camara o usar OOK.

## Verificacion del proyecto

Para correr todas las pruebas:

```powershell
python -m pytest tests
```

La ultima validacion del proyecto paso con:

```text
59 passed
```
