import sys
import clang.cindex
from clang.cindex import CursorKind, TypeKind

# --- Configuración de libclang ---
clang.cindex.Config.set_library_path("C:/Program Files/LLVM/bin")

#======================================================================
# PUNTO DE ENTRADA PRINCIPAL
#======================================================================

def parse_c_file(filepath):
    """
    Analiza un archivo C y devuelve un "mapa de partes" estructurado
    (nuestro propio AST simplificado).
    """
    print(f"  [Parser] Iniciando indexación de {filepath}...")
    try:
        index = clang.cindex.Index.create()
        tu = index.parse(filepath, ['-std=c11']) # Usar un estándar de C

        if not tu:
            raise RuntimeError("Error: No se pudo crear la Unidad de Traducción.")

        errors = [d for d in tu.diagnostics if d.severity >= d.Error]
        if errors:
            print("  [Parser] ¡Error de sintaxis en el código C!", file=sys.stderr)
            for e in errors:
                print(f"  > {e}", file=sys.stderr)
            raise RuntimeError("Error de sintaxis en el C.")

        print("  [Parser] Archivo C analizado. Construyendo AST simplificado...")
        
        # 1. Encontrar variables de estado (globales)
        state_vars = _find_state_variables(tu.cursor)
        print(f"  [Parser] Variables de Estado (S_t) encontradas: {state_vars}")
        
        # 2. Encontrar la lógica de transición (dentro del bucle)
        # Esta es la nueva función "inteligente"
        logic_ast = _find_transition_logic(tu.cursor)
        print(f"  [Parser] Árbol de lógica de transición (F) construido.")

        # Este es nuestro "mapa de partes"
        ast_map = {
            'state_vars': state_vars,
            'logic_tree': logic_ast  # Un solo nodo 'Block' que contiene todo
        }
        
        return ast_map

    except clang.cindex.LibclangError as e:
        print(f"\n--- ERROR DE LIBCLANG ---", file=sys.stderr)
        print("¿Está LLVM/Clang instalado y en el PATH del sistema?", file=sys.stderr)
        print(f"Detalle: {e}", file=sys.stderr)
        sys.exit(1)

#======================================================================
# 1. BUSCADOR DE VARIABLES DE ESTADO
#======================================================================

def _find_state_variables(root_node):
    """Recorre el AST y encuentra las variables globales (nuestro estado)."""
    state_vars = []
    if root_node.kind == CursorKind.TRANSLATION_UNIT:
        for node in root_node.get_children():
            # VAR_DECL en el nivel superior (fuera de cualquier función)
            if node.kind == CursorKind.VAR_DECL and node.lexical_parent.kind == CursorKind.TRANSLATION_UNIT:
                # Aceptamos int y char (para 'k')
                if node.type.kind == TypeKind.INT or node.type.kind == TypeKind.CHAR_S:
                    state_vars.append(node.spelling)
    return state_vars

#======================================================================
# 2. CONSTRUCTOR DE AST DE LÓGICA DE TRANSICIÓN
#======================================================================

def _find_transition_logic(root_node):
    """Encuentra 'main' -> 'for(;;)' y construye nuestro AST de su cuerpo."""
    
    main_node = next((n for n in root_node.get_children() if n.kind == CursorKind.FUNCTION_DECL and n.spelling == 'main'), None)
    if not main_node:
        raise RuntimeError("No se encontró la función 'main'.")

    # Encontrar el bloque de cuerpo de 'main'
    compound_stmt = next((n for n in main_node.get_children() if n.kind == CursorKind.COMPOUND_STMT), None)
    if not compound_stmt:
        raise RuntimeError("No se encontró el cuerpo de 'main'.")

    # Encontrar el bucle 'for'
    for_stmt = next((n for n in compound_stmt.get_children() if n.kind == CursorKind.FOR_STMT), None)
    if not for_stmt:
        raise RuntimeError("No se encontró el bucle 'for(;;)' en 'main'.")

    # El cuerpo del bule 'for' suele ser otro COMPOUND_STMT
    loop_body = next((n for n in for_stmt.get_children() if n.kind == CursorKind.COMPOUND_STMT), None)
    if not loop_body:
        # A veces es una sola sentencia, lo buscamos
        loop_body = next((n for n in for_stmt.get_children() if n.kind != CursorKind.NULL_STMT), None)
        if not loop_body:
            raise RuntimeError("El bucle 'for' no tiene un cuerpo { ... }.")

    # ¡Aquí empieza la magia!
    # Construimos nuestro AST recursivamente a partir del cuerpo del bule
    return _parse_clang_node(loop_body)


