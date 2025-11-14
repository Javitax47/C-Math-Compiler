# Project Diophantus
### Un compilador que traduce un videojuego en C a una única ecuación matemática.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Project Diophantus es un compilador experimental que explora la profunda conexión entre la computación y las matemáticas. En lugar de generar código máquina, traduce programas escritos en un subconjunto de C a su equivalente matemático puro: un sistema de ecuaciones diofánticas.

Sirve como una demostración tangible y ejecutable del **Teorema de Matiyasevich (MRDP)**, mostrando que la lógica dinámica de un programa puede ser "colapsada" en un objeto matemático estático.

---

### La Magia en Acción

El compilador toma un programa como `pong.c`, analiza su lógica y genera un informe en PDF que contiene la "ley física" del juego en forma de ecuaciones.

`pong.c`  -> `[ Diophantus Compiler ]` ->  `Informe de Análisis en PDF`

**(Recomendación: Graba un GIF corto de la terminal ejecutando el comando y mostrando el PDF. ¡Será increíblemente efectivo aquí!)**

---

### El Concepto: De `if-else` a Aritmética

El proyecto se basa en la asombrosa idea de que toda la computación es una forma de aritmética. La lógica de un programa se traduce a operaciones matemáticas:

*   La sentencia `if (C) { A } else { B }` se convierte en: `(C * A) + ((1 - C) * B)`
*   La comparación `a > b` se convierte en un sistema que afirma la existencia de números enteros `w,x,y,z` tales que `a - b = w²+x²+y²+z²+1`.

El compilador automatiza este proceso de "aritmetización" para un programa entero.

### Características

*   **Análisis de C con `libclang`:** Utiliza el potente parser de Clang para un análisis sintáctico robusto del código fuente.
*   **Aplanamiento Algebraico:** Convierte la lógica secuencial, los condicionales y las variables temporales en una única función de transición de estado `S_{t+1} = F(S_t, I_t)`.
*   **Optimización CSE:** Aplica la Eliminación de Subexpresiones Comunes para simplificar las ecuaciones masivas, revelando la estructura lógica subyacente del programa.
*   **Generación de Informe en LaTeX:** Produce un único y completo documento PDF con calidad académica que detalla cada etapa de la transformación, desde la lógica del programa hasta la ecuación teórica final.

---

## Reglas para Código C Compatible

Para que el compilador pueda traducir tu código, este debe seguir un conjunto de reglas estrictas. El objetivo es que *toda* la lógica computable del programa se pueda "aplanar" en una única función de transición.

#### 1. La Regla del Bucle Único
Toda la lógica del programa debe residir dentro de un **único bucle infinito** (`for(;;)` o `while(1)`) en la función `main`. Este bucle representa el paso del tiempo, fotograma a fotograma.

#### 2. Gestión de Estado Clara: Global vs. Local
*   **Variables de Estado (Globales):** Las variables declaradas *fuera* de cualquier función se tratan como el **Estado persistente del sistema (S_t)**.
*   **Variables Auxiliares (Locales):** Las variables declaradas *dentro* del bucle se tratan como valores temporales que se usan para construir el siguiente estado.
*   **Prohibido el Estado Oculto:** No se permite el uso de variables `static` locales, ya que introducen un estado que no forma parte del vector de estado global, rompiendo el modelo matemático.

#### 3. Flujo de Control Restringido
Para poder "aplanar" el código, los saltos deben ser predecibles.
*   **Permitido:** `if`, `else`. (Las sentencias `switch` deben ser reescritas como una cadena de `if-else`).
*   **Prohibido:** `goto`, `break`, `continue` dentro de la lógica principal del bucle.

#### 4. Lógica Autocontenida (Sin Funciones de Usuario)
Toda la lógica computable debe estar "inline" dentro del bucle principal. No se permiten llamadas a funciones definidas por el usuario (ej. `mi_funcion()`), ya que el aplanador no las analizará.

#### 5. Manejo Especial de Entradas y Salidas (I/O)
La I/O no afecta al estado matemático del sistema.
*   **Salida (Ignorada):** Llamadas a funciones como `printf()`, `puts()`, `Sleep()`, `system()` y otras funciones de librería que interactúan con el exterior serán **completamente ignoradas** por el parser.
*   **Entrada (Caso Especial):** Las funciones `getch()` y `kbhit()` son reconocidas y tratadas como las **variables de entrada (I_t)** del sistema para ese fotograma.

#### 6. Tipos de Datos Simples
El sistema está diseñado para trabajar con aritmética entera.
*   **Soportado:** `int`, `char`.
*   **No Soportado:** `float`, `double`, `struct`, arrays, punteros y otros tipos de datos complejos.

> Un ejemplo perfecto de código compatible es el archivo [`examples/pong.c`](./examples/pong.c) incluido en este repositorio.

---

## 🚀 Preparación y Uso

### 1. Instalación
El proceso de instalación gestiona todas las dependencias, incluida `libclang`.

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/project-diophantus.git
cd project-diophantus

# 2. Crea y activa un entorno virtual
python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 3. Instala todas las dependencias de Python
pip install -r requirements.txt
```

### 2. Ejecución
¡Ya estás listo! Ejecuta `main.py` desde el directorio raíz y pásale la ruta a uno de los ejemplos.

**Prueba con el juego de Pong:**
```bash
python main.py examples/pong.c
```

### ⚠️ Solución de Problemas: Error de `libclang`
Si al ejecutar el programa encuentras un error como `LibclangError` o `library file: 'libclang.dll' not found`, significa que la biblioteca de Python no pudo localizar la instalación de LLVM/Clang en tu sistema.

En ese caso, la solución más robusta es instalar LLVM manualmente:

*   **Windows:** Descarga e instala los "Pre-built binaries" de LLVM desde [su página oficial](https://releases.llvm.org/download.html). **Asegúrate de marcar la casilla "Add LLVM to the system PATH"** durante la instalación.
*   **macOS:** `brew install llvm`
*   **Linux (Debian/Ubuntu):** `sudo apt-get install libclang-dev`

Después de la instalación manual, intenta ejecutar el comando `pip install -r requirements.txt` de nuevo dentro de tu entorno virtual.

---

## 🔬 El Resultado: Un Informe Matemático

Tras una compilación exitosa, encontrarás un nuevo archivo en la carpeta `output/`:

`output/pong_full_analysis.pdf`

Este documento es el artefacto principal del proyecto. Contiene:
1.  Un análisis de las variables de estado y de entrada.
2.  La **Función de Transición** en su forma pura y optimizada.
3.  El **Sistema de Ecuaciones Diofánticas Puras**, el plano de ingeniería del programa.
4.  La **Ecuación Polinómica Única (Forma Teórica P=0)**, la demostración final del teorema.

Puedes ver el informe generado para `pong.c` directamente [aquí](./output/pong_full_analysis.pdf).

---

### Una Mirada a la Arquitectura

El compilador opera en un pipeline de 4 fases principales:

`Código C` -> **1. Parser** -> `AST` -> **2. Generator** -> `Tuple AST` -> **3. Optimizer** -> `Optimized AST` -> **4. Converters & Exporter** -> `Informe PDF Final`

---

### Para una Inmersión Profunda

Tu exploración de la teoría, el potencial y las limitaciones de este proyecto es perfecta para un artículo de blog.

> **Recomendación:** Publica tu análisis en **Medium** o **Dev.to** y pon un enlace aquí. Será la mejor manera de compartir la fascinante historia detrás del código.
> 
> "[Lee el artículo completo sobre la teoría y el potencial revolucionario de Project Diophantus.](link-a-tu-articulo.com)"

---

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.