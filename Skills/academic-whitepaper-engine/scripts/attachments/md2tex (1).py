#!/usr/bin/env python3
"""
MD2TeX: Markdown to LaTeX converter for symbolic operator documentation
Preserves UTF-8 symbols while ensuring proper rendering via XeLaTeX
Enhanced for experimental theoretical CS research workflows
"""

import re
import json
import sys
import subprocess
import argparse
import hashlib
import time
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set, Optional
import shutil

class SymbolRegistry:
    """Manages symbolic operators and their semantics"""
    
    def __init__(self, registry_path: Path = None):
        self.registry_path = registry_path or Path("symbols.json")
        self.symbols = self._load_registry()
        
    def _load_registry(self) -> Dict:
        """Load symbol registry from JSON"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"DEBUG: Loaded registry from {self.registry_path}, {len(data)} symbols.")
                print(f"DEBUG: '±' in registry: {'±' in data}")
                return data
        return self._create_default_registry()
    
    def _create_default_registry(self) -> Dict:
        """Create default symbol registry"""
        default = {
            "⊗": {
                "type": "binary_operator",
                "semantic": "tensor_product_in_frequency_space",
                "latex_fallback": "otimes",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "∇": {
                "type": "unary_operator",
                "semantic": "gradient_in_symbolic_space",
                "latex_fallback": "nabla",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "Ψ": {
                "type": "state_symbol",
                "semantic": "state_transformation_operator",
                "latex_fallback": "Psi",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "Φ": {
                "type": "state_symbol",
                "semantic": "phase_space_operator",
                "latex_fallback": "Phi",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "→": {
                "type": "transformation",
                "semantic": "symbolic_transformation",
                "latex_fallback": "rightarrow",
                "preserve_literal": True,
                "context": ["math", "prose"],
                "test_render": True
            },
            "∈": {
                "type": "relation",
                "semantic": "membership",
                "latex_fallback": "in",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "∀": {
                "type": "quantifier",
                "semantic": "universal_quantifier",
                "latex_fallback": "forall",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "∃": {
                "type": "quantifier",
                "semantic": "existential_quantifier",
                "latex_fallback": "exists",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "∑": {
                "type": "operator",
                "semantic": "summation",
                "latex_fallback": "sum",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            },
            "∫": {
                "type": "operator",
                "semantic": "integration",
                "latex_fallback": "int",
                "preserve_literal": True,
                "context": ["math"],
                "test_render": True
            }
        }
        self.save_registry(default)
        return default
    
    def save_registry(self, registry: Dict = None):
        """Save registry to JSON"""
        to_save = registry or self.symbols
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, indent=2, ensure_ascii=False)
    
    def is_registered(self, symbol: str) -> bool:
        """Check if symbol is registered"""
        return symbol in self.symbols
    
    def get_semantic(self, symbol: str) -> str:
        """Get semantic meaning of symbol"""
        return self.symbols.get(symbol, {}).get("semantic", "unknown")
    
    def get_contexts(self, symbol: str) -> List[str]:
        """Get valid contexts for symbol"""
        return self.symbols.get(symbol, {}).get("context", [])
    
    def should_test_render(self, symbol: str) -> bool:
        """Check if symbol should be tested for rendering"""
        return self.symbols.get(symbol, {}).get("test_render", False)


class SymbolLinter:
    """Lints documents for symbol usage"""
    
    def __init__(self, registry: SymbolRegistry):
        self.registry = registry
        self.issues = []
        self.usage_stats = defaultdict(lambda: {"count": 0, "contexts": [], "lines": []})
        
    def lint_file(self, filepath: Path) -> Tuple[List[str], Dict]:
        """Lint a markdown or tex file"""
        self.issues = []
        self.usage_stats = defaultdict(lambda: {"count": 0, "contexts": [], "lines": []})
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_code_block = False
        in_math_block = False
        
        for line_num, line in enumerate(lines, 1):
            # Track context
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if "$$" in line:
                in_math_block = not in_math_block
                
            # Detect context
            context = self._detect_context(line, in_code_block, in_math_block)
            
            # Find Unicode symbols
            for char in line:
                if ord(char) > 127:  # Non-ASCII
                    if not self.registry.is_registered(char):
                        self.issues.append(
                            f"Line {line_num}: Unregistered Unicode symbol '{char}' (U+{ord(char):04X})"
                        )
                    else:
                        valid_contexts = self.registry.get_contexts(char)
                        if context not in valid_contexts and "prose" not in valid_contexts:
                            self.issues.append(
                                f"Line {line_num}: Symbol '{char}' used in {context} context, "
                                f"but only valid in {valid_contexts}"
                            )
                        
                        self.usage_stats[char]["count"] += 1
                        self.usage_stats[char]["contexts"].append(context)
                        self.usage_stats[char]["lines"].append(line_num)
        
        return self.issues, dict(self.usage_stats)
    
    def _detect_context(self, line: str, in_code: bool, in_math: bool) -> str:
        """Detect the context of a line"""
        if in_code:
            return "code"
        if in_math or "$" in line:
            return "math"
        return "prose"
    
    def generate_report(self, issues: List[str], stats: Dict) -> str:
        """Generate lint report"""
        report = ["=" * 60]
        report.append("SYMBOL LINT REPORT")
        report.append("=" * 60)
        
        if issues:
            report.append("\n⚠ ISSUES FOUND:")
            for issue in issues:
                report.append(f"  • {issue}")
        else:
            report.append("\n✓ No issues found")
        
        report.append("\n" + "=" * 60)
        report.append("SYMBOL USAGE STATISTICS")
        report.append("=" * 60)
        
        for symbol, data in sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True):
            semantic = self.registry.get_semantic(symbol)
            context_counts = Counter(data["contexts"])
            report.append(f"\n{symbol} (U+{ord(symbol):04X}) - {semantic}")
            report.append(f"  Total: {data['count']} occurrences")
            report.append(f"  Contexts: {dict(context_counts)}")
            report.append(f"  Lines: {', '.join(map(str, data['lines'][:10]))}" + 
                         ("..." if len(data['lines']) > 10 else ""))
        
        return "\n".join(report)


class TensorNotationValidator:
    """Validates tensor notation consistency"""
    
    def validate(self, content: str) -> List[str]:
        """Validate tensor expressions"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check for unbalanced subscripts/superscripts
            if '_' in line or '^' in line:
                # Count braces in math mode
                if '$' in line:
                    math_parts = re.findall(r'\$([^\$]+)\$', line)
                    for math in math_parts:
                        open_braces = math.count('{')
                        close_braces = math.count('}')
                        if open_braces != close_braces:
                            issues.append(
                                f"Line {line_num}: Unbalanced braces in math expression"
                            )
                        
                        # Check for naked subscripts/superscripts
                        if re.search(r'[_^][^{]', math):
                            issues.append(
                                f"Line {line_num}: Naked subscript/superscript (use braces)"
                            )
        
        return issues


