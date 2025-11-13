import sys

#======================================================================
# El "Aplanador" (AST Visitor)
#======================================================================

class AstFlattener:
    """
    Esta clase visita el 'logic_tree' del parser y lo "aplana"
    para generar la Función de Transición F.
    
    Resuelve variables auxiliares y convierte 'if' en expresiones.
    """
    def __init__(self, state_vars):
        # Las variables de estado globales (ej. 'b', 'c', 'p')
        self.state_vars = set(state_vars)
        
        # El estado 'actual' (t). Se inicializa con los valores [t]
        # Ej: {'b': 'b', 'p': 'p', ...}
        self.current_state = {var: var for var in state_vars}
        
        # Aquí guardamos las variables auxiliares (ej. 'b_temp')
        self.aux_vars = {}
        
        # Contador para variables únicas de 'if'
        self.if_cond_counter = 0

    def generate_function_F(self, logic_tree):
        """Punto de entrada. Visita el árbol y devuelve la Función F."""
        
        # 1. Visitar el árbol lógico.
        # Esto rellena self.current_state con las expresiones finales
        # para *todas* las variables (estado y auxiliares).
        self._visit(logic_tree)
        
        # 2. Construir la Función F final
        # Solo nos interesan las variables de estado.
        function_F = {}
        for var in self.state_vars:
            if var in self.current_state:
                # Resuelve cualquier variable auxiliar restante
                final_expr = self._resolve_expression(self.current_state[var])
                function_F[var] = final_expr
            else:
                # Si no se tocó, S[t+1] = S[t]
                function_F[var] = var
                
        return function_F

    def _resolve_expression(self, expression):
        """
        Sustituye recursivamente las variables auxiliares en una expresión
        hasta que solo queden variables de estado.
        Ej: 'b_final' -> 'b_movido' -> '(b + d)'
        """
        # Si la expresión es una variable auxiliar, la sustituimos
        if isinstance(expression, str) and expression in self.aux_vars:
            return self._resolve_expression(self.aux_vars[expression])
        
        # Si es una expresión (tupla), resolvemos sus hijos
        if isinstance(expression, tuple):
            op = expression[0]
            args = [self._resolve_expression(arg) for arg in expression[1:]]
            return (op,) + tuple(args)
        
        # Es un valor base (constante o variable de estado)
        return expression

    def _format_expression(self, expr):
        """Convierte nuestras tuplas de expresión de nuevo en un string."""
        if isinstance(expr, tuple):
            op = expr[0]
            if op == 'if':
                cond, then_val, else_val = expr[1:]
                return f"({self._format_expression(cond)} * {self._format_expression(then_val)}) + ((1 - {self._format_expression(cond)}) * {self._format_expression(else_val)})"
            if op in ('+', '-', '*', '/', '==', '!=', '>', '<', '>=', '<=', '&&', '||'):
                left, right = expr[1:]
                return f"({self._format_expression(left)} {op} {self._format_expression(right)})"
            if op == 'neg': # Negación unaria
                return f"(-{self._format_expression(expr[1])})"
        if isinstance(expr, int):
            return str(expr)
        if expr is None:
            return "0" # Default
        return expr # Es un string (nombre de variable)


    def _visit(self, node):
        """Función principal de visita, llama al método correcto para cada tipo de nodo."""
        if node is None:
            return None
        
        node_type = node.get('type')
        method_name = f'_visit_{node_type}'
        visitor = getattr(self, method_name, self._visit_default)
        return visitor(node)

    def _visit_default(self, node):
        print(f"Advertencia: No se reconoce el tipo de nodo: {node.get('type')}", file=sys.stderr)
        return None

    # --- Visitantes de Nodos Estructurales ---

    def _visit_Block(self, node):
        """Visita un bloque { ... }"""
        # Visita cada sentencia en orden.
        # Esto es crucial para que las asignaciones secuenciales funcionen.
        for stmt in node['statements']:
            self._visit(stmt)
            
    def _visit_If(self, node):
        """Visita un 'if (cond) { then } else { else }'"""
        
        # 1. Visita la condición
        cond_expr = self._visit(node['condition'])
        
        # 2. Guardar el estado *antes* de entrar en las ramas
        # Esto es clave para el "aplanamiento"
        state_before_if = self.current_state.copy()
        
        # 3. Visitar la rama 'then'
        self._visit(node['then_body'])
        state_after_then = self.current_state
        
        # 4. Resetear el estado y visitar la rama 'else'
        self.current_state = state_before_if.copy()
        self._visit(node['else_body'])
        state_after_else = self.current_state
        
        # 5. Fusionar los estados
        # Itera sobre todas las variables que *podrían* haber sido modificadas
        all_modified_vars = set(state_after_then.keys()) | set(state_after_else.keys())
        
        new_state = state_before_if.copy()
        for var in all_modified_vars:
            # Si no es una variable de estado o aux, la ignoramos
            if var not in self.state_vars and var not in self.aux_vars:
                continue
                
            val_then = state_after_then.get(var, var) # Valor si C=1
            val_else = state_after_else.get(var, var) # Valor si C=0
            
            if val_then == val_else:
                new_state[var] = val_then # No hay cambio, no se necesita 'if'
            else:
                # ¡El truco aritmético!
                # new_val = (cond * val_then) + ((1 - cond) * val_else)
                new_state[var] = ('if', cond_expr, val_then, val_else)

        self.current_state = new_state

    # --- Visitantes de Nodos de Asignación ---

    def _visit_Declare(self, node):
        """Visita 'int b_temp = b + d;'"""
        target = node['target']
        value_expr = self._visit(node['value'])
        
        # La guardamos como variable auxiliar
        self.aux_vars[target] = value_expr
        self.current_state[target] = value_expr # También el estado actual

    def _visit_Assign(self, node):
        """Visita 'b = b_final;' o 'b += d;'"""
        target = node['target']
        op = node['op']
        value_expr = self._visit(node['value'])
        
        if op == '=':
            final_value = value_expr
        else:
            # Resolver 'b += d' -> ('+', 'b', d_expr)
            current_value = self.current_state.get(target, target)
            if op == '+=': final_value = ('+', current_value, value_expr)
            elif op == '-=': final_value = ('-', current_value, value_expr)
            # (Podríamos añadir '*=', '/=' aquí)
            
        if target in self.state_vars:
            self.current_state[target] = final_value
        else:
            self.aux_vars[target] = final_value
            self.current_state[target] = final_value # También el estado actual

    def _visit_Update(self, node):
        """Visita 'p++;'"""
        target = node['target']
        current_value = self.current_state.get(target, target)
        
        if node['op'] == '++':
            final_value = ('+', current_value, 1)
        else: # '--'
            final_value = ('-', current_value, 1)

        if target in self.state_vars:
            self.current_state[target] = final_value
        else:
            self.aux_vars[target] = final_value
            self.current_state[target] = final_value

    # --- Visitantes de Nodos de Expresión (Devuelven valores) ---

    def _visit_BinaryOp(self, node):
        """Visita 'a + b', 'c == 1', 'k == 'w' && p > 1'"""
        left = self._visit(node['left'])
        right = self._visit(node['right'])
        return (node['op'], left, right)

    def _visit_UnaryOp(self, node):
        """Visita '-e'"""
        operand = self._visit(node['operand'])
        if node['op'] == '-':
            return ('neg', operand)
        return operand # Ignorar otros (ej. '!') por ahora

    def _visit_Constant(self, node):
        return node['value'] # Devuelve el int (ej. 1, 40, 119)

    def _visit_Var(self, node):
        """Visita 'b', 'k', 'b_temp'"""
        name = node['name']
        # Si es una variable, devuelve su valor *actual* resuelto
        # Esto maneja la sustitución de auxiliares sobre la marcha
        if name in self.current_state:
            return self.current_state[name]
        return name # Es una variable (ej. 'k' de entrada)

    def _visit_Call(self, node):
        """Visita 'getch()' o 'kbhit()'"""
        # Las tratamos como variables de entrada especiales
        return node['name']


#======================================================================
# PUNTO DE ENTRADA PRINCIPAL (Llamado por main.py)
#======================================================================

def generate_function(ast_map):
    """
    Genera la Función de Transición (F) a partir del mapa del AST.
    """
    print(f"  [Generator] Iniciando Generación de Función F...")
    
    state_vars = ast_map['state_vars']
    logic_tree = ast_map['logic_tree']
    
    flattener = AstFlattener(state_vars)
    function_F_internal = flattener.generate_function_F(logic_tree)
    
    # El resultado final es un diccionario de strings
    function_F_strings = {}
    
    print(f"  [Generator] ...Aplanamiento completado. Generando strings de ecuación...")
    for var, expression in function_F_internal.items():
        function_F_strings[var] = flattener._format_expression(expression)
        
    print(f"  [Generator] ...Función de Transición (F) generada.")
    return function_F_strings