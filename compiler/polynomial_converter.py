import re

class PolynomialConverter:
    """
    Toma un AST de tuplas "aritmetizado" y lo convierte en un sistema
    de ecuaciones diofánticas puras (solo suma, resta, multiplicación).

    Este es el paso final para cumplir con la demostración del Teorema MRDP.
    Introduce variables existenciales (e_n) para reemplazar operadores
    lógicos con aritmética entera.
    """
    def __init__(self, optimized_f, sub_defs):
        """
        Inicializa el convertidor.

        Args:
            optimized_f (dict): La F-Function optimizada con referencias a C_n.
            sub_defs (dict): Las definiciones de las subexpresiones C_n.
        """
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.existential_vars_count = 0
        self.polynomial_system = []

    def _new_e_var(self):
        """Genera un nombre único para una nueva variable existencial."""
        var_name = f"e_{self.existential_vars_count}"
        self.existential_vars_count += 1
        return var_name

    def convert(self):
        """
        Punto de entrada. Convierte la F-Function completa a un sistema polinómico.

        Returns:
            list: Una lista de strings, donde cada string es una ecuación P=0.
        """
        print("  [PolyConverter] Iniciando conversión a polinomio puro...")
        
        # 1. Convertir las definiciones de C_n, que son los cálculos intermedios.
        sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
        for name, expr_tuple in sorted_defs:
            clean_name = name.replace("{", "").replace("}", "")
            self._convert_expr_to_poly(clean_name, expr_tuple)
        
        # 2. Convertir las ecuaciones de estado principales (las asignaciones finales).
        for var in sorted(self.optimized_f.keys()):
            expr_tuple = self.optimized_f[var]
            lhs = f"{var}[t+1]"
            self._convert_expr_to_poly(lhs, expr_tuple)
            
        print(f"  [PolyConverter] ...Conversión completada. {self.existential_vars_count} variables existenciales introducidas.")
        return self.polynomial_system

    def _convert_expr_to_poly(self, target_var, expr):
        """
        Función principal recursiva. Traduce una expresión (RHS) y genera la
        ecuación `target_var = RHS` en forma polinómica pura.
        """
        if not isinstance(expr, tuple):
            # Caso base: es una asignación simple (ej. p[t+1] = C_15)
            self.polynomial_system.append(f"{target_var} - ({expr}) = 0")
            return

        op = expr[0]
        # Nos aseguramos de que todos los operandos sean variables simples,
        # resolviendo sub-expresiones en variables temporales si es necesario.
        arg_vars = [self._resolve_operand(arg) for arg in expr[1:]]

        # --- Operadores Aritméticos Puros ---
        if op in ('+', '-', '*'):
            # target = arg1 op arg2  =>  target - (arg1 op arg2) = 0
            self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
        elif op == 'neg':
            self.polynomial_system.append(f"{target_var} - (-{arg_vars[0]}) = 0")
        elif op == 'if':
            # target = cond * val_true + (1-cond) * val_false
            cond, val_true, val_false = arg_vars
            self.polynomial_system.append(f"{target_var} - (({cond}) * ({val_true}) + (1 - {cond}) * ({val_false})) = 0")

        # --- Conversión de Lógica a Polinomios ---
        elif op == '==': # target = (a == b)
            # Se traduce en 3 restricciones:
            # 1. target debe ser 0 o 1: target * (1-target) = 0
            # 2. Si target es 1, entonces a=b: target * (a-b) = 0
            # 3. Si a!=b, entonces target es 0: (a-b)*e_n - (1-target) = 0 (truco del inverso)
            a, b = arg_vars
            e_inv = self._new_e_var()
            self.polynomial_system.append(f"{target_var} * (1 - {target_var}) = 0")
            self.polynomial_system.append(f"{target_var} * (({a}) - ({b})) = 0")
            self.polynomial_system.append(f"(({a}) - ({b})) * {e_inv} - (1 - {target_var}) = 0")

        elif op == '<=': # target = (a <= b)
            # Se traduce en 3 restricciones:
            # 1. target debe ser 0 o 1: target * (1-target) = 0
            # 2. Si target=1, b-a debe ser no-negativo (suma de 4 cuadrados)
            # 3. Si target=0, a-b-1 debe ser no-negativo (es decir, a > b)
            a, b = arg_vars
            e_squares1 = [self._new_e_var() for _ in range(4)]
            e_squares2 = [self._new_e_var() for _ in range(4)]
            sum_sq_1 = f"({e_squares1[0]}^2 + {e_squares1[1]}^2 + {e_squares1[2]}^2 + {e_squares1[3]}^2)"
            sum_sq_2 = f"({e_squares2[0]}^2 + {e_squares2[1]}^2 + {e_squares2[2]}^2 + {e_squares2[3]}^2)"
            
            self.polynomial_system.append(f"{target_var} * (1 - {target_var}) = 0")
            self.polynomial_system.append(f"{target_var} * (({b}) - ({a}) - {sum_sq_1}) = 0")
            self.polynomial_system.append(f"(1 - {target_var}) * (({a}) - ({b}) - 1 - {sum_sq_2}) = 0")

        # --- Reducción de Otros Operadores a los Casos Base ---
        else:
            a, b = arg_vars
            if op == '&&': # target = a AND b  =>  target - (a*b) = 0
                self.polynomial_system.append(f"{target_var} - ({a} * {b}) = 0")
            elif op == '||': # target = a OR b   =>  target - (a+b - a*b) = 0
                self.polynomial_system.append(f"{target_var} - ({a} + {b} - {a} * {b}) = 0")
            else:
                # Para el resto de comparaciones, creamos una variable temporal para el resultado
                # y llamamos recursivamente con una expresión equivalente.
                temp_res = self._new_e_var()
                if op == '!=': # a != b  es  1 - (a == b)
                    self._convert_expr_to_poly(temp_res, ('==', expr[1], expr[2]))
                    self.polynomial_system.append(f"{target_var} - (1 - {temp_res}) = 0")
                elif op == '<': # a < b  es  a <= b - 1
                    self._convert_expr_to_poly(target_var, ('<=', expr[1], ('-', expr[2], 1)))
                elif op == '>=': # a >= b  es  b <= a
                    self._convert_expr_to_poly(target_var, ('<=', expr[2], expr[1]))
                elif op == '>': # a > b  es  b < a
                    self._convert_expr_to_poly(target_var, ('<', expr[2], expr[1]))

    def _resolve_operand(self, operand):
        """
        Asegura que un operando sea una variable simple. Si es una sub-expresión
        compleja, la resuelve en una variable temporal y devuelve su nombre.
        """
        if not isinstance(operand, tuple):
            # Es una constante, una variable de estado, o un C_n/e_n ya resuelto.
            return str(operand).replace("{", "").replace("}", "")
        
        # Es una sub-expresión anidada. Necesitamos calcularla primero.
        temp_var = self._new_e_var()
        self._convert_expr_to_poly(temp_var, operand)
        return temp_var