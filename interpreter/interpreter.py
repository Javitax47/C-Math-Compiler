import sys
import re

class EquationEngine:
    """
    Versión final que contiene la implementación CORRECTA del algoritmo de Kahn
    para el ordenamiento topológico.
    """

    def __init__(self, filepath):
        # ... (código sin cambios)
        self.equations = {}
        self.execution_plan = []
        self.state_vars = set()
        self._load_and_parse(filepath)
        self._build_execution_plan()
        print("[Engine] Motor de ecuaciones inicializado y listo.")

    def get_state_variables(self):
        # ... (código sin cambios)
        return list(self.state_vars)

    def _load_and_parse(self, filepath):
        # ... (código sin cambios)
        print(f"[Engine] Cargando y analizando {filepath}...")
        try:
            with open(filepath, 'r') as f:
                for line in f:
                    if ' := ' not in line: continue
                    var, expr_str = line.strip().split(' := ', 1)
                    self.equations[var] = expr_str
                    if '[t+1]' in var: self.state_vars.add(var.split('[')[0])
            print(f"[Engine] ...Análisis completado.")
        except FileNotFoundError:
            print(f"Error: No se pudo encontrar el archivo de entrada '{filepath}'", file=sys.stderr)
            sys.exit(1)

    # --- LÓGICA DE ORDENAMIENTO FINAL, DEFINITIVA Y CORRECTA ---
    def _build_execution_plan(self):
        print("[Engine] Construyendo plan de ejecución (Algoritmo de Kahn)...")
        
        # 1. Construir el grafo de adyacencia (qué nodos apuntan a qué otros)
        #    y calcular los grados de entrada.
        adj = {var: [] for var in self.equations}
        in_degree = {var: 0 for var in self.equations}
        
        all_possible_nodes = set(self.equations.keys())
        for var, expr in self.equations.items():
            deps = set(re.findall(r'\b[a-zA-Z0-9_\[\]\+]+?\b', expr))
            # Quitar las dependencias que son números
            deps = {dep for dep in deps if not dep.isdigit()}
            
            # El grado de entrada de 'var' es el número de dependencias que son OTRAS ecuaciones.
            in_degree[var] = len(deps.intersection(all_possible_nodes))
            
            # Construir el grafo inverso para la propagación
            for dep in deps:
                if dep in adj:
                    adj[dep].append(var)

        # 2. Inicializar la cola con todos los nodos que no tienen dependencias INTERNAS
        #    (su grado de entrada es 0).
        queue = [var for var, degree in in_degree.items() if degree == 0]
        
        sorted_order = []
        while queue:
            var = queue.pop(0)
            sorted_order.append(var)
            
            # Decrementar el grado de los nodos que dependen de la variable actual
            if var in adj:
                for neighbor in adj[var]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        # 3. Verificación final
        if len(sorted_order) != len(self.equations):
            unresolved_nodes = set(self.equations.keys()) - set(sorted_order)
            print("Error: Se ha detectado un ciclo en el grafo de dependencias.", file=sys.stderr)
            print("Variables que no se pudieron resolver:", unresolved_nodes, file=sys.stderr)
            raise RuntimeError("¡Error! El grafo de dependencias no se pudo resolver.")
            
        self.execution_plan = sorted_order
        print(f"[Engine] ...Plan de ejecución de {len(self.execution_plan)} pasos construido.")

    def _eval_expression(self, expr_str, context):
        # ... (código sin cambios hasta la línea 92) ...
        if '(' not in expr_str:
            if expr_str in context: return context[expr_str]
            try: return int(expr_str)
            except ValueError: raise NameError(f"Variable o valor no reconocido: {expr_str}")
        
        match = re.match(r'([a-zA-Z_&|=!<>+*/-]+)\((.*)\)', expr_str)
        if not match: raise SyntaxError(f"Formato de expresión no válido: {expr_str}")
        op, args_str = match.groups()

        # --- INICIO DE LA CORRECCIÓN ---
        # El regex de split (re.split) es incorrecto para paréntesis anidados.
        # Se reemplaza por un divisor manual que respeta el balance de paréntesis.
        args_raw = []
        balance = 0
        current_arg_start = 0
        
        # Manejar el caso de una cadena de argumentos vacía (ej: FUNC())
        if not args_str:
            args = []
        else:
            for i, char in enumerate(args_str):
                if char == '(':
                    balance += 1
                elif char == ')':
                    balance -= 1
                elif char == ',' and balance == 0:
                    # Se encontró una coma en el nivel superior (balance 0)
                    args_raw.append(args_str[current_arg_start:i])
                    current_arg_start = i + 1
            
            # Añadir el último argumento (o el único si no había comas)
            args_raw.append(args_str[current_arg_start:])
            
            args = [self._eval_expression(arg.strip(), context) for arg in args_raw if arg]
        # --- FIN DE LA CORRECCIÓN ---

        op_map = {
            'if': lambda a, b, c: b if a else c,
            '+': lambda a, b: a + b, '-': lambda a, b: a - b,
            '*': lambda a, b: a * b, '/': lambda a, b: a // b,
            'neg': lambda a: -a,
            '==': lambda a, b: 1 if a == b else 0, '!=': lambda a, b: 1 if a != b else 0,
            '>': lambda a, b: 1 if a > b else 0, '<': lambda a, b: 1 if a < b else 0,
            '>=': lambda a, b: 1 if a >= b else 0, '<=': lambda a, b: 1 if a <= b else 0,
            '&&': lambda a, b: 1 if a and b else 0, '||': lambda a, b: 1 if a or b else 0
        }
        if op in op_map:
            try:
                return op_map[op](*args)
            except TypeError:
                print(f"Error: Número incorrecto de argumentos para el operador '{op}'", file=sys.stderr)
                print(f"       Expresión: {expr_str}", file=sys.stderr)
                print(f"       Argumentos evaluados: {args}", file=sys.stderr)
                raise
        raise ValueError(f"Operador desconocido: {op}")

    def compute_next_state(self, current_state, inputs):
        # ... (código sin cambios)
        context = {**current_state, **inputs}
        for var_to_compute in self.execution_plan:
            expression = self.equations[var_to_compute]
            value = self._eval_expression(expression, context)
            context[var_to_compute] = value
        next_state = {}
        for var in self.state_vars:
            key_t1 = f"{var}[t+1]"
            if key_t1 in context: next_state[var] = int(context[key_t1])
        return next_state