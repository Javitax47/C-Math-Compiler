# Compilador C a Ecuación (Project Diophantus)

> **"Cualquier problema computable puede ser representado por una ecuación diofántica."**

Este proyecto es un experimento de "compilador" teórico que intenta demostrar la profunda conexión entre la informática y las matemáticas.

El objetivo es tomar un programa sencillo escrito en un subconjunto de C (como un juego de Pong) y traducirlo a una única y masiva **ecuación polinómica** $P(vars...) = 0$, basada en el Teorema de Matiyasevich (MRDP).

Una vez que tengamos esta ecuación, una **solución entera** a esa ecuación representa una **ejecución válida** completa del programa original.

## ¿Qué es esto? La Teoría

Este compilador no genera código máquina (Assembly) ni WebAssembly. Genera una expresión matemática estática que es lógicamente equivalente al programa procedural.

Esto se logra en dos fases:

1.  **Fase 1: Análisis (Parsing)**
    No reinventamos la rueda. Usamos **`libclang`** para analizar el código C fuente. `libclang` es el frontend del compilador Clang/LLVM, lo que nos da un **Árbol de Sintaxis Abstracta (AST)** perfecto y robusto. Esto nos permite entender la gramática de C (precedencia de operadores, `e = -e;`, `b++;`, etc.) sin tener que escribir un parser de C nosotros mismos.

2.  **Fase 2: Generación (El "Aplanador")**
    Este es el corazón del proyecto. Escribimos un "Generador" que recorre el AST proporcionado por `libclang`. Su trabajo es:

      * Identificar las variables de **Estado ($S_t$)** (normalmente las globales).
      * Aplanar toda la lógica secuencial del bucle del juego (usando variables auxiliares, como discutimos) en una única **Función de Transición de Estado $F$**.
      * Esta función $F$ define el siguiente estado ($S_{t+1}$) basándose únicamente en el estado actual ($S_t$) y la entrada ($I_t$).
      * Finalmente, "aplasta" esta función $F$ en la ecuación polinómica $P=0$ usando los trucos del Teorema MRDP (ej. $a \ge 0 \rightarrow a = w^2+x^2+y^2+z^2$).

-----

## Reglas para Código Compatible

Para que el "Generador" (Fase 2) pueda traducir tu código, este debe seguir un conjunto de reglas estrictas. Estás escribiendo un programa, pero también estás definiendo una función matemática estática.

> **Importante:** El objetivo es que *toda* la lógica del programa se pueda "aplanar" en una única función de transición `S_t+1 = F(S_t)`.

### Regla 1: El Bucle de Estado Único

Toda la lógica computable del programa debe residir dentro de un **único bucle infinito** (`while(1)` o `for(;;)`).

  * **Variables de Estado (Globales):** Las variables declaradas *fuera* del bucle (como `b`, `c`, `p`, `q` en Pong) se tratan como el **Estado ($S_t$)**.
  * **Variables Auxiliares (Locales):** Las variables declaradas *dentro* del bucle (como `b_temp`) se tratan como "piezas" o "partes" para construir la ecuación final.

### Regla 2: Sin Funciones Externas

La lógica debe ser autocontenida. **No se permiten llamadas a funciones** que hayas definido en otra parte (ej. `mi_funcion()`). Toda la lógica debe estar "inline" (dentro del bucle).

### Regla 3: Manejo de Entradas y Salidas (I/O)

La I/O no es "computable" en el sentido matemático puro.

  * **Salida (Prohibida):** `printf()`, `puts()`, `system()`, `Sleep()` y cualquier función que interactúe con el "mundo exterior" será **ignorada** por el compilador.
  * **Entrada (Permitida):** Las funciones de entrada (ej. `k = getch();`) son un caso especial. El compilador las tratará como la variable de entrada $I_t$.

### Regla 4: Sin Flujo de Control Complejo

Para "aplanar" el código, no podemos tener saltos impredecibles.

  * **Prohibido:** `goto`, `break`, `continue`.
  * **Permitido:** `if`, `else`. (Las estructuras `switch` deben reescribirse como una serie de `if/else`).

### Regla 5: Sin Estado Oculto

  * **Prohibido:** No uses `static` en variables locales dentro del bucle. Esto introduce un estado oculto que rompe el modelo $S_{t+1} = F(S_t)$.

-----

### ✅ Ejemplo de Código Compatible

Este código **cumple** con las reglas. El Generador puede "aplanarlo" y traducirlo.
