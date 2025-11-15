import re

class EquationExporter:
    """
    Construye y exporta las representaciones textuales de las ecuaciones
    en múltiples formatos, cada uno con un propósito específico.
    """
    # --- CORRECCIÓN: Se añade 'state_vars' para saber qué variables son de estado ---
    def __init__(self, unoptimized_f, optimized_f, sub_defs, state_vars):
        """
        Inicializa el exportador con los AST de tuplas necesarios.
        
        Args:
            unoptimized_f (dict): AST de las ecuaciones sin optimizar.
            optimized_f (dict): AST de las ecuaciones optimizadas.
            sub_defs (dict): Definiciones de subexpresiones comunes (C_n).
            state_vars (list or set): Una colección de nombres de variables que 
                                      representan el estado del sistema (ej: ['x', 'y']).
        """
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = set(state_vars)

    # --- Métodos de Ayuda Internos (para ordenamiento y conversión) ---

    def _get_sort_key(self, item):
        """
        --- MEJORA: Clave de ordenamiento robusta para nombres como 'C_n'. ---
        Devuelve el número dentro del nombre de una subexpresión para un ordenamiento
        natural. Si no hay número, lo coloca al final.
        """
        # item[0] es el nombre de la variable, ej: 'C_10'
        match = re.search(r'\d+', item[0])
        # Si se encuentra un número, se usa para ordenar. Si no, se usa infinito
        # para asegurar que los elementos sin número vayan al final.
        return int(match.group()) if match else float('inf')

    def _expr_to_poly_string(self, expr, expand):
        """Convierte una tupla a un string para el informe (con operadores infix)."""
        if expand and isinstance(expr, str) and expr in self.sub_defs:
            return self._expr_to_poly_string(self.sub_defs[expr], expand)
        if not isinstance(expr, tuple):
            if isinstance(expr, str): return expr.replace("{", "").replace("}", "")
            return str(expr) if expr is not None else "0"
        op = expr[0]; args = [self._expr_to_poly_string(e, expand) for e in expr[1:]]
        if op == 'if': return f"(({args[0]}) * ({args[1]}) + (1 - {args[0]}) * ({args[2]}))"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'): return f"({args[0]} {op} {args[1]})"
        if op == '&&': return f"({args[0]} * {args[1]})"
        if op == '||': return f"({args[0]} + {args[1]} - {args[0]} * {args[1]})"
        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map: return f"{op_map[op]}({args[0]}, {args[1]})"
        return f"UNKNOWN_OP({op}, {', '.join(args)})"

    def _tuple_to_generic_string(self, expr):
        """Convierte una tupla a un string genérico para el intérprete, ej: 'OP(arg1, arg2)'."""
        if not isinstance(expr, tuple):
            return str(expr).replace("{", "").replace("}", "")
        op = expr[0]
        args = [self._tuple_to_generic_string(arg) for arg in expr[1:]]
        return f"{op}({', '.join(args)})"

    # --- Métodos Públicos de Exportación ---

    def export_unoptimized(self):
        """
        Construye la ecuación de energía (P=0) en su forma completamente expandida.
        """
        terms = []
        for var in sorted(self.unoptimized_f.keys()):
            # Solo las variables de estado deben tener '[t+1]'
            if var not in self.state_vars: continue
            
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=True)
            terms.append(f"({lhs} - ({rhs}))^2")
        
        return " + \n".join(terms) + " = 0"

    def export_optimized(self):
        """
        Construye un sistema de ecuaciones legible usando las subexpresiones C_n.
        """
        defs_section = []
        if self.sub_defs:
            defs_section.append("--- [DEFINICIONES DE SUBEXPRESIONES COMUNES (C_n)] ---")
            # --- MEJORA: Usa la función de ordenamiento robusta ---
            sorted_defs = sorted(self.sub_defs.items(), key=self._get_sort_key)
            for name, expr_tuple in sorted_defs:
                clean_name = name.replace("{", "").replace("}", "")
                rhs = self._expr_to_poly_string(expr_tuple, expand=False)
                defs_section.append(f"{clean_name} = {rhs}")
        
        main_eq_section = ["\n--- [ECUACIÓN MAESTRA (OPTIMIZADA)] ---"]
        terms = []
        for var in sorted(self.optimized_f.keys()):
            # Solo las variables de estado deben aparecer en la ecuación de energía
            if var not in self.state_vars: continue

            expr_tuple = self.optimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=False)
            terms.append(f"({lhs} - ({rhs}))^2")
            
        main_eq_section.append(" + \n".join(terms) + " = 0")

        return "\n".join(defs_section) + "\n" + "\n".join(main_eq_section)

    def export_optimized_for_interpreter(self):
        """
        Exporta el sistema optimizado en formato 'var := expr' para el intérprete.
        """
        lines = []
        
        # 1. Definiciones de C_n
        # --- MEJORA: Usa la función de ordenamiento robusta ---
        sorted_defs = sorted(self.sub_defs.items(), key=self._get_sort_key)
        for name, expr_tuple in sorted_defs:
            clean_name = name.replace("{", "").replace("}", "")
            expr_str = self._tuple_to_generic_string(expr_tuple)
            lines.append(f"{clean_name} := {expr_str}")
        
        # --- CORRECCIÓN: Distingue entre variables de estado y variables intermedias ---
        # 2. Ecuaciones principales (tanto de estado como intermedias)
        for var, expr_tuple in self.optimized_f.items():
            # Decide el formato del LHS basándose en si 'var' es de estado
            if var in self.state_vars:
                lhs = f"{var}[t+1]"
            else:
                # Es una variable intermedia, no lleva sufijo de tiempo
                lhs = var
            
            expr_str = self._tuple_to_generic_string(expr_tuple)
            lines.append(f"{lhs} := {expr_str}")
            
        return "\n".join(lines)

    def export_single_polynomial(self, poly_system_list):
        """
        Combina un sistema de ecuaciones ("LHS = 0") en una única ecuación P=0.
        """
        if not poly_system_list:
            return "= 0"
        
        terms = [f"({eq.rsplit(' =', 1)[0]})^2" for eq in poly_system_list]
        return " + ".join(terms) + " = 0"

    # --- Métodos de Estimación de Tamaño ---

    def get_unoptimized_size_estimate(self):
        """
        Calcula de forma segura el tamaño de la ecuación no optimizada.
        """
        total_size = 0
        state_vars = sorted([v for v in self.unoptimized_f.keys() if v in self.state_vars])
        num_terms = len(state_vars)
        
        for i, var in enumerate(state_vars):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs_size = len(f"{var}[t+1]".encode('utf-8'))
            expr_size = self._calculate_poly_string_size(expr_tuple, expand=True)
            total_size += lhs_size + expr_size + 8 # para ' - ()^2'
            if i < num_terms - 1: 
                total_size += len(" + \n".encode('utf-8'))
        
        total_size += len(" = 0".encode('utf-8'))
        return total_size
        
    def _calculate_poly_string_size(self, expr, expand):
        """Calcula el tamaño de la salida de _expr_to_poly_string de forma segura."""
        if expand and isinstance(expr, str) and expr in self.sub_defs:
            return self._calculate_poly_string_size(self.sub_defs[expr], expand)
        if not isinstance(expr, tuple):
            base_str = str(expr) if expr is not None else "0"
            if isinstance(expr, str): 
                base_str = base_str.replace("{", "").replace("}", "")
            return len(base_str.encode('utf-8'))
            
        op = expr[0]
        arg_sizes = [self._calculate_poly_string_size(e, expand) for e in expr[1:]]
        
        if op == 'if': return 8 + arg_sizes[0] + 5 + arg_sizes[1] + 8 + arg_sizes[0] + 5 + arg_sizes[2] + 2
        if op == 'neg': return 3 + arg_sizes[0]
        if op in ('+', '-', '*', '/'): return arg_sizes[0] + arg_sizes[1] + 5 # "(a op b)"
        if op == '&&': return arg_sizes[0] + arg_sizes[1] + 5 # "(a * b)"
        
        # --- CORRECCIÓN: El número de caracteres fijos era 13, pero es 11 ---
        # La expresión es "(a + b - a * b)"
        if op == '||': return (arg_sizes[0] * 2) + arg_sizes[1] + 11 
        
        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map: return len(op_map[op]) + arg_sizes[0] + arg_sizes[1] + 4 # "OP(a, b)"
        
        # Fallback para operadores desconocidos
        return len(f"UNKNOWN_OP({op})".encode('utf-8')) + sum(arg_sizes)