class MathNormalizer:
    """Normalizes math blocks without altering symbols"""
    
    def normalize(self, content: str) -> str:
        """Normalize math fencing in markdown"""
        lines = content.split('\n')
        normalized = []
        in_code_block = False
        
        for line in lines:
            # Track code blocks
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                normalized.append(line)
                continue
            
            if in_code_block:
                normalized.append(line)
                continue
            
            # Convert ```math blocks to $$
            if line.strip().startswith("```math"):
                normalized.append("$$")
                continue
            
            # Check if line looks like standalone math
            stripped = line.strip()
            if stripped and not any(x in stripped for x in ['#', '-', '*', '>', '```']):
                # Contains math symbols but no delimiters
                if self._has_math_content(stripped) and not ('$' in stripped):
                    # Wrap in display math
                    normalized.append(f"$$\n{line}\n$$")
                    continue
            
            normalized.append(line)
        
        return '\n'.join(normalized)
    
    def _has_math_content(self, line: str) -> bool:
        """Detect if line has mathematical content"""
        math_indicators = [
            '\\sum', '\\int', '\\frac', '\\partial', '\\mathcal',
            '\\left', '\\right', '\\overbrace', '\\underbrace',
            '=', '+', '-', '×', '÷', '∈', '∀', '∃', '∇', '⊗', '∑', '∫'
        ]
        return any(indicator in line for indicator in math_indicators)


