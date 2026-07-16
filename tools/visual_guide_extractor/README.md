# Visual Guide Extraction PoC

This independent tool demonstrates how three representative Antikor v2 guide
pages can be converted into reviewable extraction artifacts. It does not
modify the KnowledgeChat API, RAG flow, frontend, embedding provider, or
ChromaDB collection.

## Fixed PoC scope

The runner processes exactly three configured pages:

1. `Dinamik NAT` as a compact, mostly textual guide.
2. `Güvenlik Kuralları` as a form and UI-heavy guide.
3. `Hızlı Kurulum Kılavuzu` as a multi-screenshot, step-oriented guide.

There is no link discovery or full-site crawling in this PoC.

## Setup on Windows 11

Run these commands from the repository root:

```powershell
python -m venv tools\visual_guide_extractor\.venv
tools\visual_guide_extractor\.venv\Scripts\python.exe -m pip install -r tools\visual_guide_extractor\requirements.txt
```

Run the static extraction without a vision model:

```powershell
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_poc
```

Run the tests:

```powershell
tools\visual_guide_extractor\.venv\Scripts\python.exe -m unittest discover -s tools\visual_guide_extractor\tests -v
```

## Install Qwen2.5-VL

Keep Ollama running, then install the vision model once:

```powershell
ollama pull qwen2.5vl:7b
```

Confirm that `qwen2.5vl:7b`, `gemma3:12b`, and the existing embedding model
appear in `ollama list`.

## Run real vision extraction

The default run downloads HTML and screenshots but does not call Ollama. This
makes crawler validation possible before the vision model is installed.

First generate or refresh the fixed three-page static PoC dataset:

```powershell
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_poc
```

Then analyze the existing 15 screenshots and normalize the three page results:

```powershell
$env:VISUAL_GUIDE_VISION_MODEL="qwen2.5vl:7b"
$env:VISUAL_GUIDE_NORMALIZATION_MODEL="gemma3:12b"
$env:VISUAL_GUIDE_REQUEST_TIMEOUT="300"
$env:VISUAL_GUIDE_VISION_CONTEXT_WINDOW="8192"
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_vision_poc
```

Force a calibrated re-run of all 15 images and all three normalized drafts:

```powershell
$env:VISUAL_GUIDE_FORCE_VISION="true"
$env:VISUAL_GUIDE_FORCE_NORMALIZATION="true"
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_vision_poc
```

Qwen and Gemma have deliberately separate responsibilities:

- **Qwen2.5-VL 7B** receives one screenshot, nearby authoritative HTML, and
  existing extraction metadata. It returns only strict JSON describing visible
  controls, fields, steps, warnings, and uncertainties. It never writes
  Markdown.
- **Gemma 3 12B** receives only static HTML extraction and validated Qwen JSON.
  It is an optional fallback for difficult pages. It may clean Turkish language,
  organize sections, and remove duplicate explanations, but is forbidden from
  adding UI information, completing missing steps, or guessing workflows.

The default path does not call Gemma. It copies validated HTML/Qwen evidence into
a deterministic guide, runs the final quality gate, and renders approved
Markdown. Gemma is considered only for low confidence, excessive warnings or
uncertainties, unsupported structure, or complex multi-image/multi-step pages.
The fallback decision is recorded in `reports/gemma_usage_report.json`.

The models run sequentially and are unloaded between stages so they do not
compete for the RTX 4060's 8 GB VRAM.

The 8192-token vision context is required for the largest 2500-pixel-wide PoC
screenshots; Ollama's default 4096-token context is exhausted by their visual
tokens before the HTML context and output schema are added. The runner resumes
validated image results, so a retry does not repeat completed Qwen analyses.

## Draft outputs

All artifacts stay under:

```text
work/visual_guide_extraction/
├── pages/            # Ordered HTML extraction as JSON
├── images/           # Temporary downloaded screenshots
├── vision_results/   # Schema-validated Qwen JSON grouped by page
├── normalized_results/ # Gemma editorial JSON and Markdown drafts
└── reports/          # Run summaries and vision quality report
```

The Markdown previews in `reports/` are placeholders for review. They contain a
prominent draft warning and are never written to `knowledge_base`.

## Why extraction output is not indexed directly

Screenshot interpretation can contain OCR mistakes, UI-version mismatches, or
unsupported inferred steps. Work artifacts are therefore never passed directly
to the indexer. Sprint 20 promoted only the 42 guides that passed the quality
gate and compatibility checks into `knowledge_base/guides/antikor_v2/`; images,
model JSON, reports, and rejected drafts remain local under `work/`.

The vision quality report is written to
`work/visual_guide_extraction/reports/vision_quality_report.json`. A successful
PoC run is evidence for review, not automatic approval for full-site crawling.

Calibration comparison is written to
`work/visual_guide_extraction/reports/quality_before_after.json`. The quality
validator flags translated Turkish labels, steps that quote unknown controls,
weakly supported claims, and control/field overlap. These findings are review
signals; they never cause automatic indexing.

## Final quality gate

The current flow is Qwen JSON -> Qwen validation -> deterministic Markdown ->
final quality validation -> approved draft Markdown. Gemma normalization is an
optional fallback before the final gate for difficult pages only. The final gate
checks every action against Qwen controls and fields, preserves Turkish UI
labels, rejects unsupported menu paths, and detects English prose while allowing
terms such as IP, DNS, NAT, Firewall, IPv4, and IPv6.

Each guide receives `confidence_score`, `warnings`, and `approved`. Markdown is
written to `work/visual_guide_extraction/approved_drafts/` only when no
unsupported action, translated UI label, or critical language warning remains.
Removed sentences stay auditable in
`work/visual_guide_extraction/reports/quality_final_report.json`. Approval means
only that the draft passed the automated PoC gate; it is still not copied to
`knowledge_base` and is not indexed.

Run the optional-fallback PoC directly with:

```powershell
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_fallback_poc
```

Validated Gemma fallback results are resumable. Set
`VISUAL_GUIDE_FORCE_NORMALIZATION=true` only when a live re-normalization is
required; otherwise an existing validated fallback result is reused.

## Critical-category pilot and promotion

The checkpointed Sprint 19 pilot discovers only the configured critical
Antikor v2 categories, reuses valid cached Qwen results, and records every
Gemma fallback decision:

```powershell
tools\visual_guide_extractor\.venv\Scripts\python.exe -m tools.visual_guide_extractor.scripts.run_sprint19_pilot
```

`recover_sprint19_rejected` retries only invalid page-level fallback output and
never reprocesses the full image set. `promote_sprint20` validates the approved
Markdown contract before copying reviewed guides into
`knowledge_base/guides/antikor_v2/`. `validate_sprint20_compatibility` verifies
that promoted files work with the existing loader, parser, chunker, and metadata
pipeline. The promotion and indexing operations remain explicit; running the
crawler alone cannot modify the knowledge base or ChromaDB.
