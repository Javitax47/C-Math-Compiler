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

`output/pong_full_analysis.tex`

Este documento es el artefacto principal del proyecto. Contiene:
1.  Un análisis de las variables de estado y de entrada.
2.  La **Función de Transición** en su forma pura y optimizada.
3.  El **Sistema de Ecuaciones Diofánticas Puras**, el plano de ingeniería del programa.
4.  La **Ecuación Polinómica Única (Forma Teórica P=0)**, la demostración final del teorema.

Puedes ver el informe generado para `pong.c` directamente [aquí](C_Math.pdf).

---

## 💻 El Intérprete: Ejecutando la Ecuación

Además del informe `.tex` para análisis teórico, el compilador genera un segundo artefacto crucial: un archivo `.txt` (ej. `output/pong_interpreter_input.txt`).

Este archivo es la **función de transición de estado** (`S_{t+1} = F(S_t, I_t)`) de tu programa, escrita como una "receta" paso a paso. El `interpreter.py` es la herramienta que lee esta receta para **ejecutar el juego** o simulación.

Esto nos permite demostrar no solo la equivalencia teórica, sino también la **ejecución práctica** del programa como un sistema puramente matemático.

-----

### La Cuestión de las Comparaciones (`==`, `>`)

Al inspeccionar el archivo `.txt` de salida, notarás que aunque la lógica de flujo (`if`, `&&`, `||`) se ha convertido en aritmética pura de `+`, `-` y `*`, las **comparaciones** (como `==`, `>`, `<=`) se mantienen.

Esto se hace por una razón fundamental que distingue la **simulación práctica** de la **prueba teórica**:

1.  **Simulación Práctica (El Intérprete):** Nuestro intérprete es un ejecutor lineal. Sabe cómo resolver `a > b` en un solo paso. Mantener estos operadores nos permite *ejecutar* el juego a una velocidad razonable, demostrando que la lógica del programa se ha "aplanado" con éxito.

2.  **Prueba Teórica Pura (El Informe):** El módulo `polynomial_converter.py` *sí* convierte estas comparaciones en aritmética estricta de `+`, `-` y `*`, introduciendo variables existenciales (ej. `e_n`). El resultado (visible en el `.tex`) es un sistema de ecuaciones simultáneas puro.

-----

### El Siguiente Nivel: SMT Solvers y Computación Cuántica

El sistema de ecuaciones puras generado por `polynomial_converter.py` ya no es una "receta" lineal que nuestro simple intérprete pueda seguir; es un "puzzle" de restricciones simultáneas (ej. `C_5` y `e_0` dependen la una de la otra en un ciclo).

Para "ejecutar" esta versión estrictamente polinómica, necesitaríamos una herramienta mucho más potente:

  * Un **Solucionador de Restricciones** (Constraint Solver) o **SMT Solver** (como Z3 de Microsoft) que pueda "encontrar" los valores de todas las variables que satisfagan todas las ecuaciones a la vez.

Este tipo de problema, donde un gran número de variables están "enredadas" en un sistema de restricciones complejo, es precisamente donde la computación clásica se vuelve ineficiente. Es un campo de estudio activo para la **computación cuántica**, cuyos algoritmos (como el *quantum annealing*) están diseñados para encontrar la solución óptima a estos sistemas masivos de forma mucho más eficiente que cualquier supercomputadora clásica.

-----

### 🚀 Ejecutando tu Propia Simulación

El archivo `.txt` generado es el "cerebro" (la matemática), pero no sabe cómo *dibujar* nada. Para ejecutar tu simulación, necesitas crear un "script corredor" (como `run_pong.py`) que actúe como el "cuerpo" (los ojos y las manos).

Tu script necesita hacer cuatro cosas:

1.  Importar e inicializar el motor (`EquationEngine`).
2.  Proveer el **Estado Inicial** (`S_0`), es decir, los valores iniciales de tus variables globales.
3.  Proveer las **Entradas** (`I_t`) en cada fotograma (ej. pulsaciones de teclas).
4.  **Renderizar** el estado resultante (`S_t+1`) en la pantalla.

#### Pasos para crear tu propio `runner.py`:

**1. El Script Básico:**
Usa [`run_pong.py`](interpreter/examples_interpreter/run_pong.py) como plantilla. La estructura básica es:

```python
import sys
import time
from interpreter.interpreter import EquationEngine

# --- 1. INICIALIZA EL MOTOR ---
if len(sys.argv) < 2:
    print("Uso: python tu_runner.py <ruta_al_archivo.txt>")
    sys.exit(1)
engine = EquationEngine(sys.argv[1])

# --- 2. DEFINE EL ESTADO INICIAL (S_0) ---
# DEBES rellenar esto con TUS variables globales
current_state = {
    'tu_var_global_1': 10,
    'tu_var_global_2': 0,
    # ...etc.
}

# --- 3. DEFINE TU RENDERIZADOR ---
def mi_renderizador(state):
    # Dibuja el estado en la pantalla
    # Por ejemplo, simplemente imprimir los valores:
    print(f"Estado actual: {state}")
    pass

# --- 4. EL BUCLE PRINCIPAL ---
while True:
    # 4a. Renderiza el estado actual
    mi_renderizador(current_state)
    
    # 4b. Recoge las entradas (I_t)
    inputs = {
        'kbhit': 0, # Proporciona las entradas que tu C usa
        'getch': 0
    }
    # (Aquí iría tu lógica para detectar teclas)
    
    # 4c. Calcula el siguiente estado (S_t+1)
    next_state = engine.compute_next_state(current_state, inputs)
    
    # 4d. Actualiza el estado para el siguiente fotograma
    current_state.update(next_state)
    
    # 4e. Espera un poco
    time.sleep(0.05)
```

**2. Definir el Estado Inicial (`S_0`)**
El diccionario `current_state` debe contener **todas** las variables globales de tu archivo C con sus valores iniciales. `run_pong.py` hace esto para el Pong:
`current_state = {'b': 40, 'c': 12, 'd': 1, 'e': 1, 'p': 10, ...}`
El motor (`EquationEngine`) tiene una función de ayuda, `get_state_variables()`, que te dice qué variables espera.

**3. Manejar las Entradas (`I_t`)**
El diccionario `inputs` debe tener claves que coincidan con los nombres de las funciones de entrada que tu C utiliza (ej. `kbhit`, `getch`). Si tu programa no usa entradas, puedes pasar un diccionario vacío: `inputs = {}`.

**4. Visualizar el Estado (El "Renderizador")**
Esta es tu tarea. El motor solo te da números. Tu función `mi_renderizador` (como `render_pong` en el ejemplo) es la que sabe que la variable `b` es la "posición X de la pelota" y `p` es la "posición Y de la paleta" y las dibuja en la pantalla.

**5. ¡Ejecutar\!**
Una vez que `main.py` haya generado tu archivo `.txt`, puedes ejecutar tu simulación:

```bash
# 1. Compila tu C para generar la ecuación
python main.py examples/tu_codigo.c

# 2. Ejecuta tu script corredor con esa ecuación
python tu_runner.py output/tu_codigo_interpreter_input.txt
```

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