class AdmonitionProcessor:
    """Processes markdown admonitions into LaTeX environments"""
    
    def process(self, content: str) -> str:
        """
        Transforms Markdown blockquotes into LaTeX environments.
        Matches: > [!THEOREM] Title
        """
        lines = content.split('\n')
        new_lines = []
        current_env = None
        env_content = []
        
        for line in lines:
            stripped = line.strip()
            
            # Detect start of environment
            match = re.match(r'>\s*\[!(THEOREM|DEFINITION|LEMMA|PROOF|NOTE|PROPOSITION|COROLLARY)\]\s*(.*)', 
                           stripped, re.IGNORECASE)
            if match:
                if current_env:
                    # Close previous environment
                    new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
                    new_lines.extend(env_content)
                    new_lines.append(f"\\end{{{current_env['type']}}}")
                    env_content = []
                
                env_type = match.group(1).lower()
                title = match.group(2).strip()
                title_opt = f"[{title}]" if title else ""
                
                current_env = {"type": env_type, "title": title_opt}
                continue
                
            # Handle body of environment
            if current_env and stripped.startswith('>'):
                content_line = line.replace('>', '', 1).lstrip()
                env_content.append(content_line)
                continue
                
            # Detect end of environment (non-blockquote line)
            if current_env and not stripped.startswith('>'):
                new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
                new_lines.extend(env_content)
                new_lines.append(f"\\end{{{current_env['type']}}}")
                current_env = None
                env_content = []
                new_lines.append(line)
                continue
                
            new_lines.append(line)
            
        # Close any remaining environment
        if current_env:
            new_lines.append(f"\\begin{{{current_env['type']}}}{current_env['title']}")
            new_lines.extend(env_content)
            new_lines.append(f"\\end{{{current_env['type']}}}")
            
        return '\n'.join(new_lines)


class CitationProcessor:
    """Processes custom citation formats"""
    
    def process(self, content: str) -> str:
        """
        Handles both traditional @cite and custom [[Author YEAR]] refs
        Supports experimental/unpublished sources
        """
        # Handle custom citations: [[Pribram 1991: Holographic Brain Theory]]
        content = re.sub(
            r'\[\[([^\]]+?)\s+(\d{4})[:\s]+([^\]]+)\]\]',
            r'\\cite[\3]{\1\2}',
            content
        )
        
        # Handle self-references: [[RSIA-Core-Theorem-3.2]]
        content = re.sub(
            r'\[\[(RSIA|TGP|RCF)-([^\]]+)\]\]',
            r'\\ref{\1-\2}',
            content
        )
        
        # Handle cross-references: [[#theorem-name]]
        content = re.sub(
            r'\[\[#([^\]]+)\]\]',
            r'\\ref{\1}',
            content
        )
        
        return content


class CrossReferenceLinker:
    """Manages cross-references and auto-labeling"""
    
    def __init__(self):
        self.labels = {}
        
    def process(self, content: str) -> str:
        """Add labels to theorems and handle cross-references"""
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            # Auto-label theorem environments
            if re.match(r'\\begin\{(theorem|definition|lemma|proposition|corollary)\}', line):
                env_match = re.search(r'\\begin\{(\w+)\}(?:\[([^\]]+)\])?', line)
                if env_match:
                    env_type = env_match.group(1)
                    title = env_match.group(2) or ""
                    # Create label from title
                    label = self._create_label(env_type, title)
                    new_lines.append(line)
                    new_lines.append(f"\\label{{{label}}}")
                    continue
            
            new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _create_label(self, env_type: str, title: str) -> str:
        """Create a label from environment type and title"""
        if title:
            clean_title = re.sub(r'[^\w\s-]', '', title.lower())
            clean_title = re.sub(r'[-\s]+', '-', clean_title)
            return f"{env_type}-{clean_title}"
        return f"{env_type}-{len(self.labels)}"


