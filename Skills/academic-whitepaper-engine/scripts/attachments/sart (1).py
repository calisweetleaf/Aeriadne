#!/usr/bin/env python3
"""
SART v3: Somnus Academic Research Toolkit (Unified)
Sovereign Semantic Ontology & Equation Coherence Engine.

"Mathematics is the physics of the information realm."

Features:
- Physics-First Ontology (Causality, Type, Domain)
- Hybrid Scanning (LaTeX Blocks + Unicode/Inline)
- Incremental Processing (File Hashing)
- Self-Healing Diagnostics (Cycle/Orphan Detection)
- REPL-style Interactive Training
"""

import os
import re
import json
import argparse
import hashlib
import unicodedata
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field

# === CONFIGURATION & CONSTANTS ===

# Semantic Types for the "Physics-First" approach
SYMBOL_TYPES = [
    "Scalar", "Vector", "Matrix", "Tensor", 
    "Operator", "Function", "Set", "Manifold", 
    "Constant", "Field", "Bundle", "Space"
]

DOMAINS = [
    "R (Real)", "C (Complex)", "Z (Integers)", "N (Naturals)",
    "H (Hilbert Space)", "B (Boolean)", "L (Latent Space)", 
    "M (Spacetime)", "Q (Quantum State)", "∅ (Empty)"
]

# Canonicalization Map: Maps synonyms/unicode to a single key
CANONICAL_MAP = {
    'α': '\\alpha', 'β': '\\beta', 'γ': '\\gamma', 'δ': '\\delta',
    'ε': '\\epsilon', 'θ': '\\theta', 'λ': '\\lambda', 'μ': '\\mu',
    'π': '\\pi', 'σ': '\\sigma', 'τ': '\\tau', 'φ': '\\phi',
    'ω': '\\omega', '∇': '\\nabla', '∂': '\\partial',
    '→': '\\rightarrow', '\\to': '\\rightarrow', '⇒': '\\implies',
    '∞': '\\infty', '∈': '\\in', '∀': '\\forall', '∃': '\\exists',
    '∑': '\\sum', '∏': '\\prod', '∫': '\\int'
}

# Core LaTeX Commands to track
LATEX_COMMANDS = {
    r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\epsilon', r'\\zeta', 
    r'\\eta', r'\\theta', r'\\iota', r'\\kappa', r'\\lambda', r'\\mu', 
    r'\\nu', r'\\xi', r'\\pi', r'\\rho', r'\\sigma', r'\\tau', r'\\upsilon', 
    r'\\phi', r'\\chi', r'\\psi', r'\\omega', r'\\Gamma', r'\\Delta', 
    r'\\Theta', r'\\Lambda', r'\\Xi', r'\\Pi', r'\\Sigma', r'\\Upsilon', 
    r'\\Phi', r'\\Psi', r'\\Omega', r'\\nabla', r'\\partial', r'\\forall', 
    r'\\exists', r'\\in', r'\\notin', r'\\subset', r'\\supset', r'\\cup', 
    r'\\cap', r'\\infty', r'\\to', r'\\rightarrow', r'\\leftarrow', 
    r'\\implies', r'\\iff', r'\\times', r'\\otimes', r'\\oplus', r'\\cdot',
    r'\\mathcal', r'\\mathbb', r'\\mathbf' # Expanded for structure
}

# Unicode Ranges for Math
SYMBOL_RANGES = [
    (0x2200, 0x22FF), (0x2190, 0x21FF), (0x2A00, 0x2AFF),
    (0x27C0, 0x27EF), (0x2980, 0x29FF), (0x0370, 0x03FF),
    (0x1D400, 0x1D7FF)
]

MATH_BLOCK_PATTERN = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)

# === DATA STRUCTURES ===

@dataclass
class SymbolEntity:
    symbol: str                     # Unique Identifier (Canonical)
    latex: str = ""                 # Display LaTeX
    name: str = "Undefined"         # Human Concept Name
    definition: str = "No definition provided."
    semantic_type: str = "Scalar"
    domain: str = "R (Real)"
    dependencies: List[str] = field(default_factory=list) # "Made of" these symbols
    reverse_deps: List[str] = field(default_factory=list) # "Used in" these symbols
    defined_in: List[str] = field(default_factory=list)   # File context
    is_unicode: bool = False

@dataclass
class ScanMeta:
    file_hashes: Dict[str, str] = field(default_factory=dict)

