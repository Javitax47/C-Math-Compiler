import argparse
import sys
import os
import pprint # <--- (Esto ya no es necesario, pero no hace daño)

# Importamos los módulos que hemos creado
from compiler import parser
from compiler import generator
# from compiler import equation_builder

def main():
    # 1. Configurar el análisis de argumentos de la línea de comandos
    cli_parser = argparse.ArgumentParser(description="Compilador C a Ecuación Diophantus.")
    cli_parser.add_argument("input_file", help="La ruta al archivo .c compatible.")
    args = cli_parser.parse_args()

    print(f"--- Iniciando compilación de: {args.input_file} ---")

    try:
        # 2. Fase 1: Análisis (Parsing)
        print("[Fase 1] Analizando el código C con libclang...")
        
        ast_map = parser.parse_c_file(args.input_file)
        
        print("...Análisis completado. 'Mapa de partes' generado.\n")

        # --- QUITAR EL CÓDIGO DE DEPURACIÓN DE AQUÍ ---
        # print("--- SALIDA DE DEPURACIÓN (AST del Parser) ---")
        # pp = pprint.PrettyPrinter(indent=2, width=100)
        # pp.pprint(ast_map.get('logic_tree'))
        # print("---------------------------------------------\n")
        # print("[DEPURACIÓN] Saliendo del programa ANTES de ejecutar la Fase 2 (Generator).")
        # sys.exit(0) 
        # --- FIN DEL CÓDIGO A QUITAR ---


        # 3. Fase 2: Generación (Función F)
        print("[Fase 2] Generando la Función de Transición (F)...")
        
        # ¡Esta línea ahora se ejecutará!
        transition_function = generator.generate_function(ast_map)
        
        print("\n--- RESULTADO: Función de Transición (F) ---")
        # Usamos pprint para imprimir la función F de forma legible
        pp = pprint.PrettyPrinter(indent=2, width=120)
        pp.pprint(transition_function)
        print("------------------------------------------\n")

        # 4. Fase 3: Construcción de la Ecuación (Ecuación P)
        print("[Fase 3] Construyendo la ecuación polinómica (P)... (Saltado por ahora)")
        
        # ... (código futuro) ...

        print(f"\n--- Compilación (Fases 1 y 2) exitosa. ---")


    except FileNotFoundError:
        print(f"\n--- ERROR: Archivo no encontrado: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- ERROR DE COMPILACIÓN ---", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()