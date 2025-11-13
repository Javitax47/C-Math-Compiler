import argparse
import sys
import os

# ¡Ahora estos módulos (al menos 'parser') existen!
from compiler import parser
# from diophantus_compiler import generator, equation_builder (Aún no)

def main():
    # 1. Configurar el análisis de argumentos de la línea de comandos
    cli_parser = argparse.ArgumentParser(description="Compilador C a Ecuación Diophantus.")
    cli_parser.add_argument("input_file", help="La ruta al archivo .c compatible.")
    args = cli_parser.parse_args()

    print(f"--- [Project Diophantus] Iniciando compilación de: {args.input_file} ---")

    try:
        # 2. Fase 1: Análisis (Parsing)
        print("[Fase 1] Analizando el código C con libclang...")
        
        # ¡Llamamos a nuestra función de parseo!
        parser.parse_c_file(args.input_file)
        
        print("...Análisis (impresión de AST) completado.")

        # 3. Fase 2: Generación (Función F)
        print("\n[Fase 2] Generando la Función de Transición (F)... (Saltado por ahora)")
        
        # transition_function = generator.generate_function(ast_map)
        # print(f"...Función de Transición (F) generada.")

        # 4. Fase 3: Construcción de la Ecuación (Ecuación P)
        print("\n[Fase 3] Construyendo la ecuación polinómica (P)... (Saltado por ahora)")
        
        # final_equation = equation_builder.build_equation(transition_function)
        # print("...Ecuación P=0 construida.")

        # 5. Guardar la salida (Saltado por ahora)
        
        print(f"\n--- Compilación de prueba (Fase 1) exitosa. ---")


    except FileNotFoundError:
        print(f"\n--- ERROR: Archivo no encontrado: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- ERROR DE COMPILACIÓN ---", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()