class MD2TeXConverter:
    """Main converter class"""
    
    def __init__(self, registry: SymbolRegistry, mode: str = "pub", engine: str = "xelatex"):
        self.registry = registry
        self.mode = mode
        self.engine = engine
        self.normalizer = MathNormalizer()
        self.admonition_processor = AdmonitionProcessor()
        self.citation_processor = CitationProcessor()
        self.xref_linker = CrossReferenceLinker()
        self.tensor_validator = TensorNotationValidator()
        
    def convert(self, input_path: Path, output_path: Path, template_path: Path = None, 
                bib_path: Path = None, add_version: bool = False):
        """Convert markdown to LaTeX"""
        # Read input
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate tensor notation
        tensor_issues = self.tensor_validator.validate(content)
        if tensor_issues:
            print("\n⚠ Tensor notation issues found:")
            for issue in tensor_issues:
                print(f"  • {issue}")
        
        # 1. Normalize math
        content = self.normalizer.normalize(content)
        
        # 2. Process admonitions
        content = self.admonition_processor.process(content)
        
        # 3. Process citations
        content = self.citation_processor.process(content)
        
        # 4. Annotate if in dev mode
        if self.mode == "dev":
            content = self._annotate_symbols(content)
        
        # 5. Add computational metadata if in compute mode
        if self.mode == "compute":
            content = self._add_byte_metadata(content)
        
        # 6. Add version info if requested
        if add_version:
            content = self._add_version_info(content, input_path)
        
        # Write intermediate markdown
        temp_md = output_path.with_suffix('.normalized.md')
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Convert with pandoc
        self._run_pandoc(temp_md, output_path, template_path, bib_path)
        
        # Process cross-references in LaTeX output
        if output_path.suffix == '.tex':
            with open(output_path, 'r', encoding='utf-8') as f:
                tex_content = f.read()
            tex_content = self.xref_linker.process(tex_content)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tex_content)
        
        # Clean up
        if temp_md.exists():
            temp_md.unlink()
    
    def _annotate_symbols(self, content: str) -> str:
        """Annotate symbols with semantic tags in dev mode"""
        for symbol, data in self.registry.symbols.items():
            semantic = data.get("semantic", "unknown")
            # Replace in math mode only
            pattern = re.escape(symbol)
            # Add subscript annotation
            replacement = f"{symbol}_{{\\text{{\\tiny [{semantic}]}}}}"
            content = re.sub(f'\\${pattern}\\$', f'${replacement}$', content)
        return content
    
    def _add_byte_metadata(self, content: str) -> str:
        """Add byte sequence metadata in compute mode"""
        metadata_lines = ["\n% === COMPUTATIONAL METADATA ==="]
        for symbol in self.registry.symbols.keys():
            byte_seq = symbol.encode('utf-8').hex()
            codepoint = f"U+{ord(symbol):04X}"
            metadata_lines.append(f"% {symbol}: {codepoint} (bytes: {byte_seq})")
        metadata_lines.append("% === END METADATA ===\n")
        return '\n'.join(metadata_lines) + content
    
    def _add_version_info(self, content: str, input_path: Path) -> str:
        """Add version and hash information"""
        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        version_info = f"""
% === VERSION INFO ===
% Document Hash: {content_hash}
% Source File: {input_path.name}
% Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
% === END VERSION INFO ===

"""
        return version_info + content
    
    def _run_pandoc(self, input_path: Path, output_path: Path, 
                    template_path: Path = None, bib_path: Path = None):
        """Run pandoc conversion"""
        cmd = [
            'pandoc',
            str(input_path),
            '-o', str(output_path),
            f'--pdf-engine={self.engine}',
            '-f', 'markdown',
            '-t', 'latex',
            '--standalone'
        ]
        
        if template_path and template_path.exists():
            cmd.extend(['--template', str(template_path)])
        
        if bib_path and bib_path.exists():
            cmd.extend(['--bibliography', str(bib_path), '--natbib'])
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"Pandoc error: {e.stderr}")
            raise


