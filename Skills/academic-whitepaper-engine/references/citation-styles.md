# Citation Styles Reference

This document provides examples of common citation styles used in academic whitepapers.

## IEEE Style (Numbered References)

**In-text citations:**
```
The recursive fixed-point theorem [1] establishes convergence properties...
Multiple sources can be cited together [2], [3], [4].
```

**Bibliography entry:**
```bibtex
@article{lawvere1969,
  author = {F. William Lawvere},
  title = {Diagonal arguments and cartesian closed categories},
  journal = {Theory and Applications of Categories},
  year = {1969},
  volume = {15},
  pages = {1--13},
  doi = {10.1007/BFb0080769}
}
```

**Rendered:**
```
[1] F. W. Lawvere, "Diagonal arguments and cartesian closed categories," 
    Theory and Applications of Categories, vol. 15, pp. 1-13, 1969, 
    doi: 10.1007/BFb0080769.
```

## ACM Style (Author-Year)

**In-text citations:**
```
Recent work in tensor-guided programming (Rowell 2024) demonstrates...
This approach builds on earlier foundations (Lawvere 1969; Gödel 1931).
```

**Bibliography entry:**
```bibtex
@inproceedings{rowell2024,
  author = {Rowell, Christian Trey},
  title = {Recursive Categorical Framework for AI Consciousness},
  booktitle = {Proceedings of ARAIS},
  year = {2024},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.xxxxx}
}
```

**Rendered:**
```
Christian Trey Rowell. 2024. Recursive Categorical Framework for AI 
Consciousness. In Proceedings of ARAIS. Zenodo. 
DOI: https://doi.org/10.5281/zenodo.xxxxx
```

## APA Style (Author-Year, Psychology/Social Sciences)

**In-text citations:**
```
Frequency-based architectures (Rowell, 2024) offer advantages over...
Multiple studies (Smith, 2023; Jones & Lee, 2024) confirm...
```

**Bibliography entry:**
```bibtex
@article{rowell2024freq,
  author = {Rowell, Christian Trey},
  title = {Sacred FBS Tokenizer: A Frequency-Based Substrate},
  journal = {arXiv preprint},
  year = {2024},
  note = {arXiv:2024.xxxxx}
}
```

**Rendered:**
```
Rowell, C. T. (2024). Sacred FBS Tokenizer: A frequency-based substrate. 
arXiv preprint arXiv:2024.xxxxx.
```

## Inline Citation Best Practices

**When to cite inline:**
- Direct quotes or paraphrases
- Specific empirical claims
- Novel methodologies borrowed from other work
- Contradictory findings requiring attribution

**When to defer to bibliography section:**
- General background knowledge
- Broad theoretical frameworks cited multiple times
- Historical context with many sources

**Example integration:**
```markdown
The Lawvere fixed-point theorem [15] provides the mathematical foundation 
for our recursive operator framework. While previous transformer architectures 
rely on attention-is-all-you-need paradigms [22], our approach synthesizes 
1980s-90s neural network theory [8], [9], [11] with modern tensor operations.
```

## DOI Best Practices

Always include DOI when available. Use the standard format:
```
doi: 10.1234/example.identifier
```

For URL-based DOIs in LaTeX:
```latex
\url{https://doi.org/10.1234/example.identifier}
```

## arXiv Formatting

```bibtex
@misc{author2024,
  author = {Last, First},
  title = {Paper Title},
  year = {2024},
  eprint = {2024.12345},
  archivePrefix = {arXiv},
  primaryClass = {cs.AI}
}
```

## Zenodo Formatting

```bibtex
@misc{rowell2024urse,
  author = {Rowell, Christian Trey},
  title = {URSE: Unified Theory of Recursive Sentient Emergence},
  year = {2024},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.xxxxx},
  url = {https://zenodo.org/record/xxxxx}
}
```

## Conference Proceedings

```bibtex
@inproceedings{author2024conf,
  author = {Last, First and Second, Author},
  title = {Conference Paper Title},
  booktitle = {Proceedings of the Conference Name},
  year = {2024},
  pages = {123--145},
  publisher = {Publisher Name},
  address = {City, Country},
  doi = {10.1234/conf.2024.xxx}
}
```

## Software/Code Citations

```bibtex
@software{rowell2024rosemary,
  author = {Rowell, Christian Trey},
  title = {Project Rosemary: Recursive AI Framework},
  year = {2024},
  url = {https://github.com/username/rosemary},
  version = {v1.0.0}
}
```

## Managing Large Bibliographies

For papers with 100+ citations:

1. **Group by theme** in references.bib with comments:
```bibtex
% ============ Category Theory Foundations ============
@article{lawvere1969, ...}
@book{maclane1971, ...}

% ============ Neural Network Theory (1980s-90s) ============
@article{hopfield1982, ...}
@article{kohonen1988, ...}

% ============ Transformer Architectures ============
@article{vaswani2017, ...}
```

2. **Use BibTeX keys systematically:**
- Format: `firstauthor_year_shortname`
- Examples: `lawvere1969_fixedpoint`, `rowell2024_rcf`, `vaswani2017_attention`

3. **Maintain citation counts** in metadata.json:
```json
{
  "total_citations": 127,
  "by_category": {
    "category_theory": 18,
    "neural_networks_classic": 23,
    "transformers": 15,
    "frequency_based": 12,
    "experimental_results": 31,
    "other": 28
  }
}
```
