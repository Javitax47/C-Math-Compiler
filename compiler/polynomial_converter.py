class PolynomialConverter:
    """
    Toma un AST de tuplas "aritmetizado" y lo convierte en un sistema
    de ecuaciones diofánticas puras (solo suma, resta, multiplicación).

    Este es el paso final para cumplir con la demostración del Teorema MRDP.
    """
    def __init__(self, optimized_f, sub_defs):
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
        
        # 1. Convertir las definiciones de C_n
        for name, expr_tuple in self.sub_defs.items():
            clean_name = name.replace("{", "").replace("}", "")
            self._convert_expr_to_poly(clean_name, expr_tuple)
        
        # 2. Convertir las ecuaciones de estado principales
        for var, expr_tuple in self.optimized_f.items():
            lhs = f"{var}[t+1]"
            self._convert_expr_to_poly(lhs, expr_tuple)
            
        print(f"  [PolyConverter] ...Conversión completada. {self.existential_vars_count} variables existenciales introducidas.")
        return self.polynomial_system

    def _convert_expr_to_poly(self, target_var, expr):
        """
        Función principal recursiva. Traduce una expresión y añade las
        ecuaciones resultantes al sistema.

        Args:
            target_var (str): La variable que recibirá el resultado de la expresión.
            expr: La tupla del AST de la expresión.

        Returns:
            str: El nombre de la variable que contiene el resultado final.
        """
        if not isinstance(expr, tuple):
            # Es una asignación simple: target = expr
            self.polynomial_system.append(f"{target_var} - ({expr}) = 0")
            return expr

        op = expr[0]
        # Primero, nos aseguramos de que todos los operandos estén resueltos.
        arg_vars = [self._resolve_operand(arg) for arg in expr[1:]]

        # Ahora manejamos el operador actual
        if op in ('+', '-', '*'):
            # target = arg1 op arg2  =>  target - (arg1 op arg2) = 0
            self.polynomial_system.append(f"{target_var} - ({arg_vars[0]} {op} {arg_vars[1]}) = 0")
        
        elif op == 'neg':
            self.polynomial_system.append(f"{target_var} - (-{arg_vars[0]}) = 0")
        
        elif op == 'if':
            # target = c * a + (1-c) * b
            cond, val_true, val_false = arg_vars
            self.polynomial_system.append(f"{target_var} - (({cond}) * ({val_true}) + (1 - {cond}) * ({val_false})) = 0")

        # --- El núcleo de la conversión: Lógica a Polinomios ---
        
        elif op == '==': # target = (a == b)
            # Esto es 1 si a-b=0, y 0 si no.
            # Se logra con el "truco del inverso":
            # 1. (a - b) * e_0 = 1 - target  (Si a!=b, e_0 es el inverso. Si a=b, 1-target=0)
            # 2. (target) * (a - b) = 0      (Si target=1, entonces a=b)
            # 3. target * (1 - target) = 0   (Asegura que target es 0 o 1)
            a, b = arg_vars
            e0 = self._new_e_var()
            self.polynomial_system.append(f"({a}) - ({b})) * {e0} - (1 - {target_var}) = 0")
            self.polynomial_system.append(f"{target_var} * (({a}) - ({b})) = 0")
            self.polynomial_system.append(f"{target_var} * (1 - {target_var}) = 0")

        elif op == '<=': # target = (a <= b)
            # Equivale a target=1 si (b-a) >= 0, y target=0 si no.
            # 1. (b - a) - (e0^2 + e1^2 + e2^2 + e3^2) = 0   (si target=1, b-a es suma de 4 cuadrados)
            # 2. (a - b - 1) - (e4^2 + ...) = 0             (si target=0, a-b-1 es suma de 4 cuadrados)
            # 3. target * (ecuación_1) = 0
            # 4. (1-target) * (ecuación_2) = 0
            # 5. target * (1-target) = 0
            a, b = arg_vars
            e = [self._new_e_var() for _ in range(8)]
            sum_sq_1 = f"({e[0]}^2 + {e[1]}^2 + {e[2]}^2 + {e[3]}^2)"
            sum_sq_2 = f"({e[4]}^2 + {e[5]}^2 + {e[6]}^2 + {e[7]}^2)"
            
            # (target=1) => b-a es no-negativo
            self.polynomial_system.append(f"{target_var} * (({b}) - ({a}) - {sum_sq_1}) = 0")
            # (target=0) => a-b-1 es no-negativo (o sea, a > b)
            self.polynomial_system.append(f"(1 - {target_var}) * (({a}) - ({b}) - 1 - {sum_sq_2}) = 0")
            # Asegura que target es 0 o 1
            self.polynomial_system.append(f"{target_var} * (1 - {target_var}) = 0")

        else: # Reducir otros operadores a los ya implementados
            # a < b   -> a <= b - 1
            # a > b   -> b < a
            # a >= b  -> b <= a
            # a != b  -> 1 - (a == b)
            # a && b  -> a * b
            # a || b  -> a + b - a*b
            a, b = arg_vars
            if op == '&&': self.polynomial_system.append(f"{target_var} - ({a} * {b}) = 0")
            elif op == '||': self.polynomial_system.append(f"{target_var} - ({a} + {b} - {a} * {b}) = 0")
            else:
                # Si es una comparación, creamos una variable intermedia para el resultado
                temp_res = self._new_e_var()
                if op == '!=':
                    self._convert_expr_to_poly(temp_res, ('==', expr[1], expr[2]))
                    self.polynomial_system.append(f"{target_var} - (1 - {temp_res}) = 0")
                elif op == '<':
                    self._convert_expr_to_poly(target_var, ('<=', expr[1], ('-', expr[2], 1)))
                elif op == '>=':
                    self._convert_expr_to_poly(target_var, ('<=', expr[2], expr[1]))
                elif op == '>':
                    self._convert_expr_to_poly(target_var, ('<', expr[2], expr[1]))

        return target_var

    def _resolve_operand(self, operand):
        """
        Asegura que un operando sea una variable simple. Si es una expresión,
        la convierte a una variable temporal y devuelve su nombre.
        """
        if not isinstance(operand, tuple):
            return str(operand).replace("{", "").replace("}", "") # Es una constante o variable
        
        # Es una sub-expresión que necesita ser resuelta primero
        temp_var = self._new_e_var()
        self._convert_expr_to_poly(temp_var, operand)
        return temp_var