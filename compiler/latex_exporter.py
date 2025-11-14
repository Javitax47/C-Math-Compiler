import re
from collections import defaultdict

class LatexExporter:
    """
    Toma el AST de tuplas de la F-Function, tanto en su forma
    original como optimizada, y lo exporta a un documento LaTeX
    bien estructurado y legible.

    El documento generado está diseñado para ser educativo, explicando
    el proceso de compilación y presentando los resultados de una
    manera clara y comparativa.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs, state_vars, input_vars):
        """
        Inicializa el exportador con todos los datos necesarios.

        Args:
            unoptimized_f (dict): La F-Function en su forma original, sin optimizar.
            optimized_f (dict): La F-Function optimizada con referencias a C_n.
            sub_defs (dict): Las definiciones de las subexpresiones comunes C_n.
            state_vars (list): La lista de variables de estado (S_t).
            input_vars (set): El conjunto de variables de entrada detectadas (I_t).
        """
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = state_vars
        self.input_vars = input_vars
        
    def export(self):
        """
        Punto de entrada principal. Genera el string LaTeX completo.

        Returns:
            str: El contenido completo del archivo .tex.
        """
        print("  [Exporter] Generando documento LaTeX...")
        return self._generate_latex_string()

    # --- Métodos de Construcción de LaTeX ---

    def _generate_latex_string(self):
        """Construye el archivo .tex final uniendo todas las secciones."""
        # --- Cabeceras y texto introductorio ---
        if self.input_vars:
            input_list = ", ".join([f"{self._format_var(v)}" for v in sorted(list(self.input_vars))])
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
\usepackage{graphicx}

\allowdisplaybreaks

\title{Análisis de la Función de Transición de Estado}
\author{Generado por Project Diophantus}
\date{\today}

\begin{document}
\maketitle
\section*{Función de Transición $S_{t+1} = F(S_t, I_t)$}
"""
        intro_text = f"""
Las siguientes ecuaciones definen el estado de cada variable en el fotograma $t+1$ (\\textbf{{Estado S$_{{t+1}}$}}) basándose únicamente en el estado en el fotograma $t$ (\\textbf{{Estado S$_t$}}) y las entradas en ese mismo instante (\\textbf{{Entradas I$_t$}}). {input_text}
"""
        explanation_section = r"""
\section*{El Proceso de Generación y Optimización}
Para derivar estas ecuaciones, el compilador transforma la lógica secuencial e imperativa del código C en un sistema de expresiones matemáticas puras y estáticas. Este proceso se realiza en varios pasos:
\begin{enumerate}
    \item \textbf{Aplanamiento a Aritmética:} La lógica procedural (bucles, sentencias \texttt{if}, variables temporales) se convierte en un conjunto de asignaciones matemáticas. La construcción \texttt{if (C) \{ A \} else \{ B \}} se transforma algebraicamente en la expresión: $(C \cdot A) + ((1 - C) \cdot B)$, asumiendo que C evalúa a 1 para verdadero y 0 para falso.
    \item \textbf{Sustitución Completa:} Todas las variables auxiliares (aquellas declaradas dentro del bucle) se sustituyen recursivamente hasta que cada ecuación de estado solo depende de las variables de estado del paso anterior ($S_t$) y las entradas ($I_t$). Esto resulta en expresiones muy grandes y repetitivas, como se muestra en la primera sección de resultados.
    \item \textbf{Eliminación de Subexpresiones Comunes (CSE):} Para simplificar y hacer las ecuaciones manejables, el sistema busca expresiones que se repiten (ej. \texttt{b + d}), les asigna un nombre simbólico (ej. $C_0, C_1, \dots$) y las calcula una sola vez. Las ecuaciones finales se reescriben utilizando estos componentes intermedios, resultando en una versión optimizada y mucho más legible que revela la estructura computacional subyacente.
\end{enumerate}
A continuación se muestran los resultados detallados de este proceso.
"""
        
        # --- Sección 1: Ecuaciones SIN optimizar ---
        unoptimized_header = r"""
\subsection*{Ecuaciones de Estado (Forma Pura, Sin Optimizar)}
Esta es la forma "pura" de la función de transición. Cada ecuación es matemáticamente autocontenida y muestra la dependencia total del estado anterior $S_t$ sin necesidad de cálculos intermedios. Su complejidad visual refleja la interconexión de la lógica del programa.
\begin{align*}
"""
        unoptimized_eqs = []
        for var in sorted(self.state_vars):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            # Usamos una función especial que expande las C_n para esta sección
            rhs = self._format_expanded_latex(expr_tuple, self.sub_defs)
            if len(rhs.replace(" ", "")) > 80: # El umbral para el parbox
                rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            unoptimized_eqs.append(f"{lhs} {rhs}")
        unoptimized_section = unoptimized_header + " \\\\\n".join(unoptimized_eqs) + "\n\\end{align*}\n"

        # --- Sección 2: Definiciones CSE ---
        cse_section = ""
        if self.sub_defs:
            cse_header = r"""
\subsection*{Definiciones de Cálculos Comunes (CSE)}
Estas son las subexpresiones que aparecen repetidamente en la lógica y que han sido extraídas para su reutilización. Representan los bloques de construcción computacionales del programa, como la detección de colisiones o la actualización de posiciones.
\begin{align*}
"""
            sub_eqs = []
            sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
            
            for name, expr_tuple in sorted_defs:
                lhs = f"{name} &="
                rhs = self._format_tuple_to_latex(expr_tuple)
                if len(rhs.replace(" ", "")) > 80:
                    rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
                sub_eqs.append(f"{lhs} {rhs}")
            cse_section = cse_header + " \\\\\n".join(sub_eqs) + "\n\\end{align*}\n"

        # --- Sección 3: Ecuaciones OPTIMIZADAS ---
        optimized_header = r"""
\subsection*{Ecuaciones de Estado Finales (Optimizadas con CSE)}
Esta es la versión final y simplificada de la función de transición. Utiliza las definiciones de $C_n$ para ser más compacta, legible y eficiente. Esta forma es la que más se asemeja a cómo un humano estructuraría los cálculos.
\begin{align*}
"""
        optimized_eqs = []
        for var in sorted(self.state_vars):
            expr_tuple = self.optimized_f.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            rhs = self._format_tuple_to_latex(expr_tuple)
            if len(rhs.replace(" ", "")) > 80:
                rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            optimized_eqs.append(f"{lhs} {rhs}")
        optimized_section = optimized_header + " \\\\\n".join(optimized_eqs) + "\n\\end{align*}\n"
        
        footer = r"""\end{document}"""
        return (header + intro_text + explanation_section + 
                unoptimized_section + cse_section + optimized_section + footer)

    # --- Métodos de Formateo de Expresiones ---

    def _format_var(self, var_name):
        """Formatea un nombre de variable para LaTeX, manejando C_n y guiones bajos."""
        if var_name.startswith("C_"):
            return var_name.replace("{", "").replace("}", "") # C_{0} -> C_0
        if "_" in var_name:
            safe_name = var_name.replace("_", r"\_")
            return f"\\text{{{safe_name}}}"
        return var_name

    def _format_tuple_to_latex(self, expr):
        """Convierte recursivamente un AST de tupla a una cadena LaTeX (versión optimizada)."""
        if not isinstance(expr, tuple):
            return self._format_var(str(expr))
        
        op = expr[0]
        args = [self._format_tuple_to_latex(e) for e in expr[1:]]
        
        op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}
        
        if op == 'if': return f"({args[0]} \\cdot {args[1]} + (1 - {args[0]}) \\cdot {args[2]})"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'):
            op_latex = r" \cdot " if op == '*' else f" {op} "
            return f"({args[0]}{op_latex}{args[1]})"
        if op in op_map:
            return f"({args[0]} {op_map[op]} {args[1]})"
        return f"\\text{{OP}}_{op}({', '.join(args)})"

    def _format_expanded_latex(self, expr, sub_defs):
        """Convierte recursivamente un AST, pero expandiendo las definiciones de C_n."""
        if isinstance(expr, str) and expr in sub_defs:
            # Si es un C_n, lo sustituimos por su definición y seguimos expandiendo
            return self._format_expanded_latex(sub_defs[expr], sub_defs)

        if not isinstance(expr, tuple):
            return self._format_var(str(expr))

        op = expr[0]
        args = [self._format_expanded_latex(e, sub_defs) for e in expr[1:]]

        op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}

        if op == 'if': return f"({args[0]} \\cdot ({args[1]}) + (1 - {args[0]}) \\cdot ({args[2]}))"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'):
            op_latex = r" \cdot " if op == '*' else f" {op} "
            return f"({args[0]}{op_latex}{args[1]})"
        if op in op_map:
            return f"({args[0]} {op_map[op]} {args[1]})"
        return f"\\text{{OP}}_{op}({', '.join(args)})"