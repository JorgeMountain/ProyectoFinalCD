# Temas teoricos para la sustentacion

Este documento resume conceptos teoricos que pueden preguntar durante la sustentacion del modem optico
pantalla-camara. La idea es conectar la teoria de comunicaciones digitales con las decisiones tomadas en el codigo.

## 1. Que es un modem

Un modem es un sistema que modula y demodula informacion. En este proyecto:

- Modulador: convierte bits en niveles visuales de brillo.
- Canal: pantalla, ambiente y camara.
- Demodulador: convierte niveles capturados por la camara nuevamente en bits.

El sistema no transmite por radio ni por cable. Transmite informacion usando luz visible emitida por una pantalla.

## 2. Canal de comunicacion

Un canal es el medio por el que viaja la informacion. En este caso el canal incluye:

- pantalla del transmisor,
- distancia entre pantalla y camara,
- iluminacion del ambiente,
- enfoque de la camara,
- perspectiva,
- compresion o procesamiento interno de la camara,
- ruido electronico del sensor.

El canal no es ideal, por eso el receptor puede leer valores distintos a los que genero el transmisor.

Ejemplos de errores del canal:

- una celda blanca puede verse gris,
- una celda negra puede verse iluminada,
- una esquina puede quedar fuera de la imagen,
- un frame puede capturarse a medias,
- la camara puede saltarse frames si pasan muy rapido.

## 3. Modulacion digital

La modulacion es el proceso de representar bits usando una senal fisica. En este proyecto la senal fisica es el
brillo de cada celda visual.

### OOK

OOK significa On-Off Keying. Es una forma simple de ASK donde solo hay dos niveles:

```text
0 -> apagado u oscuro
1 -> encendido o claro
```

Ventajas:

- facil de implementar,
- robusta frente a ruido,
- decision simple con un umbral.

Desventajas:

- baja eficiencia espectral o baja cantidad de bits por simbolo,
- usa solo 1 bit por celda.

### 4-ASK

4-ASK usa cuatro niveles de amplitud. En el proyecto, la amplitud es brillo:

```text
nivel 0 -> 00
nivel 1 -> 01
nivel 2 -> 11
nivel 3 -> 10
```

Ventajas:

- transporta 2 bits por celda,
- necesita menos frames que OOK para el mismo mensaje.

Desventajas:

- mas sensible al ruido,
- necesita distinguir cuatro niveles en vez de dos,
- puede fallar si hay brillo irregular, desenfoque o compresion de camara.

## 4. Simbolo, bit y baudio

Un bit es una unidad binaria de informacion: 0 o 1.

Un simbolo es una forma fisica de representar informacion. En este proyecto, una celda de la grilla es un simbolo.

En OOK:

```text
1 simbolo = 1 bit
```

En 4-ASK:

```text
1 simbolo = 2 bits
```

Baudios es la tasa de simbolos por segundo. Bits por segundo depende de cuantos bits lleva cada simbolo:

```text
bps = baudios * bits_por_simbolo
```

Por eso 4-ASK puede tener mayor tasa util que OOK si la camara logra distinguir bien los niveles.

## 5. Mapeo Gray

El mapeo Gray ordena los simbolos para que niveles vecinos difieran en un solo bit.

En el proyecto:

```text
00, 01, 11, 10
```

Esto ayuda porque el error mas comun en 4-ASK es confundir un nivel con el nivel vecino. Con Gray, esa confusion
produce solo un bit errado en vez de dos.

## 6. Umbral de decision

El receptor debe decidir que bit o simbolo corresponde a cada celda capturada.

En OOK, la decision puede verse asi:

```text
si brillo >= umbral -> 1
si brillo < umbral  -> 0
```

En 4-ASK, el receptor compara el brillo con cuatro niveles de referencia y escoge el mas cercano.

El problema es que la camara no ve valores ideales. Por eso se usan pilotos de calibracion para estimar como se
estan viendo los niveles reales en ese momento.

## 7. Pilotos de calibracion

Los pilotos son celdas conocidas que no llevan informacion nueva. Sirven para que el receptor compare lo esperado
con lo recibido.

Funciones de los pilotos:

- estimar niveles de brillo,
- adaptar el umbral de decision,
- compensar cambios de iluminacion,
- mejorar demodulacion en OOK y 4-ASK.

Los pilotos reducen un poco la capacidad porque ocupan celdas que no transmiten datos, pero aumentan robustez.

## 8. Sincronizacion

La sincronizacion es saber donde empieza y termina la informacion.

En este proyecto hay varios niveles de sincronizacion:

