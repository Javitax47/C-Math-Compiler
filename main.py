import argparse
import sys
import os
import traceback

# Importar los módulos del compilador
from compiler import parser
from compiler import generator
from compiler import optimizer
from compiler import latex_exporter
from compiler import equation_exporter
from compiler import polynomial_converter

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Límite de seguridad en Gigabytes para el archivo de la ecuación.
# El programa se detendrá si la ecuación sin optimizar excede este tamaño.
MAX_EQUATION_SIZE_GB = 5.0

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

    # --- Definir rutas de salida ---
    try:
        os.makedirs("output", exist_ok=True)
        base_name = os.path.basename(args.input_file)
        base_filename = os.path.splitext(base_name)[0]
        
        tex_path = os.path.join("output", f"{base_filename}.tex")
        eq_unopt_path = os.path.join("output", f"{base_filename}_equation_unoptimized.txt")
        eq_opt_path = os.path.join("output", f"{base_filename}_equation_optimized.txt")
    except OSError as e:
        print(f"\n--- ERROR DE SISTEMA DE ARCHIVOS ---", file=sys.stderr)
        print(f"No se pudo crear el directorio de salida 'output': {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # FASE 1: PARSING
        print("\n[Fase 1] Analizando el código C con libclang...")
        ast_map = parser.parse_c_file(args.input_file)

        # FASE 2: GENERACIÓN
        print("\n[Fase 2] Generando la Función de Transición (F) a partir del AST...")
        unoptimized_f, input_vars = generator.generate_function(ast_map)
        
        # FASE 3: OPTIMIZACIÓN
        print("\n[Fase 3] Optimizando la Función de Transición (CSE)...")
        opt = optimizer.Optimizer(unoptimized_f)
        optimized_f, sub_defs = opt.optimize()

        # FASE 4: ANÁLISIS DE ALMACENAMIENTO (SEGURO PARA LA MEMORIA)
        print("\n[Fase 4] Analizando requerimientos de almacenamiento...")
        
        # Instanciar los exportadores con los datos procesados
        latex_exp = latex_exporter.LatexExporter(unoptimized_f, optimized_f, sub_defs, ast_map['state_vars'], input_vars)
        eq_exp = equation_exporter.EquationExporter(unoptimized_f, optimized_f, sub_defs)

        # 1. Generar contenido pequeño en memoria para calcular su tamaño
        latex_content = latex_exp.export()
        opt_eq_content = eq_exp.export_optimized()
        
        # 2. Calcular el tamaño de la ecuación grande de forma segura (sin generarla)
        size_unopt_bytes_estimate = eq_exp.get_unoptimized_size_estimate()
        
        # 3. Calcular tamaños finales y el total
        size_latex_bytes = len(latex_content.encode('utf-8'))
        size_opt_bytes = len(opt_eq_content.encode('utf-8')) # La cabecera se añade después
        total_size_bytes = size_latex_bytes + size_unopt_bytes_estimate + size_opt_bytes

        print(f"  - Se generarán 3 archivos en la carpeta 'output/':")
        print(f"    1. Documento LaTeX (.tex):      {format_bytes(size_latex_bytes)}")
        print(f"    2. Ecuación Expandida (.txt):   {format_bytes(size_unopt_bytes_estimate)}")
        print(f"    3. Ecuación Optimizada (.txt):  {format_bytes(size_opt_bytes)}")
        print(f"  --------------------------------------------------")
        print(f"  - ESPACIO TOTAL REQUERIDO: {format_bytes(total_size_bytes)}")
        
        # 4. Control de seguridad
        limit_bytes = MAX_EQUATION_SIZE_GB * (1024**3)
        if size_unopt_bytes_estimate > limit_bytes:
            print(f"\n--- ERROR DE SEGURIDAD: LÍMITE DE TAMAÑO EXCEDIDO ---", file=sys.stderr)
            print(f"El tamaño estimado de la ecuación sin optimizar ({format_bytes(size_unopt_bytes_estimate)}) excede el límite de seguridad de {MAX_EQUATION_SIZE_GB} GB.", file=sys.stderr)
            print("El proceso se ha detenido. No se ha escrito ningún archivo en el disco.", file=sys.stderr)
            sys.exit(1)
        
        print("\n[Fase 5] Generando contenido final y escribiendo archivos en disco...")
        
        # 5. Generar el contenido grande SOLO AHORA que sabemos que es seguro
        unopt_eq_content = eq_exp.export_unoptimized()

        # --- FASE 6: CONVERSIÓN A POLINOMIO PURO ---
        print("\n[Fase 6] Convirtiendo a sistema de ecuaciones diofánticas puras...")
        poly_conv = polynomial_converter.PolynomialConverter(optimized_f, sub_defs)
        polynomial_system = poly_conv.convert()

        # Definir la ruta del nuevo archivo
        poly_path = os.path.join("output", f"{base_filename}_equation_polynomial.txt")

        # Escribir el sistema de ecuaciones polinómicas
        header_poly = f"=== SISTEMA DE ECUACIONES DIOFÁNTICAS PURAS PARA {base_name} ===\n"
        header_poly += "Cada línea es una ecuación que debe ser igual a cero.\n"
        header_poly += f"Variables de Estado: {ast_map['state_vars']}\n"
        header_poly += f"Variables de Entrada: {input_vars}\n"
        header_poly += f"Variables Existenciales (e_n): {poly_conv.existential_vars_count} introducidas.\n\n"

        with open(poly_path, "w", encoding="utf-8") as f:
            f.write(header_poly)
            f.write("\n".join(polynomial_system))

        print(f"  -> Sistema polinómico puro guardado en: {poly_path}")
        print(f"  -> Tamaño del sistema: {len(polynomial_system)} ecuaciones.")

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