import argparse
import sys
import os
import traceback

# Importar todos los módulos del compilador
from compiler import parser
from compiler import generator
from compiler import optimizer
from compiler import latex_exporter
from compiler import equation_exporter
from compiler import polynomial_converter

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Límite de seguridad en Gigabytes para el informe .tex final.
# El programa se detendrá si el archivo excede este tamaño.
MAX_FINAL_REPORT_SIZE_GB = 5.0

def format_bytes(byte_count):
    """Formatea un número de bytes a un string legible (B, KB, MB, GB)."""
    if byte_count is None:
        return "0 B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while byte_count >= power and n < len(power_labels) - 1:
        byte_count /= power
        n += 1
    return f"{byte_count:.2f} {power_labels[n]}"

def main():
    """Punto de entrada principal del compilador Diophantus."""
    cli_parser = argparse.ArgumentParser(
        description="Compilador C a Ecuación Diophantus.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    cli_parser.add_argument("input_file", help="La ruta al archivo .c compatible.")
    args = cli_parser.parse_args()

    print(f"--- [Project Diophantus] Iniciando compilación de: {args.input_file} ---")

    # --- Definir ruta de salida ---
    try:
        os.makedirs("output", exist_ok=True)
        base_name = os.path.basename(args.input_file)
        base_filename = os.path.splitext(base_name)[0]
        final_tex_path = os.path.join("output", f"{base_filename}_full_analysis.tex")
    except OSError as e:
        print(f"\n--- ERROR DE SISTEMA DE ARCHIVOS ---", file=sys.stderr)
        print(f"No se pudo crear el directorio de salida 'output': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # FASE 1-3: Análisis, Generación y Optimización
        print("\n[Fase 1-3] Analizando, Generando y Optimizando...")
        ast_map = parser.parse_c_file(args.input_file)
        unoptimized_f, input_vars = generator.generate_function(ast_map)
        opt = optimizer.Optimizer(unoptimized_f)
        optimized_f, sub_defs = opt.optimize()

        # FASE 4: CONVERSIÓN A POLINOMIO PURO
        print("\n[Fase 4] Convirtiendo a sistema de ecuaciones diofánticas puras...")
        poly_conv = polynomial_converter.PolynomialConverter(optimized_f, sub_defs)
        poly_system = poly_conv.convert()
        poly_converter_info = {
            'existential_vars_count': poly_conv.existential_vars_count,
            'num_equations': len(poly_system)
        }

        # FASE 5: ENSAMBLAJE DEL INFORME FINAL
        print("\n[Fase 5] Ensamblando el informe final en LaTeX...")
        # Instanciar el exportador de ecuaciones solo para generar la ecuación P=0
        eq_exp = equation_exporter.EquationExporter(unoptimized_f, optimized_f, sub_defs)
        single_poly_equation = eq_exp.export_single_polynomial(poly_system)

        # Instanciar el exportador de LaTeX con TODOS los datos
        report_exporter = latex_exporter.LatexExporter(
            unoptimized_f, optimized_f, sub_defs, ast_map['state_vars'], input_vars,
            poly_system, single_poly_equation, poly_converter_info
        )
        final_latex_content = report_exporter.export()
        
        # FASE 6: ANÁLISIS DE TAMAÑO Y CONTROL DE SEGURIDAD
        print("\n[Fase 6] Analizando tamaño de salida y realizando control de seguridad...")
        final_size_bytes = len(final_latex_content.encode('utf-8'))
        print(f"  - Se generará 1 informe final en la carpeta 'output/':")
        print(f"    - Informe LaTeX (.tex): {format_bytes(final_size_bytes)}")

        limit_bytes = MAX_FINAL_REPORT_SIZE_GB * (1024**3)
        if final_size_bytes > limit_bytes:
            print(f"\n--- ERROR DE SEGURIDAD: LÍMITE DE TAMAÑO EXCEDIDO ---", file=sys.stderr)
            print(f"El informe final ({format_bytes(final_size_bytes)}) excede el límite de seguridad de {MAX_FINAL_REPORT_SIZE_GB} GB.", file=sys.stderr)
            print("El proceso se ha detenido. No se ha escrito ningún archivo en el disco.", file=sys.stderr)
            sys.exit(1)
        print("  - Comprobación de seguridad superada.")
        
        # FASE 7: ESCRITURA EN DISCO
        print("\n[Fase 7] Escribiendo informe final en disco...")
        with open(final_tex_path, "w", encoding="utf-8") as f:
            f.write(final_latex_content)
        print(f"  -> Informe completo guardado en: {final_tex_path}")
        print(f"  -> Para visualizar, compilar este archivo con un compilador de LaTeX (ej. pdflatex).")
        
        print(f"\n--- Compilación exitosa ---")

    except FileNotFoundError:
        print(f"\n--- ERROR: Archivo no encontrado: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- ERROR DE COMPILACIÓN INESPERADO ---", file=sys.stderr)
        print(f"Ha ocurrido un error durante el proceso: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()