- Espacial: detectar las cuatro esquinas de la pantalla.
- De grilla: saber donde cae cada celda.
- De paquete: leer numero de secuencia y total de paquetes.
- Temporal: repetir frames para que la camara tenga oportunidad de capturarlos.

No se usa sincronizacion por reloj compartido. La camara captura frames cuando puede, por eso se repite la secuencia.

## 9. Marcadores de esquina y perspectiva

La camara puede ver la pantalla inclinada. Si se leyera la grilla directamente, las celdas no coincidirian con su
posicion esperada.

Por eso se usan marcadores en las esquinas:

1. El receptor detecta las cuatro esquinas.
2. Calcula una transformacion de perspectiva.
3. Rectifica la imagen.
4. Lee la grilla como si estuviera de frente.

Este proceso es una homografia: transforma un cuadrilatero visto por la camara en un rectangulo normalizado.

## 10. Ruido

Ruido es cualquier perturbacion que cambia la senal recibida.

En este proyecto el ruido puede venir de:

- iluminacion ambiente,
- reflejos,
- desenfoque,
- movimiento,
- baja resolucion,
- compresion de video,
- exposicion automatica,
- balance de blancos,
- frecuencia de refresco de la pantalla.

El ruido puede causar errores de bit o paquetes invalidos.

## 11. BER

BER significa Bit Error Rate o tasa de error de bit.

Formula:

```text
BER = bits_errados / bits_totales
```

Ejemplo:

```text
1000 bits transmitidos
5 bits errados
BER = 5 / 1000 = 0.005
```

BER sirve para medir que tan confiable es el canal. Un BER menor significa mejor recepcion.

En el proyecto se puede calcular BER comparando el mensaje recibido contra el mensaje esperado.

## 12. Correccion de errores

La correccion de errores agrega redundancia para recuperar informacion aunque algunos bytes lleguen danados.

El proyecto usa Reed-Solomon, que trabaja a nivel de simbolos o bytes.

Regla practica:

```text
con N bytes de paridad se corrigen hasta N/2 bytes erroneos
```

Ejemplos:

```text
--ecc 16  -> corrige aprox 8 bytes
--ecc 32  -> corrige aprox 16 bytes
--ecc 64  -> corrige aprox 32 bytes
--ecc 128 -> corrige aprox 64 bytes
```

El mismo valor de ECC debe usarse en transmisor y receptor.

## 13. Redundancia vs eficiencia

Mas ECC aumenta robustez, pero tambien aumenta la cantidad de bytes transmitidos.

Consecuencia:

```text
mas ECC -> mas bytes -> mas paquetes -> mas tiempo de transmision
```

Por eso hay un compromiso:

- Poco ECC: transmision mas rapida, pero menos tolerante a errores.
- Mucho ECC: transmision mas robusta, pero mas larga.

Si la imagen es muy mala, subir ECC no siempre soluciona el problema. Primero hay que mejorar el canal:

- centrar la camara,
- aumentar `--duration-ms`,
- mejorar enfoque,
- reducir reflejos,
- usar OOK si 4-ASK falla.

## 14. Deteccion y paquetes invalidos

Un paquete puede ser invalido si:

- no aparece el identificador `OM`,
- la longitud no coincide,
- el numero de secuencia es imposible,
- la modulacion del paquete no coincide con la esperada,
- la imagen fue capturada borrosa o incompleta.

Por eso el receptor no acepta cualquier frame. Valida la cabecera antes de usarlo.

## 15. Multi-frame

Un solo frame tiene capacidad limitada. Para mensajes largos se divide el mensaje en varios paquetes.

Cada paquete tiene:

- numero de secuencia,
- total de paquetes,
- datos,
- bandera de fin.

Esto permite reconstruir el mensaje aunque los paquetes lleguen en distinto orden.

Formula:

```text
paquetes = ceil((bytes_mensaje + bytes_ECC) / capacidad_por_paquete)
```

Ejemplo con 4-ASK:

```text
500 bytes + 16 ECC = 516 bytes
516 / 123 = 4.19 -> 5 paquetes
```

Ejemplo con ECC alto:

```text
500 bytes + 128 ECC = 628 bytes
628 / 123 = 5.10 -> 6 paquetes
```

## 16. Throughput

Throughput es la tasa util de transmision.

Formula aproximada:

```text
throughput = bits_utiles / tiempo_total
```

El tiempo total depende de:

- numero de frames,
- duracion de cada frame,
- repeticiones.

Si un mensaje tiene 500 bytes:

```text
500 bytes = 4000 bits
```

Si tarda 2 segundos:

```text
throughput = 4000 / 2 = 2000 bps
```

## 17. Latencia

Latencia es el tiempo desde que empieza la transmision hasta que el receptor recupera el mensaje.