def _parse_clang_node(node):
    """
    Función recursiva que traduce un nodo AST de Clang a nuestro
    propio AST de diccionario simplificado.
    """
    kind = node.kind

    # --- Nodos Estructurales ---
    
    # { ... }
    if kind == CursorKind.COMPOUND_STMT:
        statements = []
        for child in node.get_children():
            parsed_child = _parse_clang_node(child)
            if parsed_child:
                statements.append(parsed_child)
        return {'type': 'Block', 'statements': statements}

    # if (cond) { then_body } else { else_body }
    if kind == CursorKind.IF_STMT:
        children = list(node.get_children())
        condition = _parse_clang_node(children[0])
        then_body = _parse_clang_node(children[1])
        else_body = None
        if len(children) > 2:
            # Clang incluye el 'else' como el último hijo
            else_body = _parse_clang_node(children[2])
        return {'type': 'If', 'condition': condition, 'then_body': then_body, 'else_body': else_body}

    # --- Nodos de Asignación y Declaración ---

    # int p_next = p;
    if kind == CursorKind.DECL_STMT:
        # Asumimos una sola declaración, ej. 'int x = 1;'
        # Podría haber múltiples hijos (ej. 'int x, y;') pero lo ignoramos
        decl_node = list(node.get_children())[0]
        if decl_node.kind == CursorKind.VAR_DECL:
            target = decl_node.spelling
            value = None
            # Si tiene un valor (ej. '= p'), lo parseamos
            value_nodes = list(decl_node.get_children())
            if value_nodes:
                value = _parse_clang_node(value_nodes[0])
            return {'type': 'Declare', 'target': target, 'value': value}

    # b = b_final; (op = '=')
    # b += d;      (op = '+=')
    if kind == CursorKind.BINARY_OPERATOR and node.spelling in ['=', '+=', '-=']:
        children = list(node.get_children())
        target_node = _parse_clang_node(children[0])
        value_node = _parse_clang_node(children[1])
        
        # Asegurarnos de que el 'target' es un 'Var'
        if target_node and target_node.get('type') == 'Var':
            return {'type': 'Assign', 'target': target_node['name'], 'op': node.spelling, 'value': value_node}
        
    # p++; p--;
    if kind == CursorKind.UNARY_OPERATOR and node.spelling in ['++', '--']:
        target_node = _parse_clang_node(list(node.get_children())[0])
        if target_node and target_node.get('type') == 'Var':
            return {'type': 'Update', 'target': target_node['name'], 'op': node.spelling}
        
    # --- Nodos de Expresión ---

    # p > 1, b + d, c == 1, k == 'w' && p > 1
    if kind == CursorKind.BINARY_OPERATOR:
        children = list(node.get_children())
        if len(children) < 2: return None # Error de Clang
        left = _parse_clang_node(children[0])
        right = _parse_clang_node(children[1])
        return {'type': 'BinaryOp', 'op': node.spelling, 'left': left, 'right': right}

    # -e
    if kind == CursorKind.UNARY_OPERATOR and node.spelling == '-':
        operand = _parse_clang_node(list(node.get_children())[0])
        return {'type': 'UnaryOp', 'op': '-', 'operand': operand}

    # (p > 1)
    if kind == CursorKind.PAREN_EXPR:
        # Simplemente parseamos lo que está adentro
        return _parse_clang_node(list(node.get_children())[0])

    # Manejar "envoltorios" transparentes de Clang (¡LA CORRECCIÓN!)
    if kind == CursorKind.UNEXPOSED_EXPR:
        # Clang a menudo envuelve expresiones simples.
        # Simplemente parseamos el hijo, es lo que nos interesa.
        children = list(node.get_children())
        if children:
            return _parse_clang_node(children[0])
        else:
            return None # Envoltorio vacío
            
    # k == 'w' (¡LA CORRECCIÓN!)
    if kind == CursorKind.CHARACTER_LITERAL:
        # Extrae el valor ASCII de forma robusta usando tokens
        try:
            token_text = list(node.get_tokens())[0].spelling # Esto será "'w'"
            char = token_text.strip("'")
            
            if len(char) == 0:
                # Esto maneja el caso de error (ej. '\0' podría ser '0')
                if "'\\0'" in token_text:
                    return {'type': 'Constant', 'value': 0}
                print(f"Advertencia: No se pudo parsear CHAR_LITERAL, token='{token_text}'", file=sys.stderr)
                return {'type': 'Constant', 'value': 0} # Default
            
            # Manejar secuencias de escape simples
            if char == '\\n': char = '\n'
            elif char == '\\t': char = '\t'
            elif char == '\\0': char = '\0'

            return {'type': 'Constant', 'value': ord(char)} # 'w' -> 119
            
        except Exception as e:
            print(f"Error parseando CHAR_LITERAL: {e}", file=sys.stderr)
            return {'type': 'Constant', 'value': 0}

    # 1, 40, 18
    if kind == CursorKind.INTEGER_LITERAL:
        return {'type': 'Constant', 'value': int(list(node.get_tokens())[0].spelling)}

    # p, b, k, b_final
    if kind == CursorKind.DECL_REF_EXPR:
        return {'type': 'Var', 'name': node.spelling}

    # --- Nodos de I/O y otros ---
    
    if kind == CursorKind.CALL_EXPR:
        # Casos especiales de entrada
        if node.spelling == 'getch':
            return {'type': 'Call', 'name': 'getch'}
        if node.spelling == 'kbhit':
            return {'type': 'Call', 'name': 'kbhit'}
        # Ignorar todo lo demás (printf, Sleep, etc.)
        return None

    # Ignorar nodos vacíos o que no entendemos (ej. 'return 0;')
    return None