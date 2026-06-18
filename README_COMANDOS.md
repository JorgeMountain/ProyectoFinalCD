# Comandos de prueba para emisor y receptor

Este README reune los comandos mas utiles para probar el modem optico. La regla mas importante es que emisor y
receptor deben usar los mismos valores de:

```text
--ecc
--modulation
```

## 1. Preparacion

Entrar a la carpeta del proyecto:

```powershell
cd C:\Users\USUARIO\Desktop\ProyectoFinalCD
```

Instalar dependencias si es necesario:

```powershell
pip install -r requirements.txt
```

Verificar que las pruebas pasan:

```powershell
python -m pytest tests
```

## 2. Buscar indice de camara

Antes de recibir, identificar que numero tiene la camara:

```powershell
python main_rx_video_sequence.py --scan-cameras --scan-max 6 --backend dshow
```

Si la camara 0 no abre, probar 1, 2, 3, etc. En Windows normalmente funciona mejor:

```text
--backend dshow
```

## 3. Prueba rapida 4-ASK con mensaje corto

Terminal 1, receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0
```

Terminal 2, emisor:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 20
```

## 4. Prueba rapida OOK con mensaje corto

Terminal 1, receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation ook --preview --max-frames 0
```

Terminal 2, emisor:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation ook --show --duration-ms 500 --repeat 20
```

OOK es mas lento, pero suele ser mas robusto que 4-ASK.

## 5. Prueba con archivo de 500 caracteres

Si tienes un archivo `mensaje_500.txt`, usar:

Terminal 1, receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation 4ask --preview --max-frames 0 --best-effort-after-seconds 10 --expected-message-file mensaje_500.txt
```

Terminal 2, emisor:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --show --duration-ms 500 --repeat 30
```

Si falla mucho ECC, probar con mas tiempo por frame:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --show --duration-ms 700 --repeat 30
```

## 6. Prueba con ECC alto

Usar el mismo ECC en ambos lados.

Terminal 1, receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 128 --modulation 4ask --preview --max-frames 0 --best-effort-after-seconds 10 --expected-message-file mensaje_500.txt
```

Terminal 2, emisor:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 128 --modulation 4ask --show --duration-ms 500 --repeat 30
```

Nota: mas ECC corrige mas errores, pero tambien agrega bytes y puede aumentar la cantidad de paquetes.

## 7. Prueba con ventana del transmisor

Si no quieres pantalla completa, usar `--windowed`:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --show --windowed --window-width 900 --window-height 506 --window-x 20 --window-y 100 --duration-ms 500 --repeat 30
```

Esto ayuda si quieres ver la terminal y el transmisor al mismo tiempo.

## 8. Receptor con ventana pequena o reposicionada

Por defecto las ventanas del receptor salen pequenas y centradas. Si quieres controlar posicion y tamano:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation 4ask --preview --max-frames 0 --preview-window 420,60,520,292
```

Formato:

```text
x,y,ancho,alto
```

## 9. Receptor con BER

BER compara el mensaje recibido contra el mensaje esperado.

Con mensaje directo:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0 --expected-message "Hola mundo"
```

Con archivo:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation 4ask --preview --max-frames 0 --expected-message-file mensaje_500.txt
```

Si todo salio perfecto, deberia mostrar:

```text
Errores de bit: 0
Tasa de error (BER): 0
```

## 10. Decodificacion offline sin camara

Sirve para validar que el codigo funciona sin depender de la camara.

Generar frames:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask
```

Decodificar carpeta:

```powershell
python main_rx_sequence_offline.py --input-dir data/generated/sequence --ecc 16 --modulation 4ask --expected "Hola mundo"
```

Con archivo:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 16 --modulation 4ask
python main_rx_sequence_offline.py --input-dir data/generated/sequence --ecc 16 --modulation 4ask --expected-file mensaje_500.txt
```

## 11. Analizar rendimiento antes de transmitir

Ver cantidad de frames, tiempo estimado y throughput:

```powershell
python main_analyze_performance.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --duration-ms 500 --repeat 30
```

Comparar OOK:

```powershell
python main_analyze_performance.py --message-file mensaje_500.txt --ecc 64 --modulation ook --duration-ms 500 --repeat 30
```

## 12. Comandos recomendados para sustentacion

### Demostracion corta y estable

Receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 16 --modulation 4ask --preview --max-frames 0 --expected-message "Hola mundo"
```

Emisor:

```powershell
python main_tx_sequence.py --message "Hola mundo" --ecc 16 --modulation 4ask --show --duration-ms 500 --repeat 20
```

### Demostracion de 500 caracteres

Receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation 4ask --preview --max-frames 0 --best-effort-after-seconds 10 --expected-message-file mensaje_500.txt
```

Emisor:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation 4ask --show --duration-ms 500 --repeat 30
```

### Si 4-ASK falla, probar OOK

Receptor:

```powershell
python main_rx_video_sequence.py --camera 2 --backend dshow --ecc 64 --modulation ook --preview --max-frames 0 --best-effort-after-seconds 10 --expected-message-file mensaje_500.txt
```

Emisor:

```powershell
python main_tx_sequence.py --message-file mensaje_500.txt --ecc 64 --modulation ook --show --duration-ms 500 --repeat 30
```

## 13. Como cerrar

En las ventanas de OpenCV:

```text
q
```

Tambien puede funcionar:

```text
Esc
```

Si no responde, cortar desde la terminal:

```powershell
Ctrl + C
```

## 14. Problemas comunes

### La camara no abre

Probar otro indice:

```powershell
python main_rx_video_sequence.py --camera 0 --backend dshow --preview --max-frames 0
python main_rx_video_sequence.py --camera 1 --backend dshow --preview --max-frames 0
python main_rx_video_sequence.py --camera 2 --backend dshow --preview --max-frames 0
```

O volver a escanear:

```powershell
python main_rx_video_sequence.py --scan-cameras --scan-max 6 --backend dshow
```

### Dice "Buscando 4 esquinas de color"

El receptor no ve bien las esquinas del transmisor. Revisar:

- que la pantalla completa este dentro de la camara,
- que no haya reflejos fuertes,
- que no este demasiado inclinado,
- que los marcadores de esquina sean visibles.

### Dice "Frame visto, pero bits/paquete no validos"

La pantalla se ve, pero la grilla no se esta leyendo bien. Probar:

- enfocar mejor,
- aumentar `--duration-ms`,
- acercar o alejar la camara,
- usar OOK,
- mejorar iluminacion.

### Dice "ECC no pudo corregir"

El receptor recibio paquetes, pero algunos llegaron con demasiados errores. Probar:

```powershell
--duration-ms 700
```

o subir ECC en ambos lados:

```powershell
--ecc 128
```

### Salen mas paquetes de los esperados

La cantidad de paquetes depende de:

```text
bytes_mensaje + bytes_ECC
```

Ejemplo:

```text
500 bytes con 4-ASK y ecc 16  -> 5 paquetes aprox
500 bytes con 4-ASK y ecc 128 -> 6 paquetes aprox
```

## 15. Regla de oro

Para que funcione bien:

```text
mismo --ecc
mismo --modulation
frames suficientemente lentos
pantalla completa visible
buena deteccion de esquinas
```
