import sys
import time
# --- CORRECCIÓN ---
from interpreter.interpreter import EquationEngine

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m interpreter.examples_interpreter.run_simple_counter <ruta_al_archivo>")
        sys.exit(1)
        
    engine = EquationEngine(sys.argv[1])
    current_state = {'x': 0} # Estado inicial del contador

    print("\n--- Iniciando Simulación del Contador ---")
    
    for i in range(20):
        print(f"Estado (t={i}): x = {current_state['x']}")
        
        # No hay entradas para este programa
        inputs = {}
        
        next_state = engine.compute_next_state(current_state, inputs)
        current_state.update(next_state)
        time.sleep(0.2)

if __name__ == "__main__":
    main()