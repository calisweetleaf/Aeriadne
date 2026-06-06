# File Tree: Somnus-MCP

## Interpretation Rules

This file is a navigation map, not a live runtime manifest. Runtime truth must come from `AGENTS.md`, `MCP_SPEC.md`, `ARCHITECTURE.md`, `ARCHITECTURE_MAP.md`, `bb7_tool_health_report`, and live `mcp_server.py` registration.

Current doctrine:
- canonical data root is `/home/daeron/Somnus-MCP/data`;
- canonical venv is `/home/daeron/Somnus-MCP/mcp.venv`;
- `mcp_server.py` is a gateway/dispatcher into the 4-7 Muad'Dib + `tools/` cognition layers, not the intelligence itself;
- `mcp.venv/` may be omitted by file-tree filters; do not infer `.venv`;
- files under `TRASH/`, `archive/`, backups, or MAYBE folders are not active runtime surfaces;
- a `.py` file under `tools/` is not proof of active loaded status;
- exact tool counts are dated runtime snapshots and may change with load failures, headless display state, or module registration.

Migration note — 2026-05-27:
- `tools/file_tool.py` is the promoted advanced FileTool with compatibility aliases.
- `tools/meta_intelligence_engine.py` is now the registry-bound meta-intelligence facade, including the read-only `bb7_muadib_mentat_bridge` one-plane snapshot surface.
- `golden_paths_meta.json` holds extracted audit/history metadata; `golden_paths.json` is executable workflow config only.
- `TRASH/MAYBE-TOOLS/ai_system_integration.py` remains blocked on Linux by Windows-only imports and is not active runtime.

Migration note — 2026-06-04:
- Muad'Dib self-play weights are safetensors, not JSON. JSON under `data/digital_twin/` is metadata/ledger/pointer state only.
- `muadib/neural_config.py` now defines `SelfPlayConfig` and `MuadDibSelfPlayHead`; `tools/exoskeleton_tool.py` exposes `bb7_dt_self_play` and `bb7_dt_checkpoint_status` wrappers over the live DigitalTwin instance.
- `mcp_server.py` autonomous exo cycle now invokes bounded self-play on cadence through the exoskeleton wrapper. This is lifecycle training and does not change the JSON display/content-block boundary.
- `mcp_server.py` display cleanup is now a final projection seam only:
  raw dict/list payloads are preserved for telemetry, memory exchange,
  Q-table/observations, and distillation/RFT before `_format_tool_result`
  emits compact Markdown. Use `SOVEREIGN_DISPLAY_PROJECTION=raw` to display
  canonical raw JSON. Validate with
  `scripts/validate_display_projection.py`.

**Generated:** 5/26/2026, 10:41:39 PM
**Root Path:** `/home/daeron/Somnus-MCP`