En el proyecto, la latencia depende de:

- cantidad de paquetes,
- `--duration-ms`,
- repeticiones necesarias,
- tiempo de procesamiento,
- correccion de errores,
- calidad de deteccion de camara.

## 18. Capacidad del canal

En teoria, la capacidad de canal indica la tasa maxima de informacion que se puede transmitir con cierta relacion
senal-ruido.

La idea relacionada con Shannon es:

```text
mas ruido -> menor capacidad confiable
```

En el proyecto se observa asi:

- con buena imagen, 4-ASK funciona bien y aumenta capacidad;
- con mala imagen, 4-ASK falla mas porque los niveles se confunden;
- OOK puede funcionar mejor porque solo distingue dos niveles.

## 19. Por que 4-ASK no siempre es mejor

4-ASK transmite mas bits por celda, pero necesita distinguir cuatro niveles. Si la camara no diferencia bien esos
niveles, aumenta la probabilidad de error.

OOK transmite menos, pero es mas robusto porque solo decide entre oscuro y claro.

Respuesta corta para sustentacion:

```text
4-ASK mejora eficiencia, pero reduce margen contra ruido. OOK reduce tasa, pero aumenta robustez.
```

## 20. Por que repetir frames

La camara no esta sincronizada con la pantalla. Si un frame dura poco, la camara puede no capturarlo o capturarlo
durante una transicion.

Repetir la secuencia ayuda porque:

- aumenta probabilidad de capturar cada paquete,
- permite votos por paquete,
- da oportunidad a ECC de corregir con mejores copias.

## 21. Votacion de paquetes

Cuando el receptor ve varias copias del mismo paquete, puede usar votos. Si una version aparece mas veces, se asume
que es mas confiable.

Ejemplo:

```text
Paquete 3/6 recibido (votos 4)
```

Significa que la version mas repetida del paquete 3 ha aparecido 4 veces.

La votacion ayuda a reducir errores aleatorios.

## 22. Modo mejor esfuerzo

El modo `--best-effort-after-seconds` permite entregar el mejor mensaje disponible si ya hay paquetes pero ECC no
logra corregir.

No garantiza texto perfecto. Sirve para pruebas cuando se quiere observar que tanto se recupero aunque el canal haya
sido ruidoso.

## 23. Preguntas probables y respuestas cortas

**Por que usan marcadores de esquina?**

Para detectar la pantalla en la imagen y corregir perspectiva antes de leer la grilla.

**Por que hay pilotos?**

Para calibrar niveles de brillo y adaptar la decision del receptor al canal real.

**Por que 4-ASK transmite mas rapido que OOK?**

Porque 4-ASK lleva 2 bits por celda, mientras OOK lleva 1 bit por celda.

**Por que 4-ASK falla mas facil?**

Porque debe distinguir cuatro niveles de brillo; si hay ruido, los niveles se confunden.

**Que hace Reed-Solomon?**

Agrega redundancia para corregir bytes erroneos en el receptor.

**Por que no poner ECC muy alto siempre?**

Porque aumenta bytes transmitidos, paquetes y tiempo. Hay un compromiso entre robustez y eficiencia.

**Que significa BER?**

Es la proporcion de bits recibidos incorrectamente respecto al total de bits transmitidos.

**Por que se divide en paquetes?**

Porque un frame tiene capacidad limitada y los mensajes largos necesitan varios frames.

**Que pasa si se pierde un paquete?**

El receptor no puede reconstruir completamente el mensaje hasta recibirlo o recibir una copia valida.

**Que pasa si ECC dice que no pudo corregir?**

Los errores superaron la capacidad de correccion o los paquetes recibidos estan demasiado danados.

**Por que repetir la transmision?**

Porque la camara puede saltarse frames y las repeticiones aumentan la probabilidad de recibir copias validas.

**Que es throughput?**

Es la cantidad de bits utiles recuperados por segundo.

**Que es latencia?**

Es el tiempo que tarda el sistema en recuperar el mensaje desde que inicia la recepcion.

**Que mejora mas la recepcion: subir ECC o bajar velocidad?**

Depende. Si hay pocos errores, subir ECC ayuda. Si la camara no captura bien los frames, bajar velocidad suele ayudar
mas.

## 24. Frase de cierre para la sustentacion

El proyecto demuestra un enlace digital visible pantalla-camara. La informacion se transforma en simbolos visuales,
se transmite por un canal optico ruidoso y se recupera mediante deteccion de grilla, demodulacion, paquetes,
votacion y correccion Reed-Solomon. La comparacion entre OOK y 4-ASK muestra el compromiso clasico entre robustez
y tasa de transmision.
