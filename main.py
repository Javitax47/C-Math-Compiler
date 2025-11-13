import argparse
import sys
import os
import pprint

from compiler import parser
from compiler import generator
from compiler import latex_exporter

def main():
    # 1. Configurar CLI
    cli_parser = argparse.ArgumentParser(description="Compilador C a Ecuación Diophantus.")
    cli_parser.add_argument("input_file", help="La ruta al archivo .c compatible.")
    args = cli_parser.parse_args()

    print(f"--- [Project Diophantus] Iniciando compilación de: {args.input_file} ---")

    # --- Definir rutas de salida ---
    os.makedirs("output", exist_ok=True)
    base_name = os.path.basename(args.input_file)
    base_filename = os.path.splitext(base_name)[0]
    
    tex_path = os.path.join("output", f"{base_filename}.tex")
    
    try:
        # 2. Fase 1: Análisis (Parsing)
        print("[Fase 1] Analizando el código C con libclang...")
        ast_map = parser.parse_c_file(args.input_file)
        print("...Análisis completado. 'Mapa de partes' generado.\n")

        # 3. Fase 2: Generación (Función F)
        print("[Fase 2] Generando la Función de Transición (F) (AST de tuplas)...")
        
        # --- ¡LÍNEA ACTUALIZADA! ---
        transition_function_tuples, input_vars = generator.generate_function(ast_map)
        
        print("...AST de tuplas de la Función F generado.\n")

        # 4. Fase 3: Optimización y Exportación LaTeX
        print("[Fase 3] Optimizando y exportando a LaTeX...")
        
        # --- ¡LÍNEA ACTUALIZADA! ---
        exporter = latex_exporter.LatexExporter(
            transition_function_tuples,
            ast_map['state_vars'],
            input_vars 
        )
        
        latex_output = exporter.export()
            
        latex_output = exporter.export()
            
        # 5. Guardar el .tex
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_output)
                
        print(f"...Exportación LaTeX completada.")
            
        print(f"\n--- Compilación exitosa ---")
        print(f"Documento LaTeX:      {tex_path}")

    except FileNotFoundError:
        print(f"\n--- ERROR: Archivo no encontrado: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- ERROR DE COMPILACIÓN ---", file=sys.stderr)
        print(f"{e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()