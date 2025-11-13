import re
from collections import defaultdict

class LatexExporter:
    """
    Toma el AST de tuplas de la F-Function, lo optimiza
    y lo exporta como un documento LaTeX con secciones
    optimizadas y sin optimizar, permitiendo saltos de página.
    """
    def __init__(self, f_function_tuples, state_vars, input_vars):
        self.f_function = f_function_tuples
        self.state_vars = state_vars
        self.input_vars = input_vars
        
        self.sub_map = {}
        self.sub_defs = {}
        self.sub_counter = 0

    def export(self):
        """Punto de entrada. Optimiza y genera el string LaTeX."""
        print("  [Exporter] Iniciando optimización (CSE)...")
        self._optimize_cse()
        print(f"  [Exporter] ...Optimización completada. {len(self.sub_defs)} subexpresiones comunes encontradas.")
        
        print("  [Exporter] Generando documento LaTeX...")
        return self._generate_latex_string()

    # --- 1. Optimización (CSE) ---
    # (Sin cambios en esta sección)
    def _optimize_cse(self):
        counts = defaultdict(int)
        for expr_tuple in self.f_function.values():
            self._collect_subexpressions(expr_tuple, counts)
            
        for expr_tuple, count in counts.items():
            if count > 1 and len(str(expr_tuple)) > 10: 
                sub_name = f"C_{{{self.sub_counter}}}"
                self.sub_map[expr_tuple] = sub_name
                self.sub_defs[sub_name] = expr_tuple
                self.sub_counter += 1
                
        optimized_f_func = {}
        for var, expr_tuple in self.f_function.items():
            optimized_f_func[var] = self._replace_subexpressions(expr_tuple)
        
        optimized_sub_defs = {}
        for name, expr_tuple in self.sub_defs.items():
            op = expr_tuple[0]
            args = [self._replace_subexpressions(child) for child in expr_tuple[1:]]
            optimized_sub_defs[name] = (op,) + tuple(args)
            
        self.f_function = optimized_f_func
        self.sub_defs = optimized_sub_defs

    def _collect_subexpressions(self, expr, counts):
        if not isinstance(expr, tuple):
            return
        counts[expr] += 1
        for child in expr[1:]:
            self._collect_subexpressions(child, counts)

    def _replace_subexpressions(self, expr):
        if not isinstance(expr, tuple):
            return expr
        if expr in self.sub_map:
            return self.sub_map[expr]
        op = expr[0]
        args = [self._replace_subexpressions(child) for child in expr[1:]]
        return (op,) + tuple(args)

    # --- 2. Formateo LaTeX ---

    def _generate_latex_string(self):
        """Construye el archivo .tex final con todas las secciones."""
        # --- Cabeceras y texto introductorio ---
        if self.input_vars:
            input_list = ", ".join([f"{self._format_var(v)}" for v in self.input_vars])
            input_text = f"Las variables de entrada detectadas son: ${input_list}$."
        else:
            input_text = "No se detectaron variables de entrada."
        
        header = r"""
\documentclass[12pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{lmodern}
\usepackage{amssymb}

\allowdisplaybreaks

\title{Función de Transición (F) de Pong}
\author{Compilador Diophantus}
\date{\today}

\begin{document}
\maketitle
\section*{Función de Transición $S_{t+1} = F(S_t, I_t)$}
"""
        intro_text = f"Las siguientes ecuaciones definen el estado de cada variable en el fotograma $t+1$ (\\textbf{{Estado S$_{{t+1}}$}}) basándose únicamente en el estado en $t$ (\\textbf{{Estado S$_t$}}) y las entradas en $t$ (\\textbf{{Entradas I$_t$}}). {input_text}\n"
        explanation_section = r"""
\section*{El Proceso de Cálculo y Optimización}
Para generar estas ecuaciones, el compilador "aplana" la lógica secuencial del código C en un solo paso de cálculo.
\begin{enumerate}
    \item \textbf{Aplanamiento a Aritmética:} La lógica procedural (bucles, \texttt{if}, variables temporales) se convierte en un conjunto de expresiones matemáticas puras. La sentencia \texttt{if (C) \{ A \} else \{ B \}} se transforma en: $(C \cdot A) + ((1 - C) \cdot B)$.
    \item \textbf{Sustitución Completa:} Todas las variables auxiliares se sustituyen hasta que las ecuaciones solo dependen del estado anterior ($S_t$). Esto genera expresiones muy grandes, como se ve en la primera sección.
    \item \textbf{Eliminación de Subexpresiones Comunes (CSE):} Para hacer las ecuaciones manejables, se buscan expresiones que se repiten (ej. \texttt{b + d}), se les asigna un nombre (ej. $C_0, C_1, ...$) y se calculan una sola vez. Las ecuaciones finales se reescriben usando estos componentes, resultando en una versión optimizada y más legible.
\end{enumerate}
A continuación se muestran los resultados de este proceso.
"""
        
        # --- Sección 1: Ecuaciones SIN optimizar ---
        unoptimized_header = r"""
\subsection*{Ecuaciones de Estado (Sin Optimizar)}
Esta es la forma "pura" de la función de transición. Cada ecuación es matemáticamente completa, mostrando la dependencia total del estado anterior $S_t$ sin cálculos intermedios.
\begin{align*}
"""
        unoptimized_eqs = []
        for var in sorted(self.state_vars):
            expr_tuple = self.f_function.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            rhs = self._format_expanded_latex(expr_tuple)
            if len(rhs) > 75: # El umbral para el parbox
                rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            unoptimized_eqs.append(f"{lhs} {rhs}")
        unoptimized_section = unoptimized_header + " \\\\\n".join(unoptimized_eqs) + "\n\\end{align*}\n"

        # --- Sección 2: Definiciones CSE ---
        cse_section = ""
        if self.sub_defs:
            cse_header = r"""
\subsection*{Definiciones de Cálculos Comunes (CSE)}
Estas son las subexpresiones que se repiten y que han sido extraídas. Representan los cálculos intermedios de la lógica del juego.
\begin{align*}
"""
            sub_eqs = []
            sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
            
            for name, expr_tuple in sorted_defs:
                lhs = f"{name} &="
                rhs = self._format_tuple_to_latex(expr_tuple)
                if len(rhs) > 75:
                    rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
                sub_eqs.append(f"{lhs} {rhs}")
            cse_section = cse_header + " \\\\\n".join(sub_eqs) + "\n\\end{align*}\n"

        # --- Sección 3: Ecuaciones OPTIMIZADAS ---
        optimized_header = r"""
\subsection*{Ecuaciones de Estado Finales (Optimizadas)}
Esta es la versión final y simplificada. Utiliza las definiciones de $C_n$ para ser más compacta y legible.
\begin{align*}
"""
        optimized_eqs = []
        for var in sorted(self.state_vars):
            expr_tuple = self.f_function.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            rhs = self._format_tuple_to_latex(expr_tuple)
            if len(rhs) > 75:
                rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            optimized_eqs.append(f"{lhs} {rhs}")
        optimized_section = optimized_header + " \\\\\n".join(optimized_eqs) + "\n\\end{align*}\n"
        
        footer = r"""\end{document}"""
        return (header + intro_text + explanation_section + 
                unoptimized_section + cse_section + optimized_section + footer)

    # --- Métodos de formateo (_format_var, _format_tuple_to_latex, etc.) ---
    # (Sin cambios en estas funciones auxiliares)
    def _format_var(self, var_name):
        if var_name.startswith("C_"):
            return var_name
        if "_" in var_name:
            safe_name = var_name.replace("_", r"\_")
            return f"\\text{{{safe_name}}}"
        return var_name

    def _format_tuple_to_latex(self, expr):
        if not isinstance(expr, tuple):
            if isinstance(expr, int): return str(expr)
            if isinstance(expr, str): return self._format_var(expr)
            if expr is None: return "0"
            return str(expr)
        
        op = expr[0]
        args = [self._format_tuple_to_latex(e) for e in expr[1:]]
        
        if op == 'if': return f"({args[0]} \\cdot {args[1]} + (1 - {args[0]}) \\cdot {args[2]})"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'):
            op_latex = r" \cdot " if op == '*' else f" {op} "
            return f"({args[0]}{op_latex}{args[1]})"
        if op in ('==', '!=', '>', '<', '>=', '<=', '&&', '||'):
            op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}
            return f"({args[0]} {op_map[op]} {args[1]})"
        return f"OP_{op}(?)"

    def _format_expanded_latex(self, expr):
        if isinstance(expr, str) and expr in self.sub_defs:
            return self._format_expanded_latex(self.sub_defs[expr])

        if not isinstance(expr, tuple):
            if isinstance(expr, int): return str(expr)
            if isinstance(expr, str): return self._format_var(expr)
            if expr is None: return "0"
            return str(expr)

        op = expr[0]
        args = [self._format_expanded_latex(e) for e in expr[1:]]

        if op == 'if': return f"({args[0]} \\cdot {args[1]} + (1 - {args[0]}) \\cdot {args[2]})"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'):
            op_latex = r" \cdot " if op == '*' else f" {op} "
            return f"({args[0]}{op_latex}{args[1]})"
        if op in ('==', '!=', '>', '<', '>=', '<=', '&&', '||'):
            op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}
            return f"({args[0]} {op_map[op]} {args[1]})"
        return f"OP_{op}(?)"