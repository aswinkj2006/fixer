# FixIQ — Research & Sources

All links below were found during project research and directly informed the design choices in the other handoff files. Organized by category.

## CMMS (Computerized Maintenance Management Systems) — how industry actually stores maintenance data
- IBM — "What is CMMS for Manufacturing?" — https://www.ibm.com/think/topics/cmms-for-manufacturing
- Maintainly — "How Does CMMS Help with Predictive Maintenance in Manufacturing" — https://maintainly.com/articles/how-does-cmms-help-with-predictive-maintenance-in-manufacturing
- OxMaint — "Manufacturing Maintenance Data Governance & CMMS Guide" (source of the Problem → Cause → Remedy failure-code taxonomy pattern used in this project) — https://oxmaint.com/industries/manufacturing-plant/manufacturing-maintenance-data-governance-cmms

## Official international standards
- ISO 13374 (condition monitoring data processing/communication — the pipeline this project's architecture is mapped to) — https://www.iso.org/standard/21832.html
- ISO 13374 explainer — https://vibromera.eu/glossary/iso-13374/
- ISO 14224 (reliability/maintenance data collection) — referenced via: https://worktrek.com/blog/standards-for-maintenance-professionals/

## Industry-specific quality/compliance standards (automotive & aerospace)
- OxMaint — aerospace manufacturing maintenance & AS9100 compliance guide — https://oxmaint.com/industries/manufacturing-plant/aerospace-manufacturing-maintenance-as9100-compliance
- AS9100 vs IATF 16949 comparison — https://www.greattaiwangear.com/blog/as9100-vs-iatf-16949-comparison-gear-manufacturers/
- Wikipedia — IATF 16949 — https://en.wikipedia.org/wiki/IATF_16949

## Robotics-specific condition monitoring
- Siemens — industrial robots predictive maintenance — https://www.siemens.com/es-mx/industries/automotive/industrial-robots-predictive-maintenance/
- IMEKO — "Condition Monitoring Concept for Industrial Robots" (MEMS vibration sensors on axis joints) — https://imeko.org/proceedings/condition-monitoring-concept-for-industrial-robots
- Published research paper on robotics assembly-line condition monitoring — https://research.science.eus/documentos/61d0d2622c8e992667ef087e

## Academic / technical grounding on predictive maintenance methods
- arXiv — downtime prediction using Random Forest and LSTM — https://arxiv.org/pdf/2205.09402
- NCBI/PMC — predictive maintenance model for flexible manufacturing under Industry 4.0 — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8427870/
- NCBI/PMC — remaining useful life (RUL) prediction using linear regression, neural nets, decision trees — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10611286/

## Real machine manuals (for RAG ingestion — M-01, the 6-axis robotic welding arm)
The project models M-01 on the real **FANUC ARC Mate 100iD / 120iD** family, a real 6-axis arc-welding robot with publicly hosted manuals:
- FANUC ARC Mate 100iD Mechanical Unit Maintenance Manual — https://www.scribd.com/document/715708955/Fanuc-ARC-Mate-100i-Be-Mechanical-Unit-Maintenance-Manual
- FANUC Robot ARC Welding Manual (R-30+B operator's manual, B-83614EN-4_02_01) — https://www.scribd.com/document/889564384/B-83614EN-4-02-01
- FANUC LR Mate 200iD / ARC Mate 50iD Mechanical Unit Operator's Manual (hosted on Haas CNC's own service CDN) — https://www.haascnc.com/content/dam/haascnc/en/service/reference/fanuc-manuals/Fanuc%20Robot%20LR%20Mate%20200iD%20Operators%20Manual.pdf
- FANUC Mechanical Unit Operator's Manual, HRP-1 (Haas CNC CDN) — https://www.haascnc.com/content/dam/haascnc/service/guides/online-manuals/haas-robot-package/fanuc-manuals/HRP-1-Mechanical-Unit-Operators-Manual.pdf
- FANUC Mechanical Unit Operator's Manual, HRP-2 (Haas CNC CDN) — https://www.haascnc.com/content/dam/haascnc/service/guides/online-manuals/haas-robot-package/fanuc-manuals/HRP-2-Mechanical-Unit-Operators-Manual.pdf
- FANUC Robot ARC Mate 120iC Operator's Manual (hosted by Migatronic, a welding equipment manufacturer, B-82874EN/07) — https://www.migatronic.com/media/1384/manual_am-120ic_operator_manual_b-82874en_07.pdf
- FANUC Robot Series 120iB 10L Operator's Manual — https://www.scribd.com/document/654227217/FANUC-Robot-Series-120iB-10L-Operator-s-Manual
- FANUC ArcMate 120 Mechanical Unit Maintenance — https://www.scribd.com/document/232653991/ArcMate-120-Mechaical-Unit-Mantenance
- FANUC R-30iB / R-30iB Mate Arc Welding Controller Operator's Manual — https://studylib.net/doc/27731758/fanuc---operator-manual
- FANUC ARC Mate 120iB Maintenance Manual — https://studylib.net/doc/26028273/fanuc-120ib-maintenance-manual

Note: pull these into the project's own vector DB as data for chunking/embedding. Do not ask an LLM to reproduce large verbatim sections of these documents in chat — there is no issue with downloading and processing them directly in the project's own pipeline.

For M-02 (CNC mill), Haas publishes its own CNC service/maintenance manuals on the same domain (haascnc.com) — pick a real Haas mill model to match and source its manual the same way.

For M-04 (torque calibration station), ISO 6789 governs torque wrench calibration procedure and is a legitimate reference point for that machine's narrative even without a full manual.

## Offline / local LLM model research (2026)
- Ollama Models Cheat Sheet 2026 — https://computingforgeeks.com/ollama-models-cheat-sheet/
- "Best Ollama Models 2026: 25+ Ranked by VRAM & SWE-Bench" — https://www.morphllm.com/best-ollama-models
- "The Best Local Vision Language Models in 2026" — https://tinyweights.dev/posts/best-local-vision-language-models-2026/
- Gemma 3 4B IT QAT Q4 model card — https://featherless.ai/models/Overworld-Models/gemma-3-4b-it-qat-q4_0-unquantized
- "Best Ollama Models for 8GB RAM in 2026" — https://webscraft.org/blog/ollama-na-8-gb-ram-yaki-modeli-pratsyuyut-u-2026?lang=en
- Typhoon OCR 1.5 3B QAT (small on-device vision-language OCR model) — https://huggingface.co/scb10x/typhoon-ocr1.5-3b-qat
- Devstral-Vision-Small-2507 GGUF (multimodal coding-focused model, for reference) — https://huggingface.co/QuixiAI/Devstral-Vision-Small-2507-gguf/blob/main/README.md
- "Best Small Language Models 2026: Top SLMs Ranked (1B–14B)" — https://localaimaster.com/blog/small-language-models-guide-2026
- Gemma 3 4B interview-eval quantized GGUF (example Ollama/llama.cpp packaging notes for vision models) — https://huggingface.co/Parth673/gemma3-4b-interview-eval-quantized/blob/main/README.md