class SomnusCodex:
    def __init__(self, root_dir: Path, db_path: Path):
        self.root_dir = root_dir
        self.db_path = db_path
        self.meta_path = db_path.parent / f"{db_path.stem}_meta.json"
        
        self.ontology: Dict[str, SymbolEntity] = self._load_ontology()
        self.scan_meta: ScanMeta = self._load_scan_meta()

    # --- PERSISTENCE ---

    def _load_ontology(self) -> Dict[str, SymbolEntity]:
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k: SymbolEntity(**v) for k, v in data.items()}
            except Exception: return {}
        return {}

    def _load_scan_meta(self) -> ScanMeta:
        if self.meta_path.exists():
            try:
                with open(self.meta_path, 'r', encoding='utf-8') as f:
                    return ScanMeta(**json.load(f))
            except Exception: pass
        return ScanMeta()

    def save_state(self):
        # Save Ontology
        dump_data = {k: asdict(v) for k, v in self.ontology.items()}
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(dump_data, f, indent=2, ensure_ascii=False)
        
        # Save Meta
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.scan_meta), f, indent=2)

    # --- PARSING & NORMALIZATION ---

    def _canonicalize(self, raw_sym: str) -> str:
        return CANONICAL_MAP.get(raw_sym, raw_sym)

    def _clean_latex_cmd(self, cmd: str) -> str:
        return cmd.replace('\\\\', '\\')

    def is_math_char(self, char: str) -> bool:
        code = ord(char)
        for start, end in SYMBOL_RANGES:
            if start <= code <= end: return True
        return False

    def _extract_tokens_from_math_string(self, math_str: str) -> List[Tuple[str, bool]]:
        """
        Robust token extraction preventing substring false positives.
        """
        tokens = set()
        
        # 1. LaTeX Commands (Safe Regex)
        # Sort commands by length (desc) to match longer ones first if needed, 
        # though regex word boundary handles most collisions.
        for cmd in LATEX_COMMANDS:
            clean_cmd = self._clean_latex_cmd(cmd)
            # Match literal command not followed by letters (e.g. \alpha but not \alphabet)
            # (?<!\\) ensures we don't match suffix of another command
            pattern = rf'(?<!\\){re.escape(clean_cmd)}(?:[^a-zA-Z]|$)'
            if re.search(pattern, math_str):
                tokens.add((self._canonicalize(clean_cmd), False))

        # 2. Unicode Symbols
        for char in math_str:
            if self.is_math_char(char):
                tokens.add((self._canonicalize(char), True))

        # 3. Single Letter Variables (Context Aware)
        # Exclude differentials and common layout chars if they appear as standalone
        excluded = {'d', '∂', '∇'} 
        var_pattern = r'(?<!\\)[a-zA-Z](?![a-zA-Z])' # Single char, no backslash prefix, not followed by char
        for match in re.finditer(var_pattern, math_str):
            var = match.group()
            if var not in excluded:
                # Only add if we haven't already caught it as a command (unlikely given regex)
                tokens.add((self._canonicalize(var), False))

        return list(tokens)

    def _parse_equation_structure(self, eq: str) -> Tuple[List[str], List[str]]:
        """
        AST-Lite: Determines Definition (LHS) vs Composition (RHS).
        """
        # Definition Patterns: :=, \equiv, \leftarrow
        def_patterns = [
            r'(.+?)\s*:=\s*(.+)',
            r'(.+?)\s*\\equiv\s*(.+)',
            r'(.+?)\s*\\leftarrow\s*(.+)'
        ]
        
        for pat in def_patterns:
            match = re.search(pat, eq, re.DOTALL)
            if match:
                lhs_raw, rhs_raw = match.groups()
                lhs = [t[0] for t in self._extract_tokens_from_math_string(lhs_raw)]
                rhs = [t[0] for t in self._extract_tokens_from_math_string(rhs_raw)]
                return (lhs, rhs)

        # Fallback: Treat entire block as usage
        all_tokens = [t[0] for t in self._extract_tokens_from_math_string(eq)]
        return ([], all_tokens)

    # --- CORE AUDIT LOGIC ---

    def audit_file(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8')
        
        # 1. Structural Scan (Dependencies)
        for match in MATH_BLOCK_PATTERN.finditer(content):
            eq_block = match.group(1).strip()
            defined_syms, used_syms = self._parse_equation_structure(eq_block)
            
            # Register Definitions
            for sym in defined_syms:
                self._upsert_symbol(sym, file_path.name)
                # Add dependencies (LHS depends on RHS)
                self.ontology[sym].dependencies = list(set(self.ontology[sym].dependencies) | set(used_syms))
            
            # Register Usages
            for sym in used_syms:
                self._upsert_symbol(sym, file_path.name)

        # 2. Linear Scan (Inline/Text Occurrences)
        # We process line by line for context, but ignore blocks we just processed
        clean_content = MATH_BLOCK_PATTERN.sub('', content) # remove blocks to avoid double counting
        for line in clean_content.splitlines():
            tokens = self._extract_tokens_from_math_string(line)
            for sym, is_uni in tokens:
                self._upsert_symbol(sym, file_path.name, is_uni=is_uni)

    def _upsert_symbol(self, sym: str, filename: str, is_uni: bool = False):
        if not sym: return
        if sym not in self.ontology:
            latex_val = sym if not is_uni else ""
            self.ontology[sym] = SymbolEntity(
                symbol=sym, latex=latex_val, is_unicode=is_uni, defined_in=[filename]
            )
        else:
            if filename not in self.ontology[sym].defined_in:
                self.ontology[sym].defined_in.append(filename)

    def scan_system(self, force: bool = False):
        print(f"👁️  Auditing System Coherence in {self.root_dir}...")
        files = list(self.root_dir.glob("**/*.md"))
        
        updates = 0
        for f_path in files:
            if f_path.name in ["GLOSSARY.md", "README.md", "SUMMARY.md"]: continue
            
            # Incremental Check
            current_hash = hashlib.md5(f_path.read_bytes()).hexdigest()
            if not force and self.scan_meta.file_hashes.get(str(f_path)) == current_hash:
                continue
                
            self.audit_file(f_path)
            self.scan_meta.file_hashes[str(f_path)] = current_hash
            updates += 1
            
        self._update_reverse_index()
        self.save_state()
        print(f"✓ Scan Complete. {updates} files processed.")

    def _update_reverse_index(self):
        """Rebuilds the 'Used By' list for all symbols."""
        # Reset
        for d in self.ontology.values(): d.reverse_deps = []
        # Populate
        for sym, data in self.ontology.items():
            for dep in data.dependencies:
                if dep in self.ontology:
                    self.ontology[dep].reverse_deps.append(sym)

    # --- DIAGNOSTICS & QUALITY ---

    def validate_ontology(self):
        print("\n🔍 Running Ontology Diagnostics...")
        
        # 1. Orphan Detection
        defined = {k for k,v in self.ontology.items() if v.name != "Undefined"}
        referenced = set()
        for v in self.ontology.values(): referenced.update(v.dependencies)
        
        orphans = referenced - defined
        if orphans:
            print(f"⚠️  {len(orphans)} Orphan Symbols (Used but Undefined): {list(orphans)[:5]}...")
            
        # 2. Cycle Detection
        visited = set()
        path = set()
        cycles = []
        
        def check_cycle(u):
            visited.add(u)
            path.add(u)
            for v in self.ontology.get(u, SymbolEntity("")).dependencies:
                if v not in visited:
                    if check_cycle(v): return True
                elif v in path:
                    cycles.append(u)
                    return True
            path.remove(u)
            return False

        for sym in self.ontology:
            if sym not in visited:
                check_cycle(sym)
                
        if cycles:
            print(f"⚠️  Dependency Cycles Detected involving: {cycles[:5]}...")
        else:
            print("✓ No circular dependencies found.")

    # --- INTERACTIVE TRAINING ---

    def interactive_training(self):
        sorted_keys = sorted(self.ontology.keys())
        idx = 0
        print("\n⚛️  SART v3: Neural-Symbolic Training Protocol")
        print("Cmds: [d]efine, [s]kip, [i]gnore, [j]ump <sym>, [q]uit")
        
        while idx < len(sorted_keys):
            sym = sorted_keys[idx]
            data = self.ontology[sym]
            
            # Auto-skip defined or ignored
            if data.name != "Undefined" or data.definition == "IGNORE":
                idx += 1
                continue
            
            print(f"\n[{idx+1}/{len(sorted_keys)}] Symbol: {sym}")
            print(f"  Files: {data.defined_in[:2]}...")
            if data.dependencies: print(f"  Depends on: {data.dependencies}")
            if data.reverse_deps: print(f"  Used in: {data.reverse_deps}")
            
            cmd = input("  > ").strip().lower()
            
            if cmd == 'q': break
            elif cmd == 's': 
                idx += 1
                continue
            elif cmd == 'i':
                data.definition = "IGNORE"
                self.save_state()
            elif cmd.startswith('j '):
                target = cmd[2:].strip()
                # Simple fuzzy find
                found = next((i for i, k in enumerate(sorted_keys) if target in k), -1)
                if found != -1: idx = found
            elif cmd == 'd':
                self._define_symbol_cli(data)
                self.save_state()
            
            idx += 1

    def _define_symbol_cli(self, data: SymbolEntity):
        data.name = input("  Name: ")
        data.definition = input("  Semantics: ")
        
        if not data.latex:
            l = input(f"  LaTeX (default {data.symbol}): ")
            data.latex = l if l else data.symbol
            
        print(f"  Types: {', '.join([f'[{i}]{t}' for i,t in enumerate(SYMBOL_TYPES)])}")
        try:
            t = int(input("  Type ID: ") or "0")
            data.semantic_type = SYMBOL_TYPES[t]
        except: pass
        
        print(f"  Domain: {', '.join([f'[{i}]{t}' for i,t in enumerate(DOMAINS)])}")
        try:
            d = int(input("  Domain ID: ") or "0")
            data.domain = DOMAINS[d]
        except: pass

    # --- ARTIFACT GENERATION ---

    def generate_artifacts(self):
        print("\n📦 Generating Sovereign Artifacts...")
        
        # 1. Knowledge Graph (JSON)
        graph = {
            "meta": "Somnus Sovereign Context",
            "nodes": [],
            "edges": []
        }
        for sym, data in self.ontology.items():
            if data.definition == "IGNORE": continue
            graph["nodes"].append({
                "id": sym, "label": data.name, 
                "type": data.semantic_type, "domain": data.domain
            })
            for dep in data.dependencies:
                graph["edges"].append({"source": dep, "target": sym, "rel": "constitutes"})
                
        kg_path = self.root_dir / "somnus_knowledge_graph.json"
        with open(kg_path, 'w') as f: json.dump(graph, f, indent=2)

        # 2. Markdown Glossary
        md_lines = ["# System Ontology", "", "| Symbol | Name | Semantics | Domain |", "|:--:|:--|:--|:--|"]
        
        # Sort by Type then Name
        sorted_items = sorted(
            [v for v in self.ontology.values() if v.definition != "IGNORE" and v.name != "Undefined"],
            key=lambda x: (x.semantic_type, x.name)
        )
        
        for item in sorted_items:
            disp = f"${item.latex}$" if item.latex else item.symbol
            md_lines.append(f"| {disp} | **{item.name}** | {item.definition} | `{item.domain}` |")
            
        md_path = self.root_dir / "GLOSSARY.md"
        md_path.write_text("\n".join(md_lines), encoding='utf-8')

        # 3. LaTeX Glossary
        tex_lines = ["% Somnus Auto-Glossary", "\\newglossaryentry{symbols}{name={Symbols}, description={...}}"]
        for item in sorted_items:
            safe_id = re.sub(r'[^a-zA-Z0-9]', '', item.name.lower())
            if not safe_id: safe_id = f"sym{hash(item.symbol)}"
            entry = f"\\newglossaryentry{{{safe_id}}}{{name={{{item.latex}}}, description={{{item.definition}}}, sort={{{item.name}}}}}"
            tex_lines.append(entry)
            
        tex_path = self.root_dir / "glossary.tex"
        tex_path.write_text("\n".join(tex_lines), encoding='utf-8')
        
        print(f"✓ Artifacts Generated: {kg_path.name}, {md_path.name}, {tex_path.name}")

def main():
    parser = argparse.ArgumentParser(description="SART v3: Unified Somnus Toolkit")
    parser.add_argument('path', type=Path, help="Target Directory")
    parser.add_argument('--db', type=Path, default=Path("somnus_ontology.json"))
    parser.add_argument('--force', action='store_true', help="Force re-scan all files")
    parser.add_argument('--train', action='store_true', help="Interactive Training")
    parser.add_argument('--build', action='store_true', help="Generate Artifacts")
    parser.add_argument('--check', action='store_true', help="Run Diagnostics")

    args = parser.parse_args()
    
    codex = SomnusCodex(args.path, args.db)
    codex.scan_system(force=args.force)
    
    if args.check: codex.validate_ontology()
    if args.train: codex.interactive_training()
    if args.build: codex.generate_artifacts()

if __name__ == "__main__":
    main()