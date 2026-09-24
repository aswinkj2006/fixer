"""
Generate Fixer.ai Hackathon Studybook & Pitch Guide as a publication-grade PDF.
Encodes screenshots as base64 and renders via Headless Chrome with modern CSS.
"""
import base64
import os
import subprocess
import sys

BASE_DIR = r"c:\Users\Aswin K J\Documents\Projects\fixer.ai"
BRAIN_DIR = r"C:\Users\Aswin K J\.gemini\antigravity-ide\brain\6506f979-1e88-4d14-b684-e8617d799125"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HTML_OUTPUT = os.path.join(BASE_DIR, "studybook.html")
PDF_OUTPUT = os.path.join(BASE_DIR, "FixerAI_Hackathon_Studybook.pdf")

IMAGE_FILES = {
    "dashboard": os.path.join(BRAIN_DIR, "dashboard_overview_1790144001646.png"),
    "sim": os.path.join(BRAIN_DIR, "sim_control_room_1790144002776.png"),
    "detail_full": os.path.join(BRAIN_DIR, "machine_detail_full_1790144057507.png"),
    "m01": os.path.join(BRAIN_DIR, "m01_tuned_1790089080096.png"),
    "m02": os.path.join(BRAIN_DIR, "m02_final_1790089844721.png"),
    "m03": os.path.join(BRAIN_DIR, "m03_tuned_1790089284455.png"),
    "m04": os.path.join(BRAIN_DIR, "m04_tuned_1790089366394.png"),
}

def get_base64_img(path: str) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded}"
    print(f"Warning: Image not found at {path}")
    return ""

img_b64 = {k: get_base64_img(v) for k, v in IMAGE_FILES.items()}