class PDFValidator:
    """Validates PDF output against source"""
    
    def validate(self, source_path: Path, pdf_path: Path, registry: SymbolRegistry) -> str:
        """Validate PDF rendering fidelity"""
        if not self._check_pdftotext():
            return "⚠ pdftotext not found. Install poppler-utils for validation."
        
        # Extract text from PDF
        try:
            result = subprocess.run(
                ['pdftotext', '-enc', 'UTF-8', str(pdf_path), '-'],
                capture_output=True,
                text=True,
                check=True
            )
            pdf_text = result.stdout
        except subprocess.CalledProcessError:
            return "✗ Failed to extract text from PDF"
        
        # Read source
        with open(source_path, 'r', encoding='utf-8') as f:
            source_text = f.read()
        
        # Check symbol preservation
        report = ["=" * 60, "PDF RENDER FIDELITY REPORT", "=" * 60, ""]
        
        missing = []
        preserved = []
        
        for symbol in registry.symbols.keys():
            source_count = source_text.count(symbol)
            pdf_count = pdf_text.count(symbol)
            
            if source_count > 0:
                if pdf_count == 0:
                    missing.append(f"✗ {symbol} (U+{ord(symbol):04X}): {source_count} in source, 0 in PDF")
                elif pdf_count < source_count:
                    missing.append(f"⚠ {symbol} (U+{ord(symbol):04X}): {source_count} in source, {pdf_count} in PDF")
                else:
                    preserved.append(f"✓ {symbol} (U+{ord(symbol):04X}): {source_count} occurrences preserved")
        
        if preserved:
            report.append("PRESERVED SYMBOLS:")
            report.extend(f"  {p}" for p in preserved)
            report.append("")
        
        if missing:
            report.append("MISSING/REDUCED SYMBOLS:")
            report.extend(f"  {m}" for m in missing)
        else:
            report.append("✓ All symbols preserved correctly!")
        
        return "\n".join(report)
    
    def _check_pdftotext(self) -> bool:
        """Check if pdftotext is available"""
        return shutil.which('pdftotext') is not None


class AppendixGenerator:
    """Generates symbolic operator reference appendix"""
    
    def __init__(self, registry: SymbolRegistry):
        self.registry = registry
    
    def generate(self, stats: Dict) -> str:
        """Generate LaTeX appendix"""
        lines = [
            "\\section*{SYMBOLIC OPERATOR REFERENCE}",
            "\\begin{table}[H]",
            "\\centering",
            "\\begin{tabular}{cllr}",
            "\\toprule",
            "Symbol & Semantic & Type & Usage \\\\",
            "\\midrule"
        ]
        
        # Sort by usage count
        sorted_symbols = sorted(stats.items(), key=lambda x: x[1]["count"], reverse=True)
        
        for symbol, data in sorted_symbols:
            info = self.registry.symbols.get(symbol, {})
            semantic = info.get("semantic", "unknown").replace("_", " ").title()
            sym_type = info.get("type", "unknown").replace("_", " ").title()
            count = data["count"]
            
            lines.append(f"{symbol} & {semantic} & {sym_type} & {count} \\\\")
        
        lines.extend([
            "\\bottomrule",
            "\\end{tabular}",
            "\\caption{Symbolic operators used in this document with usage statistics}",
            "\\end{table}"
        ])
        
        return "\n".join(lines)


