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
    Analiza un archivo C y devuelve un "mapa de partes" estructurado (AST simplificado).
    """
    print(f"  [Parser] Iniciando indexación de {filepath}...")
    try:
        index = clang.cindex.Index.create()
        tu = index.parse(filepath)

        if not tu:
            raise RuntimeError("Error: No se pudo crear la Unidad de Traducción.")

        errors = [d for d in tu.diagnostics if d.severity >= d.Error]
        if errors:
            print("  [Parser] ¡Error de sintaxis en el código C!", file=sys.stderr)
            for e in errors:
                print(f"  > {e}", file=sys.stderr)
            raise RuntimeError("Error de sintaxis en el C.")

        print("  [Parser] Archivo C analizado. Recorriendo el AST...")
        
        # 1. Encontrar variables de estado (globales)
        state_vars = _find_state_variables(tu.cursor)
        print(f"  [Parser] Variables de Estado (S_t) encontradas: {state_vars}")
        
        # 2. Encontrar la lógica de transición (dentro del bucle)
        transitions = _find_transition_logic(tu.cursor)
        print(f"  [Parser] Lógica de Transición (F) encontrada: {len(transitions)} asignaciones.")

        # Este es nuestro "mapa de partes"
        ast_map = {
            'state_vars': state_vars,
            'transitions': transitions  # Lista de asignaciones
        }
        
        return ast_map

    except clang.cindex.LibclangError as e:
        print(f"\n--- ERROR DE LIBCLANG ---", file=sys.stderr)
        print("¿Está LLVM/Clang instalado y en el PATH del sistema?", file=sys.stderr)
        print(f"Detalle: {e}", file=sys.stderr)
        sys.exit(1)

def _find_state_variables(root_node):
    """Recorre el AST y encuentra las variables globales (nuestro estado)."""
    state_vars = []
    if root_node.kind == CursorKind.TRANSLATION_UNIT:
        for node in root_node.get_children():
            # VAR_DECL en el nivel superior (fuera de cualquier función)
            if node.kind == CursorKind.VAR_DECL and node.lexical_parent.kind == CursorKind.TRANSLATION_UNIT:
                if node.type.kind == clang.cindex.TypeKind.INT:
                    state_vars.append(node.spelling)
    return state_vars

def _find_transition_logic(root_node):
    """Encuentra 'main' -> 'for(;;)' y extrae la lógica de asignación."""
    transitions = []
    
    def find_loop(node):
        if node.kind == CursorKind.FUNCTION_DECL and node.spelling == 'main':
            for child in node.get_children():
                if child.kind == CursorKind.COMPOUND_STMT:
                    for inner_child in child.get_children():
                        if inner_child.kind == CursorKind.FOR_STMT:
                            for loop_body in inner_child.get_children():
                                _extract_logic(loop_body, transitions)
                            return
        for child in node.get_children():
            find_loop(child)

    find_loop(root_node)
    return transitions

def _extract_logic(node, transitions_list):
    """
    Extrae recursivamente la lógica computable (asignaciones)
    e ignora I/O.
    """
    # Ignorar I/O (Regla 3)
    if node.kind == CursorKind.CALL_EXPR:
        if node.spelling in ['printf', 'Sleep', 'xy', 'kbhit', 'SetConsoleCursorInfo', 'getch']:
            return

    # Esta es la lógica que nos interesa: 'x = x + 1'
    # 'BINARY_OPERATOR' con el 'op' de '='
    if node.kind == CursorKind.BINARY_OPERATOR and node.spelling == '=':
        
        children = list(node.get_children())
        if len(children) == 2:
            target_node = children[0]
            expression_node = children[1]
            
            # Extraer el texto de la expresión (ej. 'x + 1')
            expr_tokens = [t.spelling for t in expression_node.get_tokens()]
            
            assignment_data = {
                'type': 'Assignment',
                'target': target_node.spelling,  # 'x'
                'expression_str': " ".join(expr_tokens) # 'x + 1'
            }
            transitions_list.append(assignment_data)
            return # Encontramos la asignación, no necesitamos seguir bajando

    # Recorrer recursivamente
    for child in node.get_children():
        _extract_logic(child, transitions_list)