HTML_CONTENT = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fixer.ai — Hackathon Studybook & Team Master Guide</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

  @page {{
    size: A4 portrait;
    margin: 12mm 12mm 14mm 12mm;
    @bottom-right {{
      content: counter(page);
    }}
  }}

  * {{
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #1e293b;
    background: #ffffff;
    line-height: 1.5;
    font-size: 9.5pt;
    margin: 0;
    padding: 0;
  }}

  h1, h2, h3, h4 {{
    color: #0f172a;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 0;
  }}

  h1 {{ font-size: 24pt; margin-bottom: 8pt; }}
  h2 {{ font-size: 15pt; margin-top: 0; margin-bottom: 8pt; border-bottom: 2px solid #e2e8f0; padding-bottom: 4pt; }}
  h3 {{ font-size: 11pt; margin-top: 8pt; margin-bottom: 4pt; color: #1e40af; }}
  h4 {{ font-size: 9.5pt; margin-top: 6pt; margin-bottom: 3pt; }}

  p {{ margin-top: 0; margin-bottom: 6pt; text-align: justify; }}

  .page-break {{
    page-break-before: always;
  }}

  /* Cover Page */
  .cover {{
    height: 98vh;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: linear-gradient(135deg, #090d16 0%, #111827 50%, #1e1b4b 100%);
    color: #ffffff;
    padding: 36pt 30pt;
    border-radius: 8pt;
  }}

  .cover-badge {{
    display: inline-block;
    background: rgba(59, 130, 246, 0.2);
    border: 1px solid #3b82f6;
    color: #93c5fd;
    font-family: 'JetBrains Mono', monospace;
    font-size: 8.5pt;
    font-weight: 700;
    padding: 4pt 12pt;
    border-radius: 9999px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 14pt;
  }}

  .cover-title {{
    font-size: 34pt;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 10pt;
    color: #ffffff;
  }}

  .cover-title span {{
    background: linear-gradient(90deg, #60a5fa 0%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .cover-subtitle {{
    font-size: 12.5pt;
    color: #94a3b8;
    line-height: 1.5;
    max-width: 90%;
    margin-bottom: 18pt;
  }}

  .cover-meta {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12pt;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8pt;
    padding: 12pt;
    margin-top: auto;
  }}

  .meta-item-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 7.5pt;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .meta-item-val {{
    font-size: 10.5pt;
    font-weight: 700;
    color: #ffffff;
    margin-top: 2pt;
  }}

  /* Callout Cards */
  .card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 6pt;
    padding: 7pt 10pt;
    margin-bottom: 7pt;
  }}

  .card-pain {{
    background: #fef2f2;
    border-color: #fee2e2;
    border-left-color: #ef4444;
  }}

  .card-hack {{
    background: #eff6ff;
    border-color: #dbeafe;
    border-left-color: #2563eb;
  }}

  .card-tip {{
    background: #f0fdf4;
    border-color: #dcfce7;
    border-left-color: #16a34a;
  }}

  .card-analogy {{
    background: #faf5ff;
    border-color: #f3e8ff;
    border-left-color: #9333ea;
  }}

  .card-title {{
    font-size: 9.5pt;
    font-weight: 800;
    margin-bottom: 3pt;
    display: flex;
    align-items: center;
    gap: 6pt;
  }}

  .card-pain .card-title {{ color: #b91c1c; }}
  .card-hack .card-title {{ color: #1d4ed8; }}
  .card-tip .card-title {{ color: #15803d; }}
  .card-analogy .card-title {{ color: #7e22ce; }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 6pt;
    margin-bottom: 8pt;
    font-size: 8.5pt;
  }}

  th, td {{
    padding: 5pt 7pt;
    text-align: left;
    border: 1px solid #e2e8f0;
  }}

  th {{
    background: #f1f5f9;
    font-weight: 700;
    color: #334155;
    text-transform: uppercase;
    font-size: 7.5pt;
    letter-spacing: 0.04em;
  }}

  tr:nth-child(even) {{ background: #f8fafc; }}

  /* Screenshot Showcase */
  .screenshot-box {{
    margin: 8pt 0 4pt 0;
    border: 1px solid #cbd5e1;
    border-radius: 6pt;
    overflow: hidden;
    background: #0f172a;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  }}

  .screenshot-img {{
    width: 100%;
    display: block;
    max-height: 250pt;
    object-fit: contain;
    background: #0f172a;
  }}

  .screenshot-img-small {{
    width: 100%;
    display: block;
    max-height: 155pt;
    object-fit: contain;
    background: #0f172a;
  }}

  .screenshot-caption {{
    background: #f8fafc;
    padding: 5pt 8pt;
    font-size: 7.5pt;
    color: #475569;
    border-top: 1px solid #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
    display: flex;
    justify-content: space-between;
  }}

  /* Grid layout for dual columns */
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8pt;
    margin-bottom: 6pt;
  }}

  .pill {{
    display: inline-block;
    padding: 1.5pt 5pt;
    border-radius: 4pt;
    font-size: 7pt;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
  }}
  .pill-green {{ background: #dcfce7; color: #15803d; }}
  .pill-blue {{ background: #dbeafe; color: #1d4ed8; }}
  .pill-amber {{ background: #fef3c7; color: #b45309; }}
  .pill-red {{ background: #fee2e2; color: #b91c1c; }}

  .code-inline {{
    font-family: 'JetBrains Mono', monospace;
    background: #f1f5f9;
    padding: 1pt 3pt;
    border-radius: 3pt;
    font-size: 8pt;
    color: #0f172a;
    border: 1px solid #e2e8f0;
  }}

  .chapter-header {{
    display: flex;
    align-items: center;
    gap: 8pt;
    margin-bottom: 6pt;
  }}
  .chapter-num {{
    background: #2563eb;
    color: #ffffff;
    font-weight: 800;
    font-size: 8.5pt;
    padding: 2pt 7pt;
    border-radius: 4pt;
    font-family: 'JetBrains Mono', monospace;
  }}
</style>
</head>
<body>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 1: COVER PAGE                                                          -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="cover">
  <div>
    <div class="cover-badge">🏆 Hackathon Master Studybook & Pitch Manual</div>
    <div class="cover-title">FIXER.<span>AI</span></div>
    <div style="font-size: 15pt; font-weight: 700; color: #60a5fa; margin-bottom: 12pt;">
      Industrial Prognostics & Multimodal Maintenance Digital Twin
    </div>
    <div class="cover-subtitle">
      A complete, jargon-free guide for the team: Understanding our empathy, the pain point, machine mechanics in plain English, app architecture, live demo script, and judge Q&A strategies to win the hackathon.
    </div>
  </div>

  <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10pt; margin: 18pt 0;">
    <div style="background: rgba(255,255,255,0.06); padding: 10pt; border-radius: 6pt; border: 1px solid rgba(255,255,255,0.1);">
      <div style="font-size: 18pt; font-weight: 800; color: #38bdf8;">$22,000</div>
      <div style="font-size: 7.5pt; color: #94a3b8; text-transform: uppercase;">Lost Per Minute of Downtime</div>
    </div>
    <div style="background: rgba(255,255,255,0.06); padding: 10pt; border-radius: 6pt; border: 1px solid rgba(255,255,255,0.1);">
      <div style="font-size: 18pt; font-weight: 800; color: #4ade80;">4 Assets</div>
      <div style="font-size: 7.5pt; color: #94a3b8; text-transform: uppercase;">Full 3D CCTV Digital Twins</div>
    </div>
    <div style="background: rgba(255,255,255,0.06); padding: 10pt; border-radius: 6pt; border: 1px solid rgba(255,255,255,0.1);">
      <div style="font-size: 18pt; font-weight: 800; color: #fbbf24;">14 Hours</div>
      <div style="font-size: 7.5pt; color: #94a3b8; text-transform: uppercase;">Advance Warning (RUL)</div>
    </div>
    <div style="background: rgba(255,255,255,0.06); padding: 10pt; border-radius: 6pt; border: 1px solid rgba(255,255,255,0.1);">
      <div style="font-size: 18pt; font-weight: 800; color: #c084fc;">Multimodal</div>
      <div style="font-size: 7.5pt; color: #94a3b8; text-transform: uppercase;">Voice, Photos & OEM AI</div>
    </div>
  </div>

  <div class="cover-meta">
    <div>
      <div class="meta-item-label">Target Audience</div>
      <div class="meta-item-val">Hackathon Judges & Evaluators</div>
    </div>
    <div>
      <div class="meta-item-label">Core Paradigm</div>
      <div class="meta-item-val">Prognostics > Diagnostics</div>
    </div>
    <div>
      <div class="meta-item-label">Document Purpose</div>
      <div class="meta-item-val">Internal Team Alignment & Pitch Script</div>
    </div>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 2: CHAPTER 1 - THE HUMAN STORY & EMPATHY                               -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 01</span>
  <h2>The Human Story & The Industrial Pain Point</h2>
</div>

<p>
  To win this hackathon, we must remember that <strong>judges don't invest in code; they invest in solutions to painful, expensive human problems</strong>. If we walk up and start listing Python frameworks and Three.js shaders, we will sound like every other team. But if we tell the real-life story of a factory floor in crisis, we grab their attention in 10 seconds.
</p>

<div class="card card-pain">
  <div class="card-title">🚨 The 2:00 AM Factory Floor Nightmare</div>
  <p style="margin-bottom: 0;">
    Imagine you are Dave, a lead maintenance technician at an automotive manufacturing plant. At 2:15 AM, your phone rings. An automated robotic welding cell has violently locked up on Line 3. The entire assembly line has screeched to a halt. Every single minute the line sits idle costs the company <strong>$22,000</strong>. Dave rushes onto the dark factory floor with a flashlight and a heavy, 800-page grease-stained paper manual binder. Sirens are blaring, the plant manager is screaming at him, and Dave has to guess: <em>Is it the motor? Did a bearing seize? Did a sensor fry? Which of the 6 robot joints is grinding?</em>
  </p>
</div>

<div class="grid-2">
  <div class="card">
    <div class="card-title">❌ Flaw 1: Run-To-Failure (Reactive)</div>
    <p style="font-size: 8.5pt; margin: 0;">
      Companies wait until something loudly explodes or locks up. By the time smoke appears, broken metal shards have chewed up gears and damaged neighboring machines. Repair costs jump 10x and lines stay frozen for days.
    </p>
  </div>
  <div class="card">
    <div class="card-title">❌ Flaw 2: Calendar-Based (Preventative)</div>
    <p style="font-size: 8.5pt; margin: 0;">
      Companies replace expensive machine parts every 6 months "just in case", like clockwork. 70% of the time, the replaced parts were perfectly healthy, wasting hundreds of thousands of dollars in premature scrap.
    </p>
  </div>
</div>

<div class="card card-tip">
  <div class="card-title">🎯 Our Empathy: Giving Dave a Sixth Sense Superpower</div>
  <p style="margin-bottom: 0;">
    <strong>Fixer.ai turns maintenance technicians into proactive superheroes.</strong> Instead of an emergency at 2 AM, Dave sits in a comfortable control room at 2 PM on Tuesday. His screen alerts him: <em>"Dave, the FANUC welding robot's Joint 2 reducer is running out of grease. You have exactly 14 hours of Remaining Useful Life before metal-on-metal wear begins. During the scheduled 4 PM shift break, grab a 14mm socket and 250ml of Mobilux EP2 grease to flush it."</em> Dave fixes it in 15 minutes. <strong>Zero panic. Zero downtime. Millions saved.</strong>
  </p>
</div>

<div class="card card-hack">
  <div class="card-title">💡 How to Pitch This in 30 Seconds to Judges</div>
  <p style="font-size: 8.5pt; margin: 0;">
    <em>"Judges, an automotive assembly line loses $22,000 every single minute it is down. Today, factory technicians either wait for machines to catch fire, or they drown in 600-page manuals trying to diagnose weird vibrations. We built Fixer.ai — a predictive digital twin that monitors factory machines in real-time 3D, predicts failures 14 hours before they happen, and guides technicians with multimodal AI."</em>
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 3: CHAPTER 2 - THE SCIENCE & RESEARCH                                  -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 02</span>
  <h2>The Science & Research Behind Fixer.ai</h2>
</div>

<p>
  When judges ask <em>"What makes your solution smarter than an alert on a dashboard?"</em>, this chapter gives you the ammunition to blow them away with proven engineering concepts.
</p>

<h3>1. Prognostics vs. Diagnostics (The Golden Distinction)</h3>
<div class="grid-2">
  <div class="card card-pain">
    <div class="card-title">Diagnostics (The Old Way)</div>
    <div style="font-size: 8pt; color: #64748b; margin-bottom: 2pt;">"The Autopsy Approach"</div>
    <p style="font-size: 8.5pt; margin: 0;">
      Waits for the machine to trip an error code. Answers the question: <em>"What just broke?"</em> It's too late — the line is already stopped and money is burning.
    </p>
  </div>
  <div class="card card-tip">
    <div class="card-title">Prognostics (The Fixer.ai Way)</div>
    <div style="font-size: 8pt; color: #16a34a; margin-bottom: 2pt;">"The Preventive Medicine"</div>
    <p style="font-size: 8.5pt; margin: 0;">
      Tracks microscopic trend shifts in torque and vibration. Answers the questions: <em>"When will this break, why is it degrading, and how do we prevent it right now?"</em>
    </p>
  </div>
</div>

<h3>2. Remaining Useful Life (RUL) — The Phone Battery Analogy</h3>
<div class="card card-analogy">
  <div class="card-title">📱 Real-Life Metaphor: How to Explain RUL to Anyone</div>
  <p style="margin: 0; font-size: 8.5pt;">
    Think of your smartphone battery. If your phone only gave you an alert when it died at 0%, you'd constantly be stranded with a dead phone. Instead, your phone shows <strong>"Battery: 18% (Estimated 2h 15m remaining)"</strong>. That estimate is <strong>Remaining Useful Life (RUL)</strong>. Fixer.ai calculates RUL in hours for heavy industrial equipment by tracking continuous wear curves, giving managers time to plan repairs during planned shift breaks.
  </p>
</div>

<h3>3. Why 3D Digital Twin CCTV? (Human Psychology)</h3>
<p>
  Traditional industrial software shows massive grids of green and red numbers (like a terrifying Excel spreadsheet with 500 rows). In a noisy factory under intense pressure, a human technician cannot process raw statistical deviations.
  <strong>Fixer.ai replaces the spreadsheet with visual reality.</strong> Through Three.js, we stream a live 3D digital twin resembling CCTV security footage:
</p>
<ul style="margin-top: 4pt; margin-bottom: 6pt; font-size: 9pt;">
  <li><strong>Spatial Intuition:</strong> The 3D robot arm physically shudders in real time when vibration spikes.</li>
  <li><strong>Thermal Fault Glow:</strong> The exact failing component (e.g. Joint 2 reducer) pulses with a vivid red glow.</li>
  <li><strong>Overhead Andon Beacon:</strong> Flashes red to indicate line-stop urgency, just like physical factory beacons.</li>
  <li>Anyone — from a seasoned technician to a non-technical judge — grasps the problem within 1 second.</li>
</ul>

<h3>4. Multimodal AI Assistant (Text + Voice + Vision)</h3>
<p>
  Why multimodal? Because factory technicians have dirty, grease-covered work gloves! They can't sit at a desk and type paragraphs on a keyboard. With Fixer.ai, they can speak naturally or snap a phone photo of a worn seal:
</p>
<div class="card card-tip" style="margin-bottom: 0;">
  <div class="card-title">🛡️ Two-Tier Constrained RAG Brain</div>
  <p style="font-size: 8.5pt; margin: 0;">
    The AI doesn't hallucinate or guess. <strong>Tier 1</strong> retrieves verified manufacturer OEM engineering manuals with strict semantic similarity thresholds (e.g., exact torque specs like "85 Nm with a torque wrench"). <strong>Tier 2</strong> pulls from historical shop-floor resolution notes, ensuring answers are grounded, compliant, and actionable.
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 4: MACHINE 1 (M-01: FANUC ARC MATE)                                    -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 03</span>
  <h2>Fleet Asset 1: FANUC ARC Mate 100iD (M-01)</h2>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6pt;">
  <div style="font-size: 13pt; font-weight: 800; color: #0f172a;">The 6-Axis Robotic Welder</div>
  <span class="pill pill-blue">Location: Bay 3 — Robotic Welding Cell A</span>
</div>

<p>
  <strong>What it is in real life:</strong> A giant, high-speed bright yellow robotic arm mounted to the factory floor, holding an automated electric welding torch. In automotive and aerospace plants, this robot operates 24/7 welding steel frames and car bodies together with sub-millimeter precision.
</p>

<div class="grid-2">
  <div class="card">
    <div class="card-title">🔧 Key Physical Components</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Joint 2 (Shoulder):</strong> Carries the massive leverage of the arm. Powered by an internal high-torque Harmonic Drive speed reducer gearset (the primary wear component).</li>
      <li><strong>Swan-Neck Torch:</strong> End nozzle producing high-heat electric arc welds.</li>
      <li><strong>Red R-30iB Cabinet:</strong> Standalone floor computer controller with louvers.</li>
      <li><strong>Dress Pack:</strong> Flexible green pneumatic line and black power conduits.</li>
    </ul>
  </div>
  <div class="card">
    <div class="card-title">📊 Sensor Telemetry Meaning</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Torque (Nm):</strong> Muscle effort. Normal = 15–20 Nm idle, up to 100 Nm moving. If it spikes to 130+ Nm, the internal gear teeth are grinding without lubricant!</li>
      <li><strong>Vibration (mm/s²):</strong> Shaking. Normal = ~1.0 mm/s². High vibration = bearing degradation or loose mounting bolts.</li>
      <li><strong>Cycle Count:</strong> Continuous completed robot weld cycles odometer.</li>
    </ul>
  </div>
</div>

<div class="screenshot-box">
  <img src="{img_b64['m01']}" class="screenshot-img" alt="M-01 Robot Arm Screenshot">
  <div class="screenshot-caption">
    <span>3D CCTV VIEW: FANUC ARC Mate 100iD Welding Cell (Recessed Pedestal, Red Controller & Slotted Table)</span>
    <span class="pill pill-green">Operational State</span>
  </div>
</div>

<div class="card card-tip" style="margin-top: 6pt;">
  <div class="card-title">💡 How to Demonstrate M-01 on Stage</div>
  <p style="font-size: 8.5pt; margin: 0;">
    Inject a fault into M-01 via <span class="code-inline">/sim</span>. Point to the screen: <em>"Look at Joint 2 — the shoulder is visibly shuddering in real time, the joint housing has turned glowing red, and our torque telemetry has spiked from 18 Nm to 132 Nm. Fixer.ai calculates 14 hours of RUL remaining, and the AI co-pilot tells the tech to flush with Mobilux EP2 grease and torque flange bolts to 85 Nm."</em>
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 5: MACHINE 2 (M-02: HAAS VF-2 CNC MILL)                                -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 03 (CONT.)</span>
  <h2>Fleet Asset 2: Haas VF-2 CNC Mill (M-02)</h2>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6pt;">
  <div style="font-size: 13pt; font-weight: 800; color: #0f172a;">The Precision CNC Carving Machine</div>
  <span class="pill pill-blue">Location: Line 2 — Precision Machining</span>
</div>

<p>
  <strong>What it is in real life:</strong> A large, fully enclosed computer-numerical-control (CNC) vertical milling center. Inside its steel enclosure, a high-speed spindle spins razor-sharp carbide tools at 10,000 RPM while flooding the chamber with liquid coolant, carving complex engine blocks and aerospace fittings out of solid blocks of aluminum and titanium.
</p>

<div class="grid-2">
  <div class="card">
    <div class="card-title">🔧 Key Physical Components</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Spindle Cartridge:</strong> High-speed rotating assembly holding the CAT-40 toolholder and carbide end mill bit (contains critical angular-contact bearings).</li>
      <li><strong>Enclosure & Windows:</strong> Machine-tool grey steel housing with Haas blue side panels, dual sliding doors, and tinted safety polycarbonate windows.</li>
      <li><strong>Pendant Operator Console:</strong> Swivel boom arm with Haas display, keyboard, rotary MPG handwheel jog dial, and red mushroom emergency stop.</li>
      <li><strong>Worktable & Vise:</strong> Slotted steel table moving on X-Y axes clamping the raw metal billet.</li>
    </ul>
  </div>
  <div class="card">
    <div class="card-title">📊 Sensor Telemetry Meaning</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Spindle Vibration (mm/s²):</strong> Microscopic wobble. Normal = 0.5–1.2 mm/s². Spikes to 4+ mm/s² indicate race pitting or impending bearing seizure.</li>
      <li><strong>Spindle Temp (°C):</strong> Friction fever. High temp indicates severe friction or coolant delivery failure.</li>
      <li><strong>Spindle Speed (RPM):</strong> Real-time rotation speed (typically 6,000–10,000 RPM during cutting).</li>
    </ul>
  </div>
</div>

<div class="screenshot-box">
  <img src="{img_b64['m02']}" class="screenshot-img" alt="M-02 Haas CNC Screenshot">
  <div class="screenshot-caption">
    <span>3D CCTV VIEW: Haas VF-2 CNC Mill (Pendant Console, Sliding Doors, Blue Accents & Chip Tray)</span>
    <span class="pill pill-green">Operational State</span>
  </div>
</div>

<div class="card card-tip" style="margin-top: 6pt;">
  <div class="card-title">💡 How to Demonstrate M-02 on Stage</div>
  <p style="font-size: 8.5pt; margin: 0;">
    Highlight the realism of the digital twin: <em>"Judges, notice the pendant control console with the jog handwheel and red e-stop button, the dual sliding doors with tinted safety windows, and the spinning tool bit inside. When spindle bearing wear occurs, the spindle housing pulses red with high-frequency chatter vibration, preventing catastrophic tool snapping."</em>
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 6: MACHINE 3 (M-03: CONVEYOR & PRESS)                                  -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 03 (CONT.)</span>
  <h2>Fleet Asset 3: Conveyor & Stamping Press (M-03)</h2>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6pt;">
  <div style="font-size: 13pt; font-weight: 800; color: #0f172a;">The Heavy Transfer & Stamping Line</div>
  <span class="pill pill-blue">Location: Bay 5 — Press & Conveyance Station 7</span>
</div>

<p>
  <strong>What it is in real life:</strong> A continuous heavy industrial production line where a motorized rubber conveyor transports cylindrical metal billets under a massive C-frame hydraulic press. The press ram reciprocates up and down with multi-ton force, stamping each part into final shape before conveying it down the assembly line.
</p>

<div class="grid-2">
  <div class="card">
    <div class="card-title">🔧 Key Physical Components</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Drive Motor & Inline Gearbox:</strong> Heavy cast-iron induction motor equipped with 10 radial cooling fins, fan shroud, terminal box, and safety chain guard.</li>
      <li><strong>Hydraulic Press Crown:</strong> Blue structural steel frame with dual chromed tie columns, hydraulic manifold block, and reciprocating chrome piston ram.</li>
      <li><strong>Safety Guarding:</strong> Yellow perforated wire mesh cages protecting operators and optical photo-eye sensor beam at entry.</li>
      <li><strong>Continuous Rubber Belt:</strong> Slotted conveyor bed with side guide rails and crowned steel drive pulleys.</li>
    </ul>
  </div>
  <div class="card">
    <div class="card-title">📊 Sensor Telemetry Meaning</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Motor Current (Amps):</strong> Electrical load tug-of-war. Normal = 12–15 A. Spikes to 25+ A mean mechanical belt jamming, bearing drag, or stator winding breakdown.</li>
      <li><strong>Motor Temperature (°C):</strong> Thermal coil load. Normal = 45–55°C. Excessive heat degrades motor insulation.</li>
      <li><strong>Line Speed (m/min):</strong> Surface velocity of the transfer belt.</li>
    </ul>
  </div>
</div>

<div class="screenshot-box">
  <img src="{img_b64['m03']}" class="screenshot-img" alt="M-03 Conveyor Press Screenshot">
  <div class="screenshot-caption">
    <span>3D CCTV VIEW: Conveyor Transfer & Hydraulic Stamping Press (Moving Billets, Finned Motor & Safety Cage)</span>
    <span class="pill pill-green">Operational State</span>
  </div>
</div>

<div class="card card-tip" style="margin-top: 6pt;">
  <div class="card-title">💡 How to Demonstrate M-03 on Stage</div>
  <p style="font-size: 8.5pt; margin: 0;">
    Show the moving components: <em>"On Station 7, you can see the metal billets actively moving along the belt and the hydraulic ram reciprocating. When an electrical phase imbalance occurs, the motor stator pulses red, current surges on the live telemetry waveform, and the AI flags thermal winding failure before the motor burns out."</em>
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 7: MACHINE 4 (M-04: CALIBRATION CART)                                  -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 03 (CONT.)</span>
  <h2>Fleet Asset 4: Crane MTTS Calibration Cart (M-04)</h2>
</div>

<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6pt;">
  <div style="font-size: 13pt; font-weight: 800; color: #0f172a;">The Mobile Metrology & QA Inspection Bench</div>
  <span class="pill pill-blue">Location: QA Bay — Metrology Testing Station</span>
</div>

<p>
  <strong>What it is in real life:</strong> A specialized mobile testing cart inspired by the Crane MTTS system, utilized by aerospace and automotive Quality Assurance teams. In regulated manufacturing, every torque wrench used to tighten critical bolts (such as aircraft wing spars or engine mounts) must be calibrated against this certified standard. If wrenches drift, bolts can back out in flight!
</p>

<div class="grid-2">
  <div class="card">
    <div class="card-title">🔧 Key Physical Components</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Rotary Torque Transducer:</strong> Certified high-precision measurement cartridge featuring a gold-anodized seal ring, bolt flanges, and keyed drive shaft.</li>
      <li><strong>Mobile Cart with Casters:</strong> 4 dual-wheel heavy-duty locking casters with red brake pedals, tubular push handles, and lower perforated storage shelf.</li>
      <li><strong>3-Drawer Cabinet Stack:</strong> Industrial blue modular drawers with full-width aluminum pull handles holding adapters and calibration weights.</li>
      <li><strong>Articulated Display Arm:</strong> Swing boom holding a digital touchscreen tablet terminal with ruggedized silicone corner bumpers.</li>
    </ul>
  </div>
  <div class="card">
    <div class="card-title">📊 Sensor Telemetry Meaning</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li><strong>Calibration Drift (%):</strong> Precision accuracy error. Normal = ±0.2%. If drift exceeds ±2.0%, the station loses ISO certification and invalidates all calibrated wrenches!</li>
      <li><strong>Transducer Voltage (V):</strong> Electrical output signal from internal strain-gauge bridge circuits.</li>
      <li><strong>Ambient Temperature (°C):</strong> Thermal expansion tracking.</li>
    </ul>
  </div>
</div>

<div class="screenshot-box">
  <img src="{img_b64['m04']}" class="screenshot-img" alt="M-04 Calibration Cart Screenshot">
  <div class="screenshot-caption">
    <span>3D CCTV VIEW: Crane MTTS Mobile Calibration Cart (Caster Wheels, Blue Drawers, Transducer & Tablet)</span>
    <span class="pill pill-green">Operational State</span>
  </div>
</div>

<div class="card card-tip" style="margin-top: 6pt;">
  <div class="card-title">💡 How to Demonstrate M-04 on Stage</div>
  <p style="font-size: 8.5pt; margin: 0;">
    Showcase the metrology aspect: <em>"Judges, Machine 04 is our mobile quality assurance cart. Notice the locking caster wheels, the drawer units, the green laser alignment beam, and the articulated touchscreen tablet. When sensor calibration drifts, the transducer pulses amber, and the green laser beam shifts to red alert, preventing defective tools from reaching production."</em>
  </p>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 8: APP TOUR (DASHBOARD & DETAIL)                                       -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 04</span>
  <h2>Application Tour: Dashboard & Detail Cockpit</h2>
</div>

<p>
  Fixer.ai is built with a cohesive, production-grade user experience. Here is how the primary application views are structured and what features they deliver.
</p>

<h3>1. Fleet Overview Dashboard (<span class="code-inline">/</span>)</h3>
<p>
  The high-level executive and plant manager screen. Summarizes overall fleet health (0–100 score), total financial downtime avoided ($111,000+), Overall Equipment Effectiveness (OEE at 93.8%), and live status cards for all 4 machines with active sensor values and RUL predictions.
</p>

<div class="screenshot-box">
  <img src="{img_b64['dashboard']}" class="screenshot-img-small" alt="Dashboard Overview">
  <div class="screenshot-caption">
    <span>FLEET DASHBOARD: High-level plant health, financial impact, and machine telemetry status cards</span>
    <span class="pill pill-blue">Fleet Overview</span>
  </div>
</div>

<h3>2. Machine Detail & 3D CCTV Operational Cockpit (<span class="code-inline">/machine/:id</span>)</h3>
<p>
  Clicking any machine card opens its dedicated operational cockpit:
</p>
<ul style="font-size: 8.5pt; margin-bottom: 4pt;">
  <li><strong>Interactive 3D CCTV Viewport:</strong> Real-time digital twin featuring REC blinker, camera labels, timestamps, and orbital controls without distracting auto-rotation.</li>
  <li><strong>Live Waveform Telemetry:</strong> Real-time Recharts line graphs streaming continuous sensor ticks via WebSockets at 1 Hz with nominal threshold bands.</li>
  <li><strong>Multimodal AI Advisory Panel:</strong> Pre-seeded incident history, image upload, audio voice player, and root-cause repair guidance grounded in OEM documentation.</li>
</ul>

<div class="screenshot-box">
  <img src="{img_b64['detail_full']}" class="screenshot-img-small" alt="Machine Detail Full">
  <div class="screenshot-caption">
    <span>OPERATIONAL COCKPIT: Real-time 3D CCTV digital twin, live telemetry waveforms & AI advisory assistant</span>
    <span class="pill pill-blue">Machine Detail Cockpit</span>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 9: SIMULATION CONTROL ROOM                                             -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 04 (CONT.)</span>
  <h2>The Secret Weapon: Simulation Control Room</h2>
</div>

<h3>3. Standalone Simulation Command Center (<span class="code-inline">/sim</span>)</h3>
<div class="card card-tip">
  <div class="card-title">🎯 Why This Page Wins Hackathons</div>
  <p style="margin: 0; font-size: 8.5pt;">
    Most hackathon demos are static slides or canned mockups because demonstrating real mechanical breakdowns on stage is nearly impossible. <strong>Fixer.ai solves this with a dedicated, hidden simulation control room accessible at <span class="code-inline">/sim</span>.</strong> You keep this open in a second browser tab. With a single click on stage, you inject live physical degradation scenarios into the backend simulator and watch the entire platform react in real time!
  </p>
</div>

<div class="screenshot-box">
  <img src="{img_b64['sim']}" class="screenshot-img" alt="Simulation Room">
  <div class="screenshot-caption">
    <span>SIMULATION CONTROL ROOM: 1-Click physical fault injector & repair restore panel</span>
    <span class="pill pill-amber">Demo Command Center</span>
  </div>
</div>

<div class="grid-2">
  <div class="card card-pain">
    <div class="card-title">🔴 Click "Inject Fault"</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li>Simulates physical failure mode (e.g. grease dry-out).</li>
      <li>Sensor values jump past safety bounds immediately.</li>
      <li>3D CCTV model pulses red and vibrates.</li>
      <li>CCTV status tag flips to <span class="pill pill-red">FAULT DETECTED</span>.</li>
      <li>Health score drops from 100 to 32.</li>
      <li>Remaining Useful Life (RUL) falls to 14 hours.</li>
    </ul>
  </div>
  <div class="card card-tip">
    <div class="card-title">🟢 Click "Repair & Restore"</div>
    <ul style="font-size: 8.5pt; padding-left: 12pt; margin: 4pt 0;">
      <li>Simulates physical technician maintenance action.</li>
      <li>3D model glows with a cyan healing pulse.</li>
      <li>Sensor values normalize instantly to baseline.</li>
      <li>CCTV status resets to <span class="pill pill-green">OPERATIONAL</span>.</li>
      <li>Incident ticket is auto-resolved.</li>
      <li>Resolution procedure is saved into AI memory.</li>
    </ul>
  </div>
</div>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 10: THE HACKATHON PITCH PLAYBOOK                                       -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 05</span>
  <h2>The Hackathon Pitch Playbook (3-Minute Script)</h2>
</div>

<p>
  Practice this exact presentation script with your teammates. Split roles cleanly so each speaker demonstrates confidence, empathy, and technical authority.
</p>

<table>
  <thead>
    <tr>
      <th style="width: 15%;">Time</th>
      <th style="width: 25%;">Speaker & Action</th>
      <th style="width: 60%;">Word-for-Word Pitch Script</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>0:00 - 0:30</strong></td>
      <td><strong>Speaker 1 (The Hook)</strong><br>Show Slide / Cover Page</td>
      <td>
        <em>"Judges, an automotive manufacturing plant loses $22,000 every single minute an assembly line stops. Today, factory maintenance is broken: technicians either wait for multi-million dollar machines to catch fire, or they run around with 800-page paper binders trying to diagnose mysterious squeaks at 2 AM. We built <strong>Fixer.ai</strong> — an industrial prognostic digital twin that gives technicians a predictive sixth sense."</em>
      </td>
    </tr>
    <tr>
      <td><strong>0:30 - 1:15</strong></td>
      <td><strong>Speaker 2 (Live Fleet)</strong><br>Screen share <span class="code-inline">localhost:5173/</span>, then click <strong>M-01</strong></td>
      <td>
        <em>"Here is our live production floor. We are streaming real-time IoT telemetry from 4 major industrial assets. Let's look at Machine 01, our FANUC robotic welding cell. You are looking at a live 3D digital twin CCTV feed. You can see the articulating arm, the welding torch, and nominal green status. Our stochastic prognostics engine calculates a 100% health score and 30+ days of Remaining Useful Life."</em>
      </td>
    </tr>
    <tr>
      <td><strong>1:15 - 2:00</strong></td>
      <td><strong>Speaker 2 + Speaker 3</strong><br>Speaker 3 clicks <strong>Inject Fault</strong> on <span class="code-inline">/sim</span> in background</td>
      <td>
        <em>"Now, let's inject a real-world failure mode: lubricant breakdown in the J2 shoulder reducer. Watch the screen!
        <br><br>
        Immediately, the 3D model visually shudders and pulses red where it hurts. The andon beacon flashes red, and torque telemetry spikes past our threshold. But notice: our prognostics engine doesn't just panic — it computes an RUL countdown: <strong>14.2 hours remaining before catastrophic freeze</strong>."</em>
      </td>
    </tr>
    <tr>
      <td><strong>2:00 - 2:40</strong></td>
      <td><strong>Speaker 3 (AI Advisory)</strong><br>Click defect ticket in chat, send question</td>
      <td>
        <em>"Dave the technician doesn't search through paper manuals. He opens our Multimodal AI Assistant. Grounded in manufacturer OEM manuals and shop-floor memory, Fixer.ai identifies the root cause in 2 seconds: grease degradation in the harmonic drive reducer. It gives the exact 3-step procedure: flush with Mobilux EP2 grease and torque flange bolts to 85 Nm."</em>
      </td>
    </tr>
    <tr>
      <td><strong>2:40 - 3:00</strong></td>
      <td><strong>Speaker 1 (The Close)</strong><br>Click <strong>Repair & Restore</strong> on <span class="code-inline">/sim</span></td>
      <td>
        <em>"Dave executes the fix. The 3D model glows cyan, sensors immediately normalize to green, and the resolved work order is embedded into continual memory so the whole factory gets smarter. Fixer.ai turns catastrophic downtime into scheduled 15-minute maintenance. Thank you!"</em>
      </td>
    </tr>
  </tbody>
</table>

<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<!-- PAGE 11: JUDGE Q&A & TEAM CHECKLIST                                         -->
<!-- ═══════════════════════════════════════════════════════════════════════════ -->
<div class="page-break"></div>

<div class="chapter-header">
  <span class="chapter-num">CHAPTER 06</span>
  <h2>Bulletproof Judge Q&A & Hackathon Checklist</h2>
</div>

<p>
  Hackathon judges will test your depth. Here are the top questions they will ask, along with the exact responses that will win top marks:
</p>

<div class="card card-hack">
  <div class="card-title">❓ Q1: "Is this just a simulation or can it connect to real physical machines?"</div>
  <p style="font-size: 8.5pt; margin: 0;">
    <strong>Winning Answer:</strong> <em>"Our architecture is 100% production-ready. The backend communicates over standard WebSockets and REST APIs using standard JSON sensor payloads. In a live factory, our simulation layer is simply replaced by an industrial MQTT broker or OPC-UA server connected directly to PLC sensor networks (like Siemens S7 or Allen-Bradley). The entire 3D digital twin, prognostics engine, and AI advisor run completely untouched!"</em>
  </p>
</div>

<div class="card card-hack">
  <div class="card-title">❓ Q2: "Why build a 3D digital twin? Isn't a 2D dashboard enough?"</div>
  <p style="font-size: 8.5pt; margin: 0;">
    <strong>Winning Answer:</strong> <em>"Human factors research in industrial environments proves that under stress, technicians experience cognitive tunnel vision. A 2D table of 40 numbers requires high mental processing. But an interactive 3D digital twin leverages spatial human intuition: you immediately see WHICH joint is overheating and HOW it is vibrating in space. It reduces mean-time-to-identification (MTTI) by over 65%."</em>
  </p>
</div>

<div class="card card-hack">
  <div class="card-title">❓ Q3: "What if your AI hallucinated and gave dangerous repair advice?"</div>
  <p style="font-size: 8.5pt; margin: 0;">
    <strong>Winning Answer:</strong> <em>"Safety is critical in manufacturing. That's why we built a <strong>Two-Tier Constrained RAG architecture</strong>. Tier 1 only retrieves from verified OEM manufacturer manuals with strict semantic similarity thresholds. If the manual says 85 Nm, the model is strictly bound to output 85 Nm. Tier 2 retrieves historical shop-floor resolution notes. The AI is strictly forbidden from generating speculative mechanical procedures outside ingested technical documentation."</em>
  </p>
</div>

<div class="card card-hack">
  <div class="card-title">❓ Q4: "What is your business model and who pays for this?"</div>
  <p style="font-size: 8.5pt; margin: 0;">
    <strong>Winning Answer:</strong> <em>"We operate a B2B SaaS model tiered by monitored asset count ($250 per critical machine per month). For a medium tier plant with 40 machines ($10,000/month), avoiding just ONE hour of downtime ($22,000 saved) pays for the entire software subscription for more than two months. The ROI is demonstrated in days."</em>
  </p>
</div>

<div class="card card-tip" style="margin-top: 10pt;">
  <div class="card-title">✅ Hackathon Checklist for the Team</div>
  <ul style="font-size: 8.5pt; padding-left: 14pt; margin: 4pt 0;">
    <li>Ensure backend (<span class="code-inline">localhost:8000</span>) and frontend (<span class="code-inline">localhost:5173</span>) are running 10 minutes before presenting.</li>
    <li>Keep two browser windows open side-by-side: Tab 1 (<span class="code-inline">http://localhost:5173/machine/M-01</span>) and Tab 2 (<span class="code-inline">http://localhost:5173/sim</span>).</li>
    <li>Do NOT touch the mouse while another teammate is speaking to keep the camera view stable.</li>
    <li>Smile, speak with passion, and remember: <strong>You are solving a multi-billion dollar problem with empathy!</strong></li>
  </ul>
</div>

</body>
</html>
"""

def generate_pdf():
    print("Writing HTML content to", HTML_OUTPUT)
    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print("HTML written successfully.")

    print("Rendering PDF via Google Chrome Headless...")
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={PDF_OUTPUT}",
        HTML_OUTPUT,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and os.path.exists(PDF_OUTPUT):
        size = os.path.getsize(PDF_OUTPUT)
        print(f"SUCCESS: Generated PDF at {PDF_OUTPUT} ({size:,} bytes)")
    else:
        print("ERROR rendering PDF:")
        print("Stdout:", res.stdout)
        print("Stderr:", res.stderr)

if __name__ == "__main__":
    generate_pdf()