class SymbolTestRenderer:
    """Generates test document for symbol rendering validation"""
    
    def __init__(self, registry: SymbolRegistry):
        self.registry = registry
    
    def generate_test_doc(self, output_path: Path, engine: str = "xelatex"):
        """Generate a test PDF with all registered symbols"""
        test_symbols = [s for s, d in self.registry.symbols.items() 
                       if d.get("test_render", False)]
        
        latex_content = self._create_test_latex(test_symbols)
        
        # Write LaTeX file
        tex_path = output_path.with_suffix('.tex')
        with open(tex_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Compile
        try:
            subprocess.run(
                [engine, '-interaction=nonstopmode', str(tex_path)],
                check=True,
                capture_output=True,
                cwd=tex_path.parent
            )
            print(f"✓ Test document generated: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to compile test document")
            print(e.stderr.decode() if e.stderr else "")
    
    def _create_test_latex(self, symbols: List[str]) -> str:
        """Create LaTeX content for symbol test"""
        content = r"""\documentclass{article}
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{Latin Modern Roman}
\setmathfont{Latin Modern Math}
\usepackage{booktabs}
\usepackage{geometry}
\geometry{margin=1in}

\title{Symbol Rendering Test}
\author{MD2TeX}
\date{\today}

\begin{document}
\maketitle

\section*{Registered Symbols Test}

This document tests the rendering of all registered symbolic operators.

\begin{table}[h]
\centering
\begin{tabular}{clll}
\toprule
Symbol & Unicode & Inline Math & Display Math \\
\midrule
"""
        
        for symbol in symbols:
            info = self.registry.symbols.get(symbol, {})
            codepoint = f"U+{ord(symbol):04X}"
            semantic = info.get("semantic", "unknown")
            
            content += f"{symbol} & {codepoint} & ${symbol}$ & $\\displaystyle {symbol}$ \\\\\n"
        
        content += r"""\bottomrule
\end{tabular}
\caption{Symbol rendering test results}
\end{table}

\section*{Context Tests}

\subsection*{In Equations}
$$
\Psi \otimes \Phi \rightarrow \nabla(\text{frequency space})
$$

\subsection*{In Text}
The operator $\otimes$ represents tensor product in frequency space.

\end{document}
"""
        return content


def create_template(output_path: Path):
    """Create DEC-style LaTeX template"""
    template = r"""
\documentclass[11pt, letterpaper]{article}

% --- Packages for Unicode support
\usepackage{fontspec}
\usepackage{unicode-math}
\setmainfont{Latin Modern Roman}
\setmathfont{Latin Modern Math}

% --- Original packages
\usepackage[T1]{fontenc}
\usepackage[margin=1.25in]{geometry}
\usepackage{microtype}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{newtxtext,newtxmath}
\usepackage{setspace}
\setstretch{1.1}
\usepackage{graphicx}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{caption}
\usepackage{fancyhdr}
\setlength{\headheight}{14pt}
\usepackage{titlesec}
\usepackage{mdframed}
\usepackage{tikz}
\usetikzlibrary{arrows, shapes, positioning}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{booktabs}
\usepackage{pgfplots}
\usepackage{float}
\pgfplotsset{compat=1.18}

$if(bibliography)$
\usepackage[backend=biber,style=numeric]{biblatex}
\addbibresource{$bibliography$}
$endif$

% --- TikZ Styles
\tikzset{
    component/.style={rectangle, rounded corners, text width=2.5cm, text centered, draw=black, fill=blue!10},
    block/.style={rectangle, draw, fill=blue!20, text width=5em, text centered, rounded corners, minimum height=4em},
    monitor/.style={rectangle, draw, fill=green!20, text width=5em, text centered, rounded corners, minimum height=4em},
    line/.style={draw, -latex'},
    cloud/.style={draw, ellipse, fill=red!20, node distance=3cm, minimum height=2em},
    arrow/.style={->, thick},
    flow/.style={->, thick},
    label/.style={font=\small}
}

% --- Figure captions
\captionsetup[figure]{labelfont=bf,labelsep=period,name=FIG.,justification=raggedright,singlelinecheck=false}

% --- Header/Footer
\pagestyle{fancy}
\fancyhf{}
\lhead{\uppercase{$title$}}
\rhead{\thepage}
\renewcommand{\headrulewidth}{0.5pt}

% --- Section styling
\titleformat{\section}{\large\bfseries\uppercase}{\thesection.}{1em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalsize\itshape}{\thesubsubsection}{1em}{}

% --- Theorem environments
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{proposition}[theorem]{Proposition}
\newtheorem{corollary}[theorem]{Corollary}
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{note}{Note}
\theoremstyle{remark}
\newtheorem*{proof}{Proof}

% --- Listings style
\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
    keepspaces=true,
    columns=flexible
}

\begin{document}

\begin{center}
{\Large\bfseries\uppercase{$title$}}\\[0.5em]
$if(subtitle)${\normalsize $subtitle$}\\[1em]$endif$
$if(author)${\normalsize \textbf{$author$}}$endif$ 
$if(affiliation)$\\ \texttt{$affiliation$}\\[0.5em]$endif$
{\footnotesize $date$}
\end{center}

\vspace{0.5cm}

$body$

$if(bibliography)$
\printbibliography
$endif$

\end{document}
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(template)


def watch_mode(args, main_conversion_func):
    """Watch file for changes and auto-convert"""
    print(f"👁 Watching {args.input} for changes... (Ctrl+C to stop)")
    last_mtime = args.input.stat().st_mtime
    
    try:
        while True:
            time.sleep(1)
            if not args.input.exists():
                print(f"⚠ File {args.input} no longer exists")
                break
                
            current_mtime = args.input.stat().st_mtime
            if current_mtime > last_mtime:
                print(f"\n[Change detected at {time.strftime('%H:%M:%S')}]")
                last_mtime = current_mtime
                try:
                    main_conversion_func(args)
                    print("✓ Conversion complete")
                except Exception as e:
                    print(f"✗ Conversion failed: {e}")
    except KeyboardInterrupt:
        print("\n\nStopped watching.")


def run_validation_suite(args, registry):
    """Run comprehensive validation checks"""
    print("=" * 60)
    print("VALIDATION SUITE")
    print("=" * 60)
    
    issues = []
    
    # 1. Symbol lint
    print("\n[1/4] Running symbol linter...")
    linter = SymbolLinter(registry)
    lint_issues, stats = linter.lint_file(args.input)
    if lint_issues:
        issues.extend(lint_issues)
        print(f"  ⚠ Found {len(lint_issues)} symbol issues")
    else:
        print("  ✓ No symbol issues")
    
    # 2. Math fence check
    print("\n[2/4] Checking math fences...")
    with open(args.input, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for unbalanced $ signs
    dollar_count = content.count('$')
    if dollar_count % 2 != 0:
        issues.append("Unbalanced $ delimiters in document")
        print("  ⚠ Unbalanced $ delimiters")
    else:
        print("  ✓ Math delimiters balanced")
    
    # 3. Tensor notation check
    print("\n[3/4] Validating tensor notation...")
    validator = TensorNotationValidator()
    tensor_issues = validator.validate(content)
    if tensor_issues:
        issues.extend(tensor_issues)
        print(f"  ⚠ Found {len(tensor_issues)} tensor notation issues")
    else:
        print("  ✓ Tensor notation valid")
    
    # 4. Figure existence check
    print("\n[4/4] Checking figure references...")
    fig_pattern = r'!\[.*?\]\((.*?)\)'
    figures = re.findall(fig_pattern, content)
    missing_figs = []
    for fig in figures:
        fig_path = args.input.parent / fig
        if not fig_path.exists():
            missing_figs.append(fig)
    
    if missing_figs:
        issues.extend([f"Missing figure: {fig}" for fig in missing_figs])
        print(f"  ⚠ Found {len(missing_figs)} missing figures")
    else:
        print("  ✓ All figures exist")
    
    # Print summary
    print("\n" + "=" * 60)
    if issues:
        print("VALIDATION FAILED")
        print("=" * 60)
        print("\nIssues to address:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False
    else:
        print("✓ ALL CHECKS PASSED")
        print("=" * 60)
        return True


def main_conversion_logic(args):
    """Main conversion logic separated for reuse in watch mode"""
    registry = SymbolRegistry(args.registry)
    
    # Determine output path
    output = args.output or args.input.with_suffix('.tex')
    
    # Convert
    print(f"Converting {args.input} → {output} (mode: {args.mode}, engine: {args.engine})")
    converter = MD2TeXConverter(registry, args.mode, args.engine)
    converter.convert(args.input, output, args.template, args.bib, args.add_version)
    print(f"✓ Conversion complete: {output}")
    
    # Generate appendix if requested
    if args.appendix:
        linter = SymbolLinter(registry)
        _, stats = linter.lint_file(args.input)
        gen = AppendixGenerator(registry)
        appendix = gen.generate(stats)
        
        # Append to tex file
        with open(output, 'a', encoding='utf-8') as f:
            f.write("\n\n" + appendix)
        print(f"✓ Appendix added to {output}")
    
    # Compile PDF if requested
    if args.compile_pdf:
        pdf_path = output.with_suffix('.pdf')
        print(f"Compiling to PDF with {args.engine}...")
        try:
            # Run twice for references
            for i in range(2):
                subprocess.run(
                    [args.engine, '-interaction=nonstopmode', str(output)],
                    check=True,
                    capture_output=True,
                    cwd=output.parent
                )
            print(f"✓ PDF compiled: {pdf_path}")
            
            # Validate if requested
            if args.validate:
                validator = PDFValidator()
                report = validator.validate(args.input, pdf_path, registry)
                print(f"\n{report}")
        except subprocess.CalledProcessError as e:
            print(f"✗ {args.engine} compilation failed")
            if e.stderr:
                error_output = e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr
                print(error_output)
            raise


def main():
    parser = argparse.ArgumentParser(
        description="MD2TeX: Convert Markdown to LaTeX preserving symbolic operators",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  %(prog)s paper.md
  
  # With template and bibliography
  %(prog)s paper.md --template dec.latex --bib refs.bib --compile-pdf
  
  # Watch mode for live editing
  %(prog)s paper.md --watch --compile-pdf
  
  # Development mode with annotations
  %(prog)s paper.md --mode dev --compile-pdf
  
  # Full validation suite
  %(prog)s paper.md --validate-all
  
  # Test symbol rendering
  %(prog)s --test-symbols symbol_test.pdf
        """
    )
    
    parser.add_argument('input', type=Path, nargs='?', help='Input markdown file')
    parser.add_argument('-o', '--output', type=Path, help='Output file (default: input.tex)')
    parser.add_argument('--mode', choices=['dev', 'pub', 'compute'], default='pub',
                       help='Output mode: dev (annotated), pub (clean), compute (with metadata)')
    parser.add_argument('--engine', choices=['xelatex', 'lualatex'], default='xelatex',
                       help='LaTeX engine to use')
    parser.add_argument('--template', type=Path, help='LaTeX template file')
    parser.add_argument('--bib', type=Path, help='Bibliography file (.bib)')
    parser.add_argument('--registry', type=Path, help='Symbol registry JSON file')
    parser.add_argument('--lint', action='store_true', help='Run linter and exit')
    parser.add_argument('--validate', action='store_true', help='Validate PDF after conversion')
    parser.add_argument('--validate-all', action='store_true', help='Run comprehensive validation suite')
    parser.add_argument('--appendix', action='store_true', help='Generate symbol reference appendix')
    parser.add_argument('--add-version', action='store_true', help='Add version hash to output')
    parser.add_argument('--create-template', type=Path, help='Create default template at path')
    parser.add_argument('--compile-pdf', action='store_true', help='Compile to PDF with selected engine')
    parser.add_argument('--watch', action='store_true', help='Watch file for changes and auto-convert')
    parser.add_argument('--test-symbols', type=Path, help='Generate symbol rendering test document')
    
    args = parser.parse_args()
    
    # Create template if requested
    if args.create_template:
        create_template(args.create_template)
        print(f"✓ Template created at {args.create_template}")
        return
    
    # Test symbols if requested
    if args.test_symbols:
        registry = SymbolRegistry(args.registry)
        renderer = SymbolTestRenderer(registry)
        renderer.generate_test_doc(args.test_symbols, args.engine)
        return
    
    # Require input file for other operations
    if not args.input:
        parser.error("input file is required")
    
    if not args.input.exists():
        print(f"✗ Input file not found: {args.input}")
        sys.exit(1)
    
    # Initialize registry
    registry = SymbolRegistry(args.registry)
    
    # Validation suite mode
    if args.validate_all:
        success = run_validation_suite(args, registry)
        sys.exit(0 if success else 1)
    
    # Lint mode
    if args.lint:
        linter = SymbolLinter(registry)
        issues, stats = linter.lint_file(args.input)
        report = linter.generate_report(issues, stats)
        print(report)
        
        if args.appendix:
            gen = AppendixGenerator(registry)
            appendix = gen.generate(stats)
            appendix_path = args.input.with_suffix('.appendix.tex')
            with open(appendix_path, 'w', encoding='utf-8') as f:
                f.write(appendix)
            print(f"\n✓ Appendix generated at {appendix_path}")
        
        sys.exit(0 if not issues else 1)
    
    # Watch mode
    if args.watch:
        watch_mode(args, main_conversion_logic)
        return
    
    # Normal conversion
    try:
        main_conversion_logic(args)
    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

