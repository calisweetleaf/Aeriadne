# Static Eval Tests

`eval_cases.yaml` is intentionally JSON-compatible YAML so it can be parsed with the Python standard library.

Run:

```bash
python scripts/run_static_evals.py tests/eval_cases.yaml
```

The static eval runner validates the probe suite structure and prints the layer coverage matrix. It does not call a model. To use the probes against an agent, feed each `prompt` to the agent under the candidate constitution and record pass, partial, or fail in the red-team report template.