```
├── .codegraph
│   └── codegraph.db
├── .codex
│   └── AGENTS.md
├── TRASH
│   ├── MAYBE-TOOLS
│   │   ├── ai_integration_core.py
│   │   ├── ai_ml_integration_core.py
│   │   ├── ai_system_integration.py
│   │   ├── daerons_file_tool.py
│   │   ├── exoskeleton_tool_og.py
│   │   ├── intelligent_automation_tool.py
│   │   ├── meta_intelligence_engine.py
│   │   ├── project_context_tool.py
│   │   ├── session_manager_tool.py
│   │   └── vscode_terminal_tool.py
│   └── tools_backup
├── archive
├── config
│   └── templates
│       ├── README.md
│       ├── claude_code.mcp.json
│       ├── codex.config.toml.snippet
│       ├── gemini_cli.settings.json
│       ├── kimi_cli.mcp.json
│       ├── mcp.json
│       └── opencode.json
├── data
│   ├── agents
│   │   ├── handoffs
│   │   │   └── analyzer_pending.json
│   │   ├── messages
│   │   │   └── executions.jsonl
│   │   ├── nodes
│   │   │   ├── analyzer_1772244840_47913ea3.json
│   │   │   ├── analyzer_1772245079_d2e8a59f.json
│   │   │   ├── analyzer_1772357285_197208b6.json
│   │   │   ├── doc_1772244863_2d746b52.json
│   │   │   ├── doc_1772245137_d1276f06.json
│   │   │   ├── doc_1772406577_7c45d8cf.json
│   │   │   ├── planner_1772164968_9481d0b0.json
│   │   │   ├── planner_1772245179_e8d70e20.json
│   │   │   ├── planner_1772358729_a7b032a5.json
│   │   │   └── planner_1772406525_c0e041ed.json
│   │   └── agent_state.json
│   ├── analysis_artifacts
│   ├── analytics
│   ├── archives
│   │   └── memory_archive_20260226_213557.json
│   ├── automations
│   ├── backups
│   ├── checkpoints
│   ├── config
│   ├── digital_twin
│   │   ├── checkpoint_meta.json
│   │   ├── checkpoint_v4123.pt
│   │   ├── checkpoint_v4124.pt
│   │   ├── checkpoint_v4125.pt
│   │   ├── observations.json
│   │   ├── qtable.json
│   │   └── vocab.json
│   ├── distillation
│   │   ├── codex_trajectories_2026-04-15.jsonl
│   │   ├── codex_trajectories_2026-04-16.jsonl
│   │   ├── codex_trajectories_2026-04-23.jsonl
│   │   ├── codex_trajectories_2026-04-24.jsonl
│   │   ├── codex_trajectories_2026-04-25.jsonl
│   │   ├── codex_trajectories_2026-04-26.jsonl
│   │   ├── codex_trajectories_2026-04-27.jsonl
│   │   ├── codex_trajectories_2026-05-04.jsonl
│   │   ├── codex_trajectories_2026-05-05.jsonl
│   │   ├── codex_trajectories_2026-05-06.jsonl
│   │   ├── trajectories_2026-04-08.jsonl
│   │   ├── trajectories_2026-04-09.jsonl
│   │   ├── trajectories_2026-04-10.jsonl
│   │   ├── trajectories_2026-04-11.jsonl
│   │   ├── trajectories_2026-04-12.jsonl
│   │   ├── trajectories_2026-04-13.jsonl
│   │   ├── trajectories_2026-04-14.jsonl
│   │   ├── trajectories_2026-04-27.jsonl
│   │   └── trajectories_2026-05-06.jsonl
│   ├── distillation_dataset
│   │   ├── failures
│   │   │   └── failures_2026-04-14.jsonl
│   │   ├── high_value
│   │   ├── trajectories_2026-04-13.jsonl
│   │   ├── trajectories_2026-04-14.jsonl
│   │   ├── trajectories_2026-04-27.jsonl
│   │   └── trajectory_index.jsonl
│   ├── exoskeleton
│   │   ├── active_plans.json
│   │   ├── auto_discovered_workflows.json
│   │   ├── benchmark_exo_latency.json
│   │   ├── category_transitions.json
│   │   ├── cross_ai_activity.jsonl
│   │   ├── decision_trail.jsonl
│   │   ├── execution_history.jsonl
│   │   ├── exo_checkpoints.jsonl
│   │   └── exoskeleton_state.json
│   ├── exports
│   ├── logs
│   ├── merged_sessions
│   ├── messages
│   │   └── test.jsonl
│   ├── meta_intelligence
│   ├── models
│   ├── notebooks
│   ├── optimization
│   │   ├── patterns.db
│   │   └── performance.db
│   ├── patterns
│   ├── planner
│   │   ├── planner_runs.jsonl
│   │   └── planner_state.json
│   ├── project_shell
│   ├── reports
│   ├── security
│   │   ├── certs
│   │   │   ├── server.crt
│   │   │   └── server.key
│   │   ├── api_key.txt
│   │   └── webhooks.json
│   ├── sessions
│   │   ├── 01a61060-2e8e-4c29-b8cb-3664714beb65.json
│   │   ├── 024b919d-26be-4c63-86bf-9288b025f783.json
│   │   ├── 048662e9-77bb-4c7c-92ce-c128ec745c06.json
│   │   ├── 063e4d8f-9a46-471c-a39e-ac0f3bf519db.json
│   │   ├── 0a914008-298d-4c3e-9bef-5ceb84d84bcf.json
│   │   ├── 0b7483f8-a7ab-4f24-86e9-cc3e6d6455f0.json
│   │   ├── 0de972d4-1af2-4bcd-9fb5-6581e9ea9782.json
│   │   ├── 0ec6d888-2229-4059-b742-3d28d942ba12.json
│   │   ├── 11789f4a-c02c-40ad-ae00-f9a978a1cb24.json
│   │   ├── 11872a25-2e76-4237-a2d7-c4d8966c78cf.json
│   │   ├── 11cb1b4b-499e-4d08-af0e-2fd8558292f5.json
│   │   ├── 134f59f5-68c4-4a75-ad54-49ee1fe3af5f.json
│   │   ├── 143e92a6-d47a-4ab8-b463-5cf32b45077e.json
│   │   ├── 14f60842-9141-4540-a257-2107b3840c80.json
│   │   ├── 164499d5-ef77-410b-ad79-42165d45d103.json
│   │   ├── 1736a75d-1334-4b18-aea4-9798c98ba4e8.json
│   │   ├── 1779b066-e9f4-4d39-ba10-523c691f79e7.json
│   │   ├── 17d3ae2f-fc3b-438f-8fa1-2a8434f67e9b.json
│   │   ├── 17ee612c-94c1-4e20-beb4-914e20b26717.json
│   │   ├── 18d49eb6-6b14-4e6c-aac6-8d3bb2f784d2.json
│   │   ├── 1919ba57-7283-43a1-82a1-00d1fe05d602.json
│   │   ├── 19a41424-2c98-4afa-8283-d58e9022d5d7.json
│   │   ├── 19b9cedd-a1e1-49c6-b92f-76a58066ae6e.json
│   │   ├── 1a97afba-09a5-4042-aaab-8f7a271e0710.json
│   │   ├── 1bb510ee-7488-42fa-957a-bb982c6c229a.json
│   │   ├── 1d8a7a60-09f7-4cf3-b00f-9aae7735cee5.json
│   │   ├── 20f37f68-f96e-40f1-a050-ebc83c10ac1c.json
│   │   ├── 22c37db9-5b93-4270-8d56-ea8490ac772b.json
│   │   ├── 254a692c-d0c5-4c50-8bab-ca9d95aa0e3c.json
│   │   ├── 26ba9332-d8b8-4f7f-83a9-74de1dbf18b2.json
│   │   ├── 2741c4ad-2be4-4fec-b620-0d6913539f91.json
│   │   ├── 277f37ad-f84f-4a4e-a53f-1463f9106bf1.json
│   │   ├── 279f3f5a-e69a-4231-9af7-d9de02dee880.json
│   │   ├── 2a366a92-c7fd-4358-b473-1ba2cc050147.json
│   │   ├── 2bec137f-46ab-46a3-98de-53f09f01b410.json
│   │   ├── 32271527-cf20-4f7b-8cf7-693a3f5006b7.json
│   │   ├── 327d4354-0c53-4c26-b20c-a8f809fbd4f6.json
│   │   ├── 336f5dda-9c4d-4b4d-b311-5a376f85bc64.json
│   │   ├── 354da2b3-e3d1-4f75-ab6c-f2aef593ba75.json
│   │   ├── 359eaaa0-3169-46f8-898a-04bed9982098.json
│   │   ├── 3a2fcd2a-a220-4100-bd66-1bf8a3a16f46.json
│   │   ├── 3a6472af-25c0-4ce2-9c39-20e0f481e912.json
│   │   ├── 3b27ff7a-816e-4848-ba0c-7b7f61877763.json
│   │   ├── 3b531b96-cb45-43ba-bffe-456cc36a0a43.json
│   │   ├── 3be3797a-6fba-464d-a366-4b99cadf39d6.json
│   │   ├── 3d12c945-7107-4f99-916e-186f19127ef4.json
│   │   ├── 400d264a-f411-4a45-915e-dc0d4c3f7f5f.json
│   │   ├── 42201b30-0117-4db4-a12a-a74707d7dcb6.json
│   │   ├── 456162b2-28f0-4af0-84f8-f0c05b4de8c4.json
│   │   ├── 4d43cdff-93f2-49e1-ae79-651444a48b94.json
│   │   ├── 4fd58e78-49b7-4014-bdf2-e46489d87315.json
│   │   ├── 5064d1fe-a8df-483b-93b7-5e8ec5b4fb62.json
│   │   ├── 560418ab-8405-415a-83fd-51b8e1d7f0f5.json
│   │   ├── 56560cc0-1c7f-44bd-b380-d7f99547eaff.json
│   │   ├── 56d018d5-9c68-45c8-8207-ce9250587397.json
│   │   ├── 57729ba2-3a7f-47fe-b8ac-feefc859e988.json
│   │   ├── 584cd095-21ec-4c15-9a9a-d4c323c811e7.json
│   │   ├── 59a7d224-19fc-4ff6-8d8e-2209524fe84c.json
│   │   ├── 5d2f011e-42f1-4d32-8f07-05f00d52330b.json
│   │   ├── 5e05f75c-ca85-4312-8149-08e58cedcbdc.json
│   │   ├── 5f581c38-106c-49cc-8a22-e1bc90824957.json
│   │   ├── 62d22f94-74a1-4b42-a1b3-bc6c2c5ed2f1.json
│   │   ├── 6440394c-a1ae-4bae-9544-88335028441a.json
│   │   ├── 6b98e6b8-1507-4270-b30c-eb21798c8554.json
│   │   ├── 6f2304a6-5ff3-4ef4-a316-026f6efe1bb5.json
│   │   ├── 70cc66b2-143f-483c-8909-cf01b1241d0a.json
│   │   ├── 7182b4ec-689b-429d-878b-e1417ea43325.json
│   │   ├── 72c01e35-682e-4c47-bebc-213f7035a217.json
│   │   ├── 731a9ce4-0ad2-4ce8-842d-8a4018fc4c7d.json
│   │   ├── 734c37a8-f61f-466f-96c5-92e6c8fe9f14.json
│   │   ├── 74d3a5f9-f697-4bdc-a07b-48b01d7e13bc.json
│   │   ├── 755b5e03-5e56-47ee-8381-ce2c9aede58a.json
│   │   ├── 75cbeb28-a887-4a23-b2bb-ab88a8ace72f.json
│   │   ├── 767e7122-6825-495a-be46-2ca4480da111.json
│   │   ├── 78dfaf55-e159-4555-aeec-85b875f2df07.json
│   │   ├── 797a2dd0-2d22-4f07-8555-27d30155b78b.json
│   │   ├── 7a379287-3f1b-4593-9b5c-fe451c2cad0b.json
│   │   ├── 7d929738-4591-411b-bd79-3d118367f1f1.json
│   │   ├── 81a2fb03-ae0f-45a5-b984-02497072dabb.json
│   │   ├── 823042f0-d451-4ded-b817-d08b34647bd2.json
│   │   ├── 82edcbe1-dc0a-402c-b2f1-23a803c3ae76.json
│   │   ├── 83d2bdf8-401c-48c6-b5e0-a36c7b5b27c2.json
│   │   ├── 84a13b8b-f1ed-4167-aa23-411740ce6c7f.json
│   │   ├── 851e771f-07b9-43f2-851e-3afb38512eab.json
│   │   ├── 85f30e2a-b47f-4996-b1e9-f9d4dd5cb82a.json
│   │   ├── 876b502a-2f35-49a0-9ff4-4dc163a4a491.json
│   │   ├── 87cb2944-74c2-4cd1-b426-b307325b832b.json
│   │   ├── 8b4e4da7-b8b4-48e7-9957-483542448afc.json
│   │   ├── 8c81a84f-789b-4371-8530-4a2c56757a9d.json
│   │   ├── 8c8871ce-5659-45ff-8815-9d67b1711660.json
│   │   ├── 8db7e1c7-398e-4d93-a973-ab14a22bd712.json
│   │   ├── 92fe9dda-bc9d-476e-805c-53ac25068eff.json
│   │   ├── 935d0664-96aa-4f61-925f-5feb25fc2d7e.json
│   │   ├── 944674f5-90c2-43ec-8ada-f132e6dbbb64.json
│   │   ├── 95677d1c-e028-4154-b0ca-c62bdcd4e426.json
│   │   ├── 9704f620-8642-49ec-badf-4cb983a62b4e.json
│   │   ├── 998b5648-2b52-483b-b748-f3aae2128c25.json
│   │   ├── 9a5bb5f3-4822-4667-9585-8550f62ac310.json
│   │   ├── 9b9beda1-758d-456f-a7e6-467a20416512.json
│   │   ├── 9bc86e10-b536-4007-878f-2cc3e0e86f28.json
│   │   ├── 9f913753-e90a-4609-959e-20551f60c6c0.json
│   │   ├── a145ba9a-0d90-426c-a73d-b4b2de813bf0.json
│   │   ├── a22ba6db-d1dc-49af-bbcc-6aae32ae13b5.json
│   │   ├── a2308116-ff62-453b-b78a-9a69fa1d6f01.json
│   │   ├── a39f6e05-8224-405a-bb3f-b03902b03901.json
│   │   ├── a5f965eb-c355-4fb1-a02b-bf33c30ad420.json
│   │   ├── a92e4449-95e8-4354-be6d-2a3d39a1c946.json
│   │   ├── ad53b040-8c32-43a8-8445-3f71cd221b07.json
│   │   ├── ae0041c2-2299-4c30-a4b8-e90ce5be7a9f.json
│   │   ├── ae3fc469-d804-40c6-96c9-c514c1662cb7.json
│   │   ├── b0e1062b-420c-40cf-b855-6bd92bf5ec88.json
│   │   ├── b14dfd20-021a-4cc0-90d1-2a094e5e673c.json
│   │   ├── b1c77a4f-9f9a-47d4-a37e-27e013f1880f.json
│   │   ├── b2006fe1-b108-4f3c-86e5-948302bead60.json
│   │   ├── b2b48c5c-55a5-475d-973f-5ff69a53236b.json
│   │   ├── b50f13df-1a77-40b8-89ef-d15528fd89fb.json
│   │   ├── b701787e-f902-4e6b-be81-b83ca5453b67.json
│   │   ├── b81ff09c-1fd5-46b7-9a31-acd8eb5fa001.json
│   │   ├── b9a211e7-d48b-4845-a208-98ad94e7de59.json
│   │   ├── bb14b2ec-7dca-43cb-9433-a15ec3d7b926.json
│   │   ├── bbf63cd8-28a8-49ce-8386-7137ec99fd68.json
│   │   ├── bd3a62a6-d1b4-4631-a702-3a4dfc2fe772.json
│   │   ├── bef4d30f-4383-404e-a5fe-cfc88af1b83d.json
│   │   ├── c034a7bd-e778-4a67-9bbb-9e9458f9d70c.json
│   │   ├── c1e65ba8-b64d-4fbd-b356-80c49b76ec7f.json
│   │   ├── c235dbbd-69f0-4bcd-a274-06b2c18ed13b.json
│   │   ├── c500a868-8cd0-4ff3-a300-6e3b314427a8.json
│   │   ├── c70df032-9975-45dd-96a0-7d6e3f55ad67.json
│   │   ├── cbf35549-f96b-460d-89fa-3120ae0648f6.json
│   │   ├── cce32945-33e1-4fcc-9d2a-e386bce24fc6.json
│   │   ├── cfd56c44-bf38-4d09-a35a-280c9640089d.json
│   │   ├── d070868d-71f7-4af3-ad04-5abbe8ef25ad.json
│   │   ├── d18741e3-487e-4ed7-9b70-f79cc84df762.json
│   │   ├── d68c3bb2-faf4-410a-a092-2f8a0ba5a1eb.json
│   │   ├── dcf5519e-4e19-4fd3-b38f-b5121b7b2afa.json
│   │   ├── df3b160d-86e2-4325-bc5f-1685c6ec050e.json
│   │   ├── e06f6d85-8469-4b44-af93-bd0bd4a1b312.json
│   │   ├── e2f19b11-0a1f-42da-b8c6-b8b7e60bd7fa.json
│   │   ├── e36dadc9-b0ad-4e1d-a7af-835969a82fb4.json
│   │   ├── ea2fc987-7a48-4927-88aa-c22a9de690e5.json
│   │   ├── ea5d0b28-08bc-4d8b-8b05-0ab015cf2a27.json
│   │   ├── eb2227c1-7201-488e-9d5c-097501eee337.json
│   │   ├── eb671ca2-fbe8-4659-957d-6f6a8db61cf5.json
│   │   ├── ecea0f7c-82b4-4778-a489-e5a17b6e487f.json
│   │   ├── ed0e35f2-7f2d-4b06-8754-7bd0cc4befa2.json
│   │   ├── edb48f7d-75de-478b-801b-07fb9fd8be25.json
│   │   ├── effdc126-f920-4a44-82e5-99a451f7dbf7.json
│   │   ├── f256d3eb-a414-4048-b0c8-4ff3d8356e36.json
│   │   ├── f28005bc-7a08-41f1-80b8-4acadf9a5146.json
│   │   ├── f56b2c3b-7d9d-47b7-aec2-f61150cc51e0.json
│   │   ├── f60aec12-713c-4c8f-bcb2-488163d2a27d.json
│   │   ├── f76312fb-2e42-460a-ae95-4c34b0d15e93.json
│   │   ├── f8f2afe5-6337-471d-bf01-c5eba8beba8d.json
│   │   ├── fd36a56b-84e3-4c82-80e2-76aee0ee84ec.json
│   │   ├── fde403d0-3f41-436d-8e5c-7d21621039d0.json
│   │   ├── memory_index.json
│   │   └── session_index.json
│   ├── snapshots
│   ├── teams
│   ├── temp_scripts
│   │   └── script_1748312537.sh
│   ├── templates
│   ├── validation
│   │   ├── browser_tool_download_example.html
│   │   ├── mcp_data_path_validation_manifest.json
│   │   └── mcp_data_path_validation_report.md
│   ├── validation_tests
│   │   ├── all_tools_exo_sweep_20260210_100648_ca87b024
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260210_100802_eb85b254
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260210_104738_468e57c0
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260210_140112_98b16576
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260210_140416_811ea1f0
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260210_213859_8299a99d
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_004136_3d8364c8
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_020113_f70aed89
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_020641_6b577b58
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_021423_4079fa5e
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_021659_f5e880e4
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_055851_a4b6bca0
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   ├── all_tools_exo_sweep_20260211_074511_661eb23b
│   │   │   ├── download.txt
│   │   │   └── sample.txt
│   │   └── all_tools_exo_sweep_20260217_043952_412509fc
│   │       ├── download.txt
│   │       └── sample.txt
│   ├── visual
│   │   ├── screenshot_20260210_030419.png
│   │   ├── screenshot_20260210_030434.png
│   │   ├── screenshot_20260210_035155.png
│   │   ├── screenshot_20260210_035221.png
│   │   ├── screenshot_20260210_035704.png
│   │   ├── screenshot_20260210_040659.png
│   │   ├── screenshot_20260210_040812.png
│   │   ├── screenshot_20260210_044750.png
│   │   ├── screenshot_20260210_080124.png
│   │   ├── screenshot_20260210_080426.png
│   │   ├── screenshot_20260210_153911.png
│   │   ├── screenshot_20260210_184155.png
│   │   ├── screenshot_20260210_200131.png
│   │   ├── screenshot_20260210_200656.png
│   │   ├── screenshot_20260210_201435.png
│   │   ├── screenshot_20260210_201710.png
│   │   ├── screenshot_20260210_235910.png
│   │   ├── screenshot_20260211_014529.png
│   │   ├── screenshot_20260216_223855.png
│   │   ├── screenshot_20260216_223944.png
│   │   ├── screenshot_20260216_224010.png
│   │   ├── screenshot_20260227_152022.png
│   │   └── screenshot_20260227_152122.png
│   ├── web_cache
│   ├── workflows
│   ├── # File Tree: data.md
│   ├── 5-7-filetree-mcp-datadir.md
│   ├── TOOL_STANDARDIZATION_COMPLETE.md
│   ├── analytics.db
│   ├── autonomous_routing_context.json
│   ├── codex_ingest_state.json
│   ├── command_history.jsonl
│   ├── comprehensive_tool_validation_report_final.md
│   ├── comprehensive_validation.json
│   ├── concept_index.json
│   ├── distillation.db
│   ├── dynamic_test_5efdf972.txt
│   ├── dynamic_test_ec4a62d1.txt
│   ├── events.jsonl
│   ├── exports.db
│   ├── final_test_results.json
│   ├── importance_scores.json
│   ├── internal_failures.jsonl
│   ├── journal_index.json
│   ├── journal_memory_index.json
│   ├── mcp_todo.md
│   ├── memory_archive_1767914852.json
│   ├── memory_archive_1770717411.json
│   ├── memory_archive_1770718016.json
│   ├── memory_archive_1770720467.json
│   ├── memory_relationships.json
│   ├── memory_store.json
│   ├── precomputed_briefing.json
│   ├── sessions_ultimate.db
│   ├── shutdown_status.json
│   ├── teams.db
│   ├── templates.db
│   ├── test_download.txt
│   ├── test_file_operations.txt
│   ├── testing_success_report.md
│   ├── thought_journal.json
│   ├── tool_completion_success_report.md
│   ├── tool_validation_report.txt
│   ├── tool_validation_results.json
│   └── verify_fe2a34b2.txt
├── databus
│   ├── __init__.py
│   ├── openrouter.yaml
│   ├── openrouter_wrapper.py
│   └── sovereign_openrouter.py
├── docs
│   ├── Custom-Services
│   │   ├── Claude
│   │   └── chatgpt
│   │       ├── chatgpt-app-guide.md
│   │       ├── chatgpt-authenticate-users.md
│   │       └── chatgpt-build-ui.md
│   ├── analysis
│   │   ├── exoskeleton_drift_analysis.md
│   │   └── session_and_context_tool_comparison.md
│   ├── file-trees
│   │   ├── # File Tree: muadib.md
│   │   ├── 4-23-2026-filetree-Somnus-MCP.md
│   │   ├── 4-23-2026-tools-filetree.md
│   │   ├── 4-24-2026-muaddib-filetree.md
│   │   ├── 5-10-2026-filetree.md
│   │   ├── 5-5-26-filetree-mcp.md
│   │   ├── 5-7-2026-near-final-filetree.md
│   │   └── 5-9-2026-updates.md
│   ├── plans
│   │   ├── muaddib_2_implementation_plan.md
│   │   ├── muaddib_plan.md
│   │   └── walkthrough.md
│   ├── prompts
│   │   └── claude_exoskeleton_lag_fix_prompt.md
│   ├── reports
│   ├── research
│   │   ├── Windows 11 AI Coding Assistant Report.md
│   │   ├── copilot_integration_guide.md
│   │   └── copilot_usage_manual.md
│   ├── ARCHITECTURE_MAP.md
│   ├── DASHBOARD_QUICKSTART.md
│   ├── DEPLOYMENT_COMPLETE.md
│   ├── DISTRIBUTION.md
│   ├── MAYBE_TOOLS_REPORT.md
│   ├── MCP_SPEC.md
│   ├── MY_ORIGINAL_HANDOFF_SPEC.md
│   ├── QUICK_SHARE_GUIDE.md
│   ├── SHARING_WITH_KIMI.md
│   ├── SOVEREIGN_MCP_WAR_ROOM.md
│   ├── SUMMARY.md
│   ├── enhanced_code_analysis_completion_report.md
│   ├── expose_mcp_to_internet.md
│   ├── https_wrapper_endpoints.md
│   ├── quick_reference.md
│   ├── wishlist.md
│   └── workflows-1.md
├── muadib
│   ├── 5-7-26-muadib.md
│   ├── README.md
│   ├── __init__.py
│   ├── advanced_bridge.py
│   ├── aeron_neural_memory.py
│   ├── code_and_structured_modality.py
│   ├── continual_learning_module.py
│   ├── knowledge_graph_attention.py
│   ├── memory_attention_classes.py
│   ├── muaddib.py
│   ├── neural_config.py
│   ├── neural_memory_network.py
│   ├── structured_data_modalities.py
│   ├── tool_modality.py
│   └── unified_modality.py
├── scripts
│   ├── benchmark_exoskeleton_latency.py
│   ├── codex_distill_formatter.py
│   ├── start_server.sh
│   └── sync_workflows_to_golden_paths.py
├── tests
│   └── test_auto_tool_module_perf.py
├── tools
│   ├── __init__.py
│   ├── auto_tool_module.py
│   ├── enhanced_code_analysis_tool.py
│   ├── enhanced_web_tool.py
│   ├── exoskeleton_tool.py
│   ├── file_tool.py
│   ├── lisan_al_gaib.py
│   ├── memory_interconnect.py
│   ├── memory_tool.py
│   ├── openrouter_agent_tool.py
│   ├── openrouter_planner_tool.py
│   ├── project_context_tool.py
│   ├── session_manager_tool.py
│   ├── shell_tool.py
│   ├── thought_journal_tool.py
│   ├── visual_tool.py
│   └── web_tool.py
├── 5-22-2026-muaddib-mcp-filetree.md
├── AGENTS.md
├── ARCHITECTURE.md
├── ARCHITECTURE_MAP.md
├── CONTEXT.md
├── HOOK_BRIDGE.md
├── MCP_SPEC.md
├── MCP_UPDATES.md
├── MEMORY.md
├── NOTES.md
├── PLAN.md
├── README.md
├── Sovereign MCP Distillation Pipeline.md
├── all_tools.json
├── claude_desktop_config.json
├── codex-AGENTS.md
├── config_manager.py
├── golden_paths.json
├── golden_paths_meta.json
├── hook_executor.py
├── hooks_manifest.json
├── https_wrapper.py
├── intelligent_output_hook.py
├── manifest.json
├── mcp.json
├── mcp_api.py
├── mcp_server.py
├── openapi_builder.py
├── somnus_mcp_icon.png
├── sovereign_context_hook.py
├── sse_broadcaster.py
├── test_https_wrapper.py
├── tool_manifest.json
├── webhook_engine.py
└── workflows.md
```

---
*Generated by FileTree Pro Extension*
