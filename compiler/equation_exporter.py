import re

class EquationExporter:
    """
    Construye y exporta la Ecuación Maestra P=0 en múltiples formatos,
    incluyendo la versión teórica de una sola ecuación.
    
    Incluye métodos para calcular de forma segura el tamaño de todas las salidas
    antes de generar el contenido completo en la memoria.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs):
        # ... (constructor sin cambios)
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs

    # --- Métodos de Estimación de Tamaño (Seguros para la Memoria) ---

    def get_unoptimized_size_estimate(self):
        # ... (sin cambios)
        total_size = 0
        sorted_vars = sorted(self.unoptimized_f.keys())
        num_terms = len(sorted_vars)
        for i, var in enumerate(sorted_vars):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs_size = len(f"{var}[t+1]".encode('utf-8'))
            expr_size = self._calculate_poly_string_size(expr_tuple, expand=True)
            term_size = lhs_size + expr_size + 8
            total_size += term_size
            if i < num_terms - 1:
                total_size += len(" + \n".encode('utf-8'))
        total_size += len(" = 0".encode('utf-8'))
        return total_size
    
    # --- NUEVO: Estimador para la Ecuación Única P=0 ---
    def get_single_polynomial_size_estimate(self, poly_system_list):
        """
        Calcula el tamaño de la ecuación P=0 (suma de cuadrados) sin generarla.
        """
        if not poly_system_list:
            return 0
        total_size = 0
        num_eqs = len(poly_system_list)
        for i, eq_str in enumerate(poly_system_list):
            # Para "A = 0", queremos el tamaño de "(A)^2"
            # len(" = 0") es 4. len("()^2") es 4. Así que el tamaño no cambia.
            term_size = len(eq_str.encode('utf-8')) 
            total_size += term_size
            if i < num_eqs - 1:
                total_size += len(" + ".encode('utf-8'))
        
        total_size += len(" = 0".encode('utf-8'))
        return total_size

    # --- Métodos de Exportación (Generación de Contenido) ---

    def export_unoptimized(self):
        # ... (sin cambios)
        terms = []
        for var in sorted(self.unoptimized_f.keys()):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=True)
            terms.append(f"({lhs} - ({rhs}))^2")
        return " + \n".join(terms) + " = 0"

    def export_optimized(self):
        # ... (sin cambios)
        defs_section = []
        if self.sub_defs:
            defs_section.append("--- [DEFINICIONES DE SUBEXPRESIONES COMUNES (C_n)] ---")
            sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
            for name, expr_tuple in sorted_defs:
                clean_name = name.replace("{", "").replace("}", "")
                rhs = self._expr_to_poly_string(expr_tuple, expand=False)
                defs_section.append(f"{clean_name} = {rhs}")
        main_eq_section = ["\n--- [ECUACIÓN MAESTRA (OPTIMIZADA)] ---"]
        terms = []
        for var in sorted(self.optimized_f.keys()):
            expr_tuple = self.optimized_f.get(var, var)
            lhs = f"{var}[t+1]"
            rhs = self._expr_to_poly_string(expr_tuple, expand=False)
            terms.append(f"({lhs} - ({rhs}))^2")
        main_eq_section.append(" + \n".join(terms) + " = 0")
        return "\n".join(defs_section) + "\n" + "\n".join(main_eq_section)

    # --- NUEVO: Exportador para la Ecuación Única P=0 ---
    def export_single_polynomial(self, poly_system_list):
        """
        Toma el sistema de ecuaciones puras y las combina en una
        única ecuación de suma de cuadrados.
        """
        if not poly_system_list:
            return "= 0"
        
        terms = []
        for eq in poly_system_list:
            # Extraer el lado izquierdo de "LHS = 0"
            lhs = eq.rsplit(' =', 1)[0]
            terms.append(f"({lhs})^2")
        
        return " + ".join(terms) + " = 0"

    # --- Funciones de Ayuda Internas ---
    # ... (_expr_to_poly_string y _calculate_poly_string_size sin cambios)
    def _expr_to_poly_string(self, expr, expand):
        if expand and isinstance(expr, str) and expr in self.sub_defs:
            return self._expr_to_poly_string(self.sub_defs[expr], expand)
        if not isinstance(expr, tuple):
            if isinstance(expr, str):
                return expr.replace("{", "").replace("}", "")
            return str(expr) if expr is not None else "0"
        op = expr[0]
        args = [self._expr_to_poly_string(e, expand) for e in expr[1:]]
        if op == 'if': return f"(({args[0]}) * ({args[1]}) + (1 - {args[0]}) * ({args[2]}))"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'): return f"({args[0]} {op} {args[1]})"
        if op == '&&': return f"({args[0]} * {args[1]})"
        if op == '||': return f"({args[0]} + {args[1]} - {args[0]} * {args[1]})"
        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map: return f"{op_map[op]}({args[0]}, {args[1]})"
        return f"UNKNOWN_OP({op}, {', '.join(args)})"

    def _calculate_poly_string_size(self, expr, expand):
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
        if op in ('+', '-', '*', '/'): return arg_sizes[0] + arg_sizes[1] + 6
        if op == '&&': return arg_sizes[0] + arg_sizes[1] + 7
        if op == '||': return arg_sizes[0] * 2 + arg_sizes[1] * 2 + 13
        op_map = {'==': 'EQ', '!=': 'NEQ', '>': 'GT', '<': 'LT', '>=': 'GTE', '<=': 'LTE'}
        if op in op_map: return len(op_map[op]) + 1 + arg_sizes[0] + 2 + arg_sizes[1] + 1
        return len(f"UNKNOWN_OP({op})".encode('utf-8'))