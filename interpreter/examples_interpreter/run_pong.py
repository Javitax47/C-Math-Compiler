import sys
import os
import time
import msvcrt
# --- CORRECCIÓN ---
from interpreter.interpreter import EquationEngine

def render_pong(state):
    """
    Función de renderizado específica para Pong.
    Sabe qué significan las variables 'b', 'c', 'p', 'q', etc.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    b = state.get('b', 0); c = state.get('c', 0)
    p = state.get('p', 0); q = state.get('q', 0)
    f = state.get('f', 0); g = state.get('g', 0)
    
    print(f"Score: {f} - {g}   |   Ejecutando desde Ecuaciones Genéricas")
    for y in range(24):
        line = ""
        for x in range(80):
            if x == 1 and p <= y < p + 5: line += "|"
            elif x == 78 and q <= y < q + 5: line += "|"
            elif x == b and y == c: line += "O"
            elif y == 0 or y == 23: line += "-"
            else: line += " "
        print(line)

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m interpreter.examples_interpreter.run_pong <ruta_al_archivo>")
        sys.exit(1)
    
    engine = EquationEngine(sys.argv[1])
    
    current_state = {'b': 40, 'c': 12, 'd': 1, 'e': 1, 'p': 10, 'q': 10, 'f': 0, 'g': 0}
    
    expected_vars = set(engine.get_state_variables())
    if not expected_vars.issubset(current_state.keys()):
        missing = expected_vars - current_state.keys()
        raise ValueError(f"Faltan variables de estado iniciales: {missing}")

    print("\n--- Iniciando Simulación de Pong ---")
    time.sleep(2)

    while True:
        render_pong(current_state)
        
        inputs = {'kbhit': 0, 'getch': 0}
        if msvcrt.kbhit():
            inputs['kbhit'] = 1
            char = msvcrt.getch()
            inputs['getch'] = ord(char)
            if char.lower() == b'q':
                break
        
        next_state = engine.compute_next_state(current_state, inputs)
        current_state.update(next_state)
        time.sleep(0.05)

if __name__ == "__main__":
    main()