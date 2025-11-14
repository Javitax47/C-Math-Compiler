import re

class LatexExporter:
    """
    Generador de informes final. Consolida todos los artefactos de la compilación
    (ecuaciones optimizadas, sistema polinómico, ecuación única P=0) en un
    único documento LaTeX, con explicaciones detalladas para cada sección.
    """
    def __init__(self, unoptimized_f, optimized_f, sub_defs, state_vars, input_vars,
                 poly_system, single_poly_equation, poly_converter_info):
        """
        Inicializa el exportador con todos los datos generados durante la compilación.
        """
        self.unoptimized_f = unoptimized_f
        self.optimized_f = optimized_f
        self.sub_defs = sub_defs
        self.state_vars = state_vars
        self.input_vars = input_vars
        self.poly_system = poly_system
        self.single_poly_equation = single_poly_equation
        self.poly_converter_info = poly_converter_info

    def export(self):
        """Punto de entrada. Genera el string LaTeX completo del informe."""
        print("  [Exporter] Ensamblando informe final en LaTeX...")
        
        # Construir cada sección del documento
        header = self._build_header()
        intro = self._build_intro()
        part1_transition_func = self._build_transition_function_section()
        part2_polynomial_conv = self._build_polynomial_conversion_section()
        footer = r"\end{document}"

        return header + intro + part1_transition_func + part2_polynomial_conv + footer

    # --- Métodos de Construcción de Secciones ---

    def _build_header(self):
        return r"""
\documentclass[12pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{geometry}
\geometry{a4paper, margin=1in}
\usepackage{lmodern}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{xcolor}

\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.95,0.95,0.92}

\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\footnotesize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}
\lstset{style=mystyle}

\allowdisplaybreaks

\title{Análisis Matemático de un Programa en C \\ \large Generado por Project Diophantus}
\author{}
\date{\today}
"""

    def _build_intro(self):
        state_list = ", ".join(sorted(self.state_vars))
        input_list = ", ".join(sorted(list(self.input_vars))) if self.input_vars else "ninguna"
        
        return f"""
\\begin{{document}}
\\maketitle

\\section*{{Resumen Ejecutivo}}
Este documento presenta la traducción completa de un programa de software escrito en C a un objeto matemático puro: un sistema de ecuaciones diofánticas. El proceso demuestra la equivalencia fundamental entre la computación (algoritmos) y la teoría de números (polinomios), como lo postula el Teorema de Matiyasevich (MRDP).

El compilador ha analizado el código fuente y ha extraído las siguientes componentes clave para describir una única transición de estado (un "fotograma"):
\\begin{{itemize}}
    \\item \\textbf{{Variables de Estado ($S_t$):}} Las variables que definen el estado del sistema en un instante $t$. Para este programa, son: {state_list}.
    \\item \\textbf{{Variables de Entrada ($I_t$):}} Las variables que representan la interacción con el exterior en el instante $t$. Para este programa, son: {input_list}.
\\end{{itemize}}

El documento se divide en dos partes principales, que corresponden a las dos grandes fases de la traducción:
\\begin{{enumerate}}
    \\item \\textbf{{La Función de Transición de Estado:}} Muestra cómo la lógica procedural del programa (bucles, condicionales) se "aplana" en un sistema de ecuaciones de asignación $S_{{t+1}} = F(S_t, I_t)$, y cómo este sistema se optimiza para revelar su estructura.
    \\item \\textbf{{La Conversión a Polinomio Puro:}} Muestra cómo el sistema de asignación, que aún contiene operadores lógicos, se convierte en un sistema de ecuaciones diofánticas puras (solo usando suma, resta y multiplicación), cumpliendo con el objetivo teórico final del proyecto.
\\end{{enumerate}}
"""

    def _build_transition_function_section(self):
        # --- Unoptimized Section ---
        unoptimized_eqs_str = []
        for var in sorted(self.state_vars):
            expr_tuple = self.unoptimized_f.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="
            rhs = self._format_expanded_latex(expr_tuple, self.sub_defs)
            if len(rhs.replace(" ", "")) > 80: rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            unoptimized_eqs_str.append(f"{lhs} {rhs}")
        unoptimized_section = "\\\\\n".join(unoptimized_eqs_str)

        # --- CSE Section ---
        cse_section_content = ""
        if self.sub_defs:
            sub_eqs = []
            sorted_defs = sorted(self.sub_defs.items(), key=lambda item: int(re.search(r'\d+', item[0]).group()))
            for name, expr_tuple in sorted_defs:
                lhs = f"{self._format_var(name)} &="; rhs = self._format_tuple_to_latex(expr_tuple)
                if len(rhs.replace(" ", "")) > 80: rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
                sub_eqs.append(f"{lhs} {rhs}")
            cse_section_content = f"""
\\subsection*{{Definiciones de Cálculos Comunes (CSE)}}
Para simplificar y hacer las ecuaciones manejables, el sistema busca expresiones que se repiten (ej. la lógica de movimiento de una pala), les asigna un nombre simbólico (ej. $C_0, C_1, \\dots$) y las calcula una sola vez. Estas definiciones representan los bloques de construcción lógicos del programa.
\\begin{{align*}}
{" \\\\\n".join(sub_eqs)}
\\end{{align*}}
"""
        # --- Optimized Section ---
        optimized_eqs_str = []
        for var in sorted(self.state_vars):
            expr_tuple = self.optimized_f.get(var, var)
            lhs = f"{self._format_var(var)}[t+1] &="; rhs = self._format_tuple_to_latex(expr_tuple)
            if len(rhs.replace(" ", "")) > 80: rhs = f"\\parbox[t]{{0.8\\linewidth}}{{{rhs}}}"
            optimized_eqs_str.append(f"{lhs} {rhs}")
        optimized_section = "\\\\\n".join(optimized_eqs_str)

        return f"""
\\part{{La Función de Transición de Estado}}
\\section{{Aplanamiento y Optimización}}
El primer paso consiste en convertir la lógica imperativa del bucle principal del programa en una función matemática estática, $F$. Esto se logra mediante un proceso de "aplanamiento" que transforma construcciones como `if-else` en expresiones aritméticas y sustituye todas las variables temporales hasta que cada ecuación solo dependa del estado anterior ($S_t$) y las entradas ($I_t$).

\\subsection*{{Ecuaciones de Estado (Forma Pura, Sin Optimizar)}}
Esta es la forma "pura" de la función de transición. Cada ecuación es matemáticamente autocontenida y muestra la dependencia total del estado anterior. Su complejidad y repetición visual reflejan la necesidad de optimización.
\\begin{{align*}}
{unoptimized_section}
\\end{{align*}}
{cse_section_content}
\\subsection*{{Ecuaciones de Estado Finales (Optimizadas con CSE)}}
Esta es la versión final y simplificada de la función de transición. Utiliza las definiciones de $C_n$ para ser más compacta, legible y eficiente. Esta forma es la que más se asemeja a cómo un humano estructuraría los cálculos.
\\begin{{align*}}
{optimized_section}
\\end{{align*}}
"""

    def _build_polynomial_conversion_section(self):
        e_vars_count = self.poly_converter_info['existential_vars_count']
        num_equations = self.poly_converter_info['num_equations']
        
        poly_system_str = "\\\\\n".join([self._format_poly_system_line(line) for line in self.poly_system])
        single_poly_str = self._format_single_poly(self.single_poly_equation)

        return f"""
\\part{{Conversión a Polinomio Puro}}
\\section{{Traducción a Ecuaciones Diofánticas}}
El paso final y más profundo es convertir la función de transición (que aún contiene operadores lógicos como `==`, `<`, etc.) en un sistema que solo utiliza aritmética entera (suma, resta, multiplicación). Esto se logra introduciendo variables existenciales ($e_n$) y aplicando trucos de la teoría de números, como el Teorema de los Cuatro Cuadrados de Lagrange para manejar las desigualdades.

El proceso ha introducido \\textbf{{{e_vars_count} variables existenciales}} para producir un sistema de \\textbf{{{num_equations} ecuaciones puras}}.

\\subsection*{{Sistema de Ecuaciones Diofánticas Puras (Forma Práctica)}}
Esta es la representación más útil para aplicaciones de ingeniería, como la simulación o la síntesis de hardware. Es un sistema de ecuaciones interdependientes que deben satisfacerse simultáneamente. Cada línea representa un cálculo simple o una restricción lógica.
\\begin{{align*}}
{poly_system_str}
\\end{{align*}}
\\subsection*{{Ecuación Polinómica Única (Forma Teórica P=0)}}
Por completitud teórica, el sistema anterior puede ser combinado en una única ecuación mediante la suma de los cuadrados de cada ecuación. Una solución entera a esta única y masiva ecuación corresponde a una transición de estado válida del programa original. Esta es la forma final que demuestra el Teorema MRDP.
\\begin{{align*}}
{single_poly_str}
\\end{{align*}}
"""

    # --- Métodos de Formateo de Expresiones ---

    def _format_poly_expression(self, expr_str):
        s = expr_str.replace('*', r' \cdot ')
        s = re.sub(r'([a-zA-Z0-9_]+)\[t\+1\]', r'\1[t+1]', s)
        s = re.sub(r'([Ce])_(\d+)', r'\1_{\2}', s)
        s = re.sub(r'\^2', r'^{2}', s)
        return s

    def _format_poly_system_line(self, line):
        parts = line.split(' = ', 1)
        if len(parts) == 2:
            lhs = self._format_poly_expression(parts[0]); rhs = self._format_poly_expression(parts[1])
            return f"{lhs} &= {rhs}"
        return self._format_poly_expression(line) + "&="

    def _format_single_poly(self, line):
        terms = line.split(' + '); last_term_parts = terms[-1].split(' = '); terms[-1] = last_term_parts[0]
        formatted_terms = [self._format_poly_expression(term) for term in terms]
        output_lines = []; current_line = ""; line_threshold = 90
        for term in formatted_terms:
            separator = " + " if current_line else ""
            if len(current_line) + len(separator) + len(term) > line_threshold and current_line:
                output_lines.append(current_line); current_line = term
            else:
                current_line += separator + term
        if current_line: output_lines.append(current_line)
        if not output_lines: return "& = 0"
        # Usamos el estilo robusto de alineación con '& + ...' en la nueva línea
        body = (" \\\\\n& + ").join(output_lines)
        return f"& {body} = 0"

    def _format_var(self, var_name):
        if var_name.startswith("C_"): return var_name.replace("{", "").replace("}", "")
        if "_" in var_name: return f"\\text{{{var_name.replace('_', r'\\_')}}}"
        return var_name

    def _format_tuple_to_latex(self, expr):
        if not isinstance(expr, tuple): return self._format_var(str(expr))
        op = expr[0]; args = [self._format_tuple_to_latex(e) for e in expr[1:]]
        op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}
        if op == 'if': return f"({args[0]} \\cdot {args[1]} + (1 - {args[0]}) \\cdot {args[2]})"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'): op_latex = r" \cdot " if op == '*' else f" {op} "; return f"({args[0]}{op_latex}{args[1]})"
        if op in op_map: return f"({args[0]} {op_map[op]} {args[1]})"
        return f"\\text{{OP}}_{op}({', '.join(args)})"

    def _format_expanded_latex(self, expr, sub_defs):
        if isinstance(expr, str) and expr in sub_defs: return self._format_expanded_latex(sub_defs[expr], sub_defs)
        if not isinstance(expr, tuple): return self._format_var(str(expr))
        op = expr[0]; args = [self._format_expanded_latex(e, sub_defs) for e in expr[1:]]
        op_map = {'==': '=', '!=': r'\neq', '>': '>', '<': '<', '>=': r'\geq', '<=': r'\leq', '&&': r'\land', '||': r'\lor'}
        if op == 'if': return f"({args[0]} \\cdot ({args[1]}) + (1 - {args[0]}) \\cdot ({args[2]}))"
        if op == 'neg': return f"(-{args[0]})"
        if op in ('+', '-', '*', '/'): op_latex = r" \cdot " if op == '*' else f" {op} "; return f"({args[0]}{op_latex}{args[1]})"
        if op in op_map: return f"({args[0]} {op_map[op]} {args[1]})"
        return f"\\text{{OP}}_{op}({', '.join(args)})"