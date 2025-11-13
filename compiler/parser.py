import sys
import clang.cindex
from clang.cindex import CursorKind

# --- Configuración de libclang ---
# El paquete 'libclang' de Python necesita encontrar la biblioteca de Clang
# (libclang.dll en Windows, libclang.so en Linux).
# Si instalaste LLVM (ej. 'winget install LLVM.LLVM'), 
# es posible que necesites descomentar la siguiente línea y apuntar a tu instalación.
# clang.cindex.Config.set_library_path("C:/Program Files/LLVM/bin")

def parse_c_file(filepath):
    """
    Analiza un archivo C y devuelve un AST simplificado.
    Por ahora, imprimirá los nodos que encuentre dentro del bucle principal.
    """
    print(f"  [Parser] Iniciando indexación de {filepath}...")
    try:
        index = clang.cindex.Index.create()
        
        # Analiza el archivo
        # translation_unit (tu) es el AST completo del archivo
        tu = index.parse(filepath)

        if not tu:
            raise RuntimeError("Error: No se pudo crear la Unidad de Traducción.")

        # Comprobar si hay errores de sintaxis en el C
        errors = [d for d in tu.diagnostics if d.severity >= d.Error]
        if errors:
            print("  [Parser] ¡Error de sintaxis en el código C!", file=sys.stderr)
            for e in errors:
                print(f"  > {e}", file=sys.stderr)
            raise RuntimeError("Error de sintaxis en el C. Corrígelo e inténtalo de nuevo.")

        print("  [Parser] Archivo C analizado. Recorriendo el AST...")
        
        # El "cursor" es el puntero que usamos para caminar por el AST
        _walk_ast(tu.cursor)
        
        # TODO: En el futuro, _walk_ast devolverá nuestro "mapa de partes"
        # ast_map = _walk_ast(tu.cursor)
        # return ast_map

    except clang.cindex.LibclangError as e:
        print(f"\n--- ERROR DE LIBCLANG ---", file=sys.stderr)
        print("¿Está LLVM/Clang instalado y en el PATH del sistema?", file=sys.stderr)
        print("Es posible que necesites instalarlo ('winget install LLVM.LLVM')", file=sys.stderr)
        print(f"Detalle: {e}", file=sys.stderr)
        sys.exit(1)


def _walk_ast(node, level=0):
    """
    Recorre el AST de Clang e imprime los nodos.
    Esta es una función de depuración para *mostrar* la estructura.
    """
    # Imprimir el tipo de nodo y su nombre (si lo tiene)
    indent = "  " * level
    print(f"{indent}Nodo: {node.kind.name}, Texto: '{node.spelling or node.displayname}'")

    # --- LÓGICA DE BÚSQUEDA ---
    # Queremos encontrar el bucle 'for' dentro de la función 'main'
    
    if node.kind == CursorKind.FUNCTION_DECL and node.spelling == 'main':
        print(f"{indent}  [Parser] ¡Función 'main' encontrada! Buscando bucle...")

        # Recorrer los hijos de 'main'
        for child in node.get_children():
            if child.kind == CursorKind.COMPOUND_STMT: # Es un bloque { ... }
                # Recorrer los hijos del bloque
                for inner_child in child.get_children():
                    if inner_child.kind == CursorKind.FOR_STMT:
                        print(f"{indent}    [Parser] ¡Bucle FOR(;;) encontrado!")
                        print(f"{indent}    --- INICIO LÓGICA COMPUTABLE ---")
                        # Recorrer los hijos del bucle FOR
                        for loop_body in inner_child.get_children():
                            _print_computable_logic(loop_body, level + 4)
                        print(f"{indent}    --- FIN LÓGICA COMPUTABLE ---")

    # --- RECURSIÓN ---
    # Continuar caminando por el árbol (aunque ya encontramos 'main')
    # En una implementación real, seríamos más selectivos.
    for child in node.get_children():
        # Evitar recursión infinita en 'main'
        if node.kind != CursorKind.FUNCTION_DECL or node.spelling != 'main':
            _walk_ast(child, level + 1)


def _print_computable_logic(node, level):
    """
    Una función de ejemplo que imprime la lógica dentro del bucle
    e ignora las llamadas a I/O (printf, etc.)
    """
    indent = "  " * level

    # Ignorar llamadas de I/O (Regla 3 de nuestro README)
    if node.kind == CursorKind.CALL_EXPR:
        if node.spelling in ['printf', 'Sleep', 'xy', 'kbhit', 'SetConsoleCursorInfo']:
            print(f"{indent}(Ignorando I/O: {node.spelling}())")
            return # No imprimir más

    # Imprimir la línea de código (de forma aproximada)
    # Esto usa los "tokens" (palabras) que componen el nodo
    tokens = [t.spelling for t in node.get_tokens()]
    if tokens:
        print(f"{indent}LÓGICA: {' '.join(tokens)}")

    # Recorrer recursivamente los hijos de esta sentencia
    for child in node.get_children():
        _print_computable_logic(child, level + 1)