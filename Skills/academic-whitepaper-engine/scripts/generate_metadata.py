#!/usr/bin/env python3
"""
Generate metadata.json for academic whitepapers.

This script extracts metadata from the whitepaper and creates
a DOI-ready metadata.json file for archival and citation.

Usage:
    python generate_metadata.py whitepaper.tex
    python generate_metadata.py --interactive
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

def extract_title_from_tex(tex_content: str) -> Optional[str]:
    """Extract title from LaTeX document."""
    patterns = [
        r'\\title\{([^}]+)\}',
        r'\\LARGE\\bfseries\s+([^\\\n]+)',
        r'\\begin\{center\}\\textbf\{\\Large\s+([^}]+)\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, tex_content)
        if match:
            return match.group(1).strip()
    
    return None

def extract_authors_from_tex(tex_content: str) -> List[str]:
    """Extract author names from LaTeX document."""
    patterns = [
        r'\\author\{([^}]+)\}',
        r'\\AuthorList\{([^}]+)\}'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, tex_content)
        if match:
            authors_str = match.group(1)
            # Handle \and separator
            authors = [a.strip() for a in re.split(r'\\and|,', authors_str)]
            return [a for a in authors if a]
    
    return []

def extract_abstract_from_tex(tex_content: str) -> Optional[str]:
    """Extract abstract from LaTeX document."""
    abstract_pattern = r'\\begin\{abstract\}(.*?)\\end\{abstract\}'
    match = re.search(abstract_pattern, tex_content, re.DOTALL)
    
    if match:
        abstract = match.group(1).strip()
        # Remove LaTeX commands
        abstract = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', abstract)
        abstract = re.sub(r'\\[a-zA-Z]+', '', abstract)
        return abstract.strip()
    
    return None

def extract_keywords_from_tex(tex_content: str) -> List[str]:
    """Extract keywords from LaTeX document."""
    patterns = [
        r'\\keywords\{([^}]+)\}',
        r'Keywords:\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, tex_content, re.IGNORECASE)
        if match:
            keywords_str = match.group(1)
            keywords = [k.strip() for k in keywords_str.split(',')]
            return [k for k in keywords if k]
    
    return []

def generate_metadata_interactive() -> Dict:
    """Interactively collect metadata from user."""
    print("=== Academic Whitepaper Metadata Generator ===\n")
    
    metadata = {}
    
    # Basic information
    metadata['title'] = input("Title: ").strip()
    metadata['subtitle'] = input("Subtitle (optional): ").strip() or None
    
    # Authors
    authors = []
    print("\nAuthors (press Enter with blank name when done):")
    while True:
        name = input(f"  Author {len(authors)+1} name: ").strip()
        if not name:
            break
        affiliation = input(f"  {name}'s affiliation: ").strip()
        authors.append({
            "name": name,
            "affiliation": affiliation or "Independent Researcher"
        })
    metadata['authors'] = authors
    
    # Abstract
    print("\nAbstract (enter text, then Ctrl+D or Ctrl+Z when done):")
    abstract_lines = []
    try:
        while True:
            line = input()
            abstract_lines.append(line)
    except EOFError:
        pass
    metadata['abstract'] = "\n".join(abstract_lines).strip()
    
    # Keywords
    keywords_str = input("\nKeywords (comma-separated): ").strip()
    metadata['keywords'] = [k.strip() for k in keywords_str.split(',') if k.strip()]
    
    # Dates
    metadata['date_created'] = datetime.now().isoformat()
    metadata['version'] = input("Version (default: v1.0): ").strip() or "v1.0"
    
    # Optional fields
    doi = input("DOI (optional, leave blank to reserve): ").strip()
    metadata['doi'] = doi if doi else "Reserved - pending publication"
    
    metadata['license'] = input("License (default: CC BY-NC-SA 4.0): ").strip() or "CC BY-NC-SA 4.0"
    
    return metadata

def generate_metadata_from_tex(tex_path: Path) -> Dict:
    """Extract metadata from existing .tex file."""
    with open(tex_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    metadata = {
        'title': extract_title_from_tex(content),
        'authors': [{'name': a, 'affiliation': 'Unknown'} 
                   for a in extract_authors_from_tex(content)],
        'abstract': extract_abstract_from_tex(content),
        'keywords': extract_keywords_from_tex(content),
        'date_created': datetime.now().isoformat(),
        'version': 'v1.0',
        'doi': 'Reserved - pending publication',
        'license': 'CC BY-NC-SA 4.0',
        'source_file': str(tex_path)
    }
    
    return metadata

def save_metadata(metadata: Dict, output_path: Path = Path('metadata.json')):
    """Save metadata to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Metadata saved to {output_path}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--interactive':
            metadata = generate_metadata_interactive()
        else:
            tex_path = Path(sys.argv[1])
            if not tex_path.exists():
                print(f"Error: {tex_path} not found")
                sys.exit(1)
            
            print(f"Extracting metadata from {tex_path}...")
            metadata = generate_metadata_from_tex(tex_path)
    else:
        # Default: interactive mode
        metadata = generate_metadata_interactive()
    
    # Add additional computed fields
    metadata['word_count_estimate'] = 'Run word count tool on final document'
    metadata['citation_count'] = 'Run citation count on references.bib'
    
    save_metadata(metadata)
    
    print("\nGenerated metadata:")
    print(json.dumps(metadata, indent=2))

if __name__ == '__main__':
    main()
