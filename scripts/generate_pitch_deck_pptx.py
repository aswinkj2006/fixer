"""
Fixer.ai HackfiniX 2026 Finals Pitch Deck Generator
Creates a professional, 16:9 widescreen PowerPoint presentation (.pptx)
Grounded in the HackfiniX 2026 Rulebook, Plain-English Workflow, and Indian Rupee (INR) Metrics.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# Color Palette (Dark Industrial Modern)
BG_COLOR = RGBColor(10, 15, 29)         # #0a0f1d
CARD_BG = RGBColor(19, 28, 49)          # #131c31
CARD_BORDER = RGBColor(37, 51, 80)      # #253350
TEXT_WHITE = RGBColor(248, 250, 252)    # #f8fafc
TEXT_MUTED = RGBColor(148, 163, 184)    # #94a3b8
TEXT_BODY = RGBColor(203, 213, 225)     # #cbd5e1

CYAN = RGBColor(14, 165, 233)           # #0ea5e9
CYAN_LIGHT = RGBColor(56, 189, 248)     # #38bdf8
GREEN = RGBColor(34, 197, 94)           # #22c55e
AMBER = RGBColor(245, 158, 11)          # #f59e0b
ROSE = RGBColor(244, 63, 94)            # #f43f5e
PURPLE = RGBColor(168, 85, 247)         # #a855f7
GOLD = RGBColor(251, 191, 36)           # #fbbf24

ARTIFACT_DIR = r"C:\Users\Aswin K J\.gemini\antigravity-ide\brain\6506f979-1e88-4d14-b684-e8617d799125"

def get_image_path(filename):
    p = os.path.join(ARTIFACT_DIR, filename)
    return p if os.path.exists(p) else None

def create_base_slide(prs, category_tag, slide_title, subtitle=None):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    
    # Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.color.rgb = BG_COLOR
    
    # Category Tag / Badge
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8), Inches(0.35))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = category_tag.upper()
    p_tag.font.size = Pt(10)
    p_tag.font.bold = True
    p_tag.font.color.rgb = CYAN
    
    # Slide Title
    title_top = Inches(0.7)
    title_box = slide.shapes.add_textbox(Inches(0.8), title_top, Inches(11.7), Inches(0.6))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = slide_title
    p_title.font.size = Pt(24)
    p_title.font.bold = True
    p_title.font.color.rgb = TEXT_WHITE
    
    if subtitle:
        p_sub = tf_title.add_paragraph()
        p_sub.text = subtitle
        p_sub.font.size = Pt(13)
        p_sub.font.color.rgb = TEXT_MUTED
        
    return slide

def add_card(slide, left, top, width, height, bg_color=CARD_BG, border_color=CARD_BORDER):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.2)
    return card

def add_header_text(slide, left, top, width, height, title, body_bullets, accent_color=CYAN):
    tx_box = slide.shapes.add_textbox(left, top, width, height)
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.2)
    tf.margin_top = tf.margin_bottom = Inches(0.15)
    
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size = Pt(15)
    p0.font.bold = True
    p0.font.color.rgb = accent_color
    p0.space_after = Pt(8)
    
    for item in body_bullets:
        p = tf.add_paragraph()
        p.text = "• " + item
        p.font.size = Pt(11.5)
        p.font.color.rgb = TEXT_BODY
        p.space_after = Pt(5)

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # -------------------------------------------------------------
    # SLIDE 1: COVER SLIDE
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = BG_COLOR
    bg1.line.color.rgb = BG_COLOR
    
    # Header badge
    badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(4.8), Inches(0.4))
    badge.fill.solid()
    badge.fill.fore_color.rgb = CARD_BG
    badge.line.color.rgb = CYAN
    badge.text_frame.text = "🏆 HACKFINIX 2026 FINALS | CITNC BENGALURU"
    badge.text_frame.paragraphs[0].font.size = Pt(11)
    badge.text_frame.paragraphs[0].font.bold = True
    badge.text_frame.paragraphs[0].font.color.rgb = CYAN_LIGHT
    
    # Big Title
    tb_title = slide1.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.5), Inches(2.2))
    tf = tb_title.text_frame
    tf.word_wrap = True
    p1 = tf.paragraphs[0]
    p1.text = "FIXER.AI"
    p1.font.size = Pt(54)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    
    p2 = tf.add_paragraph()
    p2.text = "The Continuously Learning RAG Technician for Industrial Machines"
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = CYAN_LIGHT
    p2.space_before = Pt(8)
    
    p3 = tf.add_paragraph()
    p3.text = "A dedicated 'digital doctor' with isolated per-machine memory — transforming reactive emergency repairs into proactive, human-in-the-loop intelligence."
    p3.font.size = Pt(14)
    p3.font.color.rgb = TEXT_MUTED
    p3.space_before = Pt(10)
    
    # 4 Key Metric Cards
    metrics = [
        ("₹18,00,000", "LOST PER MINUTE OF DOWNTIME", ROSE),
        ("Per-Machine Memory", "ISOLATED RAG BRAIN PER ASSET", PURPLE),
        ("14+ Hours Advance", "REMAINING USEFUL LIFE (RUL)", AMBER),
        ("Multimodal RAG", "VOICE + PHOTOS + OEM MANUALS", GREEN)
    ]
    card_w = Inches(2.7)
    card_h = Inches(1.8)
    gap = Inches(0.3)
    start_x = Inches(0.8)
    y_pos = Inches(4.2)
    
    for i, (m_val, m_lbl, m_col) in enumerate(metrics):
        x = start_x + i * (card_w + gap)
        add_card(slide1, x, y_pos, card_w, card_h, CARD_BG, CARD_BORDER)
        tx = slide1.shapes.add_textbox(x, y_pos, card_w, card_h)
        tx_tf = tx.text_frame
        tx_tf.word_wrap = True
        tx_tf.margin_left = tx_tf.margin_right = Inches(0.2)
        tx_tf.margin_top = Inches(0.3)
        
        p_v = tx_tf.paragraphs[0]
        p_v.text = m_val
        p_v.font.size = Pt(22)
        p_v.font.bold = True
        p_v.font.color.rgb = m_col
        
        p_l = tx_tf.add_paragraph()
        p_l.text = m_lbl
        p_l.font.size = Pt(9.5)
        p_l.font.bold = True
        p_l.font.color.rgb = TEXT_MUTED
        p_l.space_before = Pt(8)
        
    # Footer info
    ft_box = slide1.shapes.add_textbox(Inches(0.8), Inches(6.4), Inches(11.7), Inches(0.5))
    ft_tf = ft_box.text_frame
    p_ft = ft_tf.paragraphs[0]
    p_ft.text = "Target Tracks: Track 01 (Smart Manufacturing & Industry 5.0)  |  Track 02 (Human–AI Collaboration)  |  Eligible for Best UI/UX (₹10,000)"
    p_ft.font.size = Pt(11)
    p_ft.font.color.rgb = TEXT_MUTED
    
    # -------------------------------------------------------------
    # SLIDE 2: THE REAL-WORLD PAIN POINT
    # -------------------------------------------------------------
    slide2 = create_base_slide(prs, "Chapter 01 // The Problem", "The Factory Floor Nightmare: Unplanned Downtime Costs ₹18 Lakhs / Minute", "Why modern manufacturing lines are bleeding capital under 2 AM panic")
    
    # Left Box: Dave's Story (Human Empathy)
    add_card(slide2, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, ROSE)
    tx_story = slide2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1))
    st_tf = tx_story.text_frame
    st_tf.word_wrap = True
    st_tf.margin_left = st_tf.margin_right = Inches(0.3)
    st_tf.margin_top = Inches(0.3)
    
    p = st_tf.paragraphs[0]
    p.text = "🚨 The 2:15 AM Crisis (Dave's Story)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = ROSE
    p.space_after = Pt(10)
    
    story_paras = [
        "Dave is the lead maintenance technician at a Tier-1 automotive plant in Bengaluru.",
        "At 2:15 AM, Robotic Welding Cell 3 violently locks up. The entire assembly line grinds to a halt.",
        "Every single minute the line sits frozen costs the company ₹18,00,000 (₹18 Lakhs/min = ₹1.08 Crore/hour).",
        "Dave rushes onto the dark factory floor with a flashlight and an 800-page grease-stained paper manual binder. Sirens are blaring, plant managers are panicking.",
        "Dave is forced to play a guessing game: Is it Joint 2? Did a harmonic gear strip? Is the sensor fried? Which bearing is screaming?"
    ]
    for sp in story_paras:
        p = st_tf.add_paragraph()
        p.text = sp
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_BODY
        p.space_after = Pt(8)
        
    # Right Box: Three Cost Factors
    r_w = Inches(5.8)
    r_h = Inches(1.5)
    r_x = Inches(6.7)
    
    factors = [
        ("₹1.08 Crore Lost Every Hour", "Automotive, aerospace, and precision robotics operate on razor-thin JIT (Just-In-Time) schedules. A 3-hour freeze wipes out weekly profit margins.", ROSE),
        ("70% Time Wasted on Lookup (MTTR)", "Technicians waste over an hour flipping through PDF manuals, searching past ticket archives, and guessing machine quirks before turning a single wrench.", AMBER),
        ("Tribal Knowledge Walks Out the Door", "When senior technicians retire or change shifts, their intimate knowledge of how each specific machine 'behaves' is permanently lost.", PURPLE)
    ]
    
    for i, (f_title, f_desc, f_col) in enumerate(factors):
        f_y = Inches(1.6) + i * (r_h + Inches(0.3))
        add_card(slide2, r_x, f_y, r_w, r_h, CARD_BG, CARD_BORDER)
        add_header_text(slide2, r_x, f_y, r_w, r_h, f_title, [f_desc], f_col)
        
    # -------------------------------------------------------------
    # SLIDE 3: WHY TRADITIONAL SOLUTIONS FAIL
    # -------------------------------------------------------------
    slide3 = create_base_slide(prs, "Chapter 02 // Competitive Comparison", "Why Existing Maintenance Strategies Fail the Modern Factory", "The fatal flaws of reactive, calendar-based, and generic anomaly-detection models")
    
    col_w = Inches(3.7)
    col_h = Inches(5.1)
    col_gap = Inches(0.3)
    start_x = Inches(0.8)
    y_pos = Inches(1.6)
    
    approaches = [
        ("❌ Run-To-Failure\n(Pure Reactive)", ROSE, [
            "Wait until machines scream, smoke, or violently seize up.",
            "Broken metal fragments chew through adjacent gears and tooling.",
            "Repair costs surge 10x higher due to collateral damage.",
            "Production halts for days while waiting for replacement parts.",
            "Extremely dangerous for nearby operators on the shop floor."
        ]),
        ("❌ Calendar-Based\n(Standard Preventative)", AMBER, [
            "Replace expensive bearings & seals every 6 months 'just in case'.",
            "70% of replaced components are completely healthy when scrapped!",
            "Wastes ₹40,00,000 to ₹50,00,000 annually per line in premature scrap.",
            "Does NOT prevent sudden catastrophic failure between schedules.",
            "Ignores actual operating wear, loads, and thermal stress."
        ]),
        ("❌ Generic ML / Black-Box\n(Predictive 1.0)", CYAN, [
            "Trained on generic sensor datasets with no per-machine memory.",
            "Produces raw statistical curves that overwhelm techs (alert fatigue).",
            "Zero actionable repair guidance: says 'anomaly' but cannot say HOW to fix it.",
            "Must be rebuilt and retrained machine-by-machine from scratch.",
            "No human-in-the-loop verification or auditable compliance trail."
        ])
    ]
    
    for i, (title, color, points) in enumerate(approaches):
        x = start_x + i * (col_w + col_gap)
        add_card(slide3, x, y_pos, col_w, col_h, CARD_BG, CARD_BORDER)
        add_header_text(slide3, x, y_pos, col_w, col_h, title, points, color)
        
    # -------------------------------------------------------------
    # SLIDE 4: THE CORE IDEA - PERMANENT DIGITAL TECHNICIAN
    # -------------------------------------------------------------
    slide4 = create_base_slide(prs, "Chapter 03 // The Breakthrough", "The Core Innovation: A 'Permanent Digital Technician' for Every Machine", "Not a generic document chatbot — an isolated, growing brain for every individual asset")
    
    # Left Card: The Concept
    add_card(slide4, Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.1), CARD_BG, PURPLE)
    tx_idea = slide4.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(5.8), Inches(5.1))
    tf_idea = tx_idea.text_frame
    tf_idea.word_wrap = True
    tf_idea.margin_left = tf_idea.margin_right = Inches(0.3)
    tf_idea.margin_top = Inches(0.3)
    
    p = tf_idea.paragraphs[0]
    p.text = "🧠 The Dedicated 'Digital Doctor' Concept"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = PURPLE
    p.space_after = Pt(12)
    
    pts = [
        "In a real factory, the best asset is a veteran master technician who has worked with a specific machine for 10 years. They know its subtle vibrations, sound pitch, and historical quirks.",
        "Fixer.ai builds a digital replica of that master technician for EVERY machine in the plant.",
        "Crucial Differentiator: Isolated Per-Machine Memory. Machine 01 (FANUC Welder) has its own private knowledge base separate from Machine 02 (Haas CNC Mill).",
        "It remembers every repair, every oil flush, every sensor anomaly, and every technician note from day one.",
        "It never retires, never forgets, and gets smarter every single day through reinforcement learning."
    ]
    for pt in pts:
        p = tf_idea.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_BODY
        p.space_after = Pt(8)
        
    # Right Column: 3 Core Pillars
    r_w = Inches(5.6)
    r_h = Inches(1.5)
    r_x = Inches(6.9)
    
    pillars = [
        ("1. Isolated Knowledge Partitions", "Each machine maintains an autonomous vector partition containing its specific operating envelope, wear history, and manuals. No cross-contamination of machine quirks.", CYAN),
        ("2. Real-Time CCTV + Sensor Fusion", "Combines high-frequency telemetry (vibration, torque, motor current, spindle heat) with 3D digital twin CCTV visualization for spatial human intuition.", GREEN),
        ("3. Continuous Reinforcement Loop", "Every time a technician confirms or corrects a repair suggestion, that outcome serves as an RLHF-style reward or error signal to sharpen future accuracy.", GOLD)
    ]
    for i, (p_title, p_desc, p_col) in enumerate(pillars):
        p_y = Inches(1.6) + i * (r_h + Inches(0.3))
        add_card(slide4, r_x, p_y, r_w, r_h, CARD_BG, CARD_BORDER)
        add_header_text(slide4, r_x, p_y, r_w, r_h, p_title, [p_desc], p_col)

    # -------------------------------------------------------------
    # SLIDE 5: ARCHITECTURE - RAG AS BRAIN, LLM AS BODY
    # -------------------------------------------------------------
    slide5 = create_base_slide(prs, "Chapter 04 // System Architecture", "Architecture: RAG as the Brain, LLM as the Body", "Decoupling persistent per-machine memory from a shared high-performance reasoning engine")
    
    # Left: RAG Brain
    add_card(slide5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(4.2), CARD_BG, PURPLE)
    add_header_text(slide5, Inches(0.8), Inches(1.6), Inches(5.6), Inches(4.2),
        "🧠 RAG: The Brain (Isolated per Machine)", [
            "Partitions: Machine #1, Machine #2, Machine #N have dedicated ChromaDB vector collections.",
            "Stores: Ingested OEM manuals, electrical schematics, full repair logs, CCTV visual logs, and sensor anomaly snapshots.",
            "Dynamic Growth: Continually incorporates technician feedback notes and verified work orders.",
            "Zero Cross-Bleed: Prevents a CNC mill's spindle issue from contaminating a welding robot's joint reducer diagnosis."
        ], PURPLE)
        
    # Right: LLM Body
    add_card(slide5, Inches(6.9), Inches(1.6), Inches(5.6), Inches(4.2), CARD_BG, CYAN)
    add_header_text(slide5, Inches(6.9), Inches(1.6), Inches(5.6), Inches(4.2),
        "⚡ LLM: The Body (Shared Reasoning Engine)", [
            "Single High-Performance Engine: Powers overseer chat, multimodal diagnostics, and automated alerts.",
            "Zero Costly Retraining: The base LLM remains frozen; only the machine-specific RAG context is swapped dynamically.",
            "Two-Tier Constrained Output: Strictly bound to verified OEM engineering manual tolerances (e.g. '85 Nm torque wrench').",
            "Future-Ready: Supports lightweight LoRA / adapter tuning per machine type without risking catastrophic model drift."
        ], CYAN)
        
    # Bottom Banner: Docker & FDE Delivery
    add_card(slide5, Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.9), CARD_BG, GREEN)
    tx_bot = slide5.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.9))
    tf_b = tx_bot.text_frame
    tf_b.margin_left = Inches(0.3)
    tf_b.margin_top = Inches(0.15)
    p_b = tf_b.paragraphs[0]
    p_b.text = "📦 Enterprise Delivery: Packaged as a local on-prem Docker container. Set up on factory edge servers by a Field Deployment Engineer (FDE) with full offline security compliance."
    p_b.font.size = Pt(12)
    p_b.font.bold = True
    p_b.font.color.rgb = GREEN

    # -------------------------------------------------------------
    # SLIDE 6: THE DUAL WORKFLOW (SIDE A & SIDE B)
    # -------------------------------------------------------------
    slide6 = create_base_slide(prs, "Chapter 05 // Complete Workflow", "The Dual Workflow: Overseer Operations & Machine Learning Loop", "A closed-loop system connecting high-level plant oversight with shop-floor technician execution")
    
    # Side A Box
    add_card(slide6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, CYAN)
    add_header_text(slide6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1),
        "🖥️ SIDE A: Overseer Fleet Intelligence", [
            "1. Fleet Health Dashboard: Real-time 0–100 health scores, avoided downtime value in ₹, and Overall Equipment Effectiveness (OEE).",
            "2. Conversational Overseer AI: Technical plant managers ask: 'Which machine has degraded most this week?'",
            "3. Dynamic On-Demand Analytics: Generates live sensor comparison waveforms and degradation trend charts dynamically.",
            "4. Cross-Fleet Pattern Detection: Identifies systemic component flaws across identical machine models."
        ], CYAN)
        
    # Side B Box
    add_card(slide6, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, GREEN)
    add_header_text(slide6, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1),
        "⚙️ SIDE B: Shop-Floor Diagnosis & Learning", [
            "1. Real-Time Telemetry & CCTV Twin: IoT streams at 1 Hz; 3D digital twin shudders and pulses red at the exact failing joint.",
            "2. Multimodal Diagnosis: Fuses sensor spikes + CCTV visual state + OEM manual schematics + past repair memory.",
            "3. Tiered Alert & Work Order: Direct instructions to technician: 'Joint 2 dry. Flush with Mobilux EP2 grease; torque to 85 Nm.'",
            "4. Closed Feedback Loop: Tech completes repair -> confirms in app -> RAG updates weights with reward signal (+1)."
        ], GREEN)

    # -------------------------------------------------------------
    # SLIDE 7: MULTIMODAL DIAGNOSIS & HUMAN EMPATHY
    # -------------------------------------------------------------
    slide7 = create_base_slide(prs, "Chapter 06 // Human-AI Collaboration", "Multimodal Diagnosis: Designed for Grease-Covered Work Gloves", "Solving the human friction point on noisy, fast-paced factory floors")
    
    card_w = Inches(3.7)
    card_h = Inches(5.1)
    
    features = [
        ("🎙️ Voice & Photo Inputs", CYAN, [
            "Technicians have heavy, grease-stained work gloves and cannot type on laptops.",
            "Technician speaks naturally: 'Joint 2 has a high-pitched grinding sound during weld cycle.'",
            "Snaps a phone photo of a worn seal or oil leak.",
            "System transcribes audio and extracts visual wear markers in real time."
        ]),
        ("📐 Two-Tier Constrained RAG", PURPLE, [
            "Tier 1: OEM Manuals (Strict similarity threshold). Extracts exact factory specs: 'Use Mobilux EP2 grease, 85 Nm torque wrench.'",
            "Tier 2: Historical Shop-Floor Notes. Retrieves past repair tricks from Dave and veteran technicians.",
            "Zero Hallucination: The LLM is strictly prohibited from inventing speculative mechanical procedures."
        ]),
        ("🚨 Alert Severity Tiering", AMBER, [
            "Eliminates Alert Fatigue: Factory techs ignore systems that scream at every tiny anomaly.",
            "Tier 1 (Notice): Microscopic wear drift noted in log; zero interruption.",
            "Tier 2 (Warning): Service needed during next planned shift break (RUL > 12h).",
            "Tier 3 (Critical Emergency): Immediate line-stop recommendation to prevent ₹18L/min breakdown."
        ])
    ]
    for i, (title, color, points) in enumerate(features):
        x = Inches(0.8) + i * (card_w + Inches(0.3))
        add_card(slide7, x, Inches(1.6), card_w, card_h, CARD_BG, CARD_BORDER)
        add_header_text(slide7, x, Inches(1.6), card_w, card_h, title, points, color)

    # -------------------------------------------------------------
    # SLIDE 8: CONTINUOUS LEARNING - THE GROWING BRAIN
    # -------------------------------------------------------------
    slide8 = create_base_slide(prs, "Chapter 07 // Machine Intelligence", "The Continuous Learning Loop: A Self-Improving Brain", "How every physical maintenance interaction makes the system smarter over time")
    
    add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, PURPLE)
    add_header_text(slide8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1),
        "🔄 The Reinforcement Feedback Mechanism", [
            "Step 1: Failure Anomaly Detected. Telemetry trips thresholds; RAG retrieves root cause candidate.",
            "Step 2: Technician Action. Dave opens the machine, verifies the physical component, and performs repair.",
            "Step 3A: Confirmation (Reward Signal +1). Tech marks 'Fix Verified'. The vector embedding weight for this retrieval pathway increases. RUL calibration tightens.",
            "Step 3B: Correction (Error Signal -1). Tech notes: 'It wasn't grease dry-out, it was a loose flange bolt.' RAG embeds the correction with high priority for that specific machine.",
            "Step 4: Continuous Evolution. Over 6 months, the RAG transforms into an infallible expert on that machine's exact quirks."
        ], PURPLE)
        
    add_card(slide8, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, CYAN)
    add_header_text(slide8, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1),
        "🌱 Onboarding & Bootstrap Phase (Cold-Start)", [
            "The Rookie Technician Analogy: Even a top human mechanic needs a few weeks to learn a new machine's sounds.",
            "Transparent Confidence Indicator: The UI displays 'Bootstrapping Mode: 65% Confidence' during initial calibration.",
            "Ingestion Phase: Auto-ingests PDF technical manuals, electrical schematics, and the first 48 hours of baseline sensor data.",
            "Context-Aware Storage Pruning: Factory edge servers have limited storage. Raw 1 kHz sensor streams are compressed into feature vectors and statistical trends, preserving compliance audit logs while deleting raw noise."
        ], CYAN)

    # -------------------------------------------------------------
    # SLIDE 9: EXPLAINABILITY & REGULATED INDUSTRIES
    # -------------------------------------------------------------
    slide9 = create_base_slide(prs, "Chapter 08 // Enterprise Ready", "Explainability & Regulated Industry Compliance", "Built specifically for aerospace, automotive, precision robotics, and defense manufacturing")
    
    col_w = Inches(3.7)
    col_h = Inches(5.1)
    
    reg_cards = [
        ("📋 100% Auditable Reasoning", CYAN, [
            "Regulated sectors (Aerospace, ISO 9001, AS9100) legally cannot act on black-box AI outputs.",
            "Every Fixer.ai diagnosis includes clickable citations to the exact OEM manual paragraph and page number.",
            "Displays the exact sensor waveform window that triggered the anomaly diagnosis.",
            "Full digital paper trail ready for external quality audits."
        ]),
        ("🛡️ Human-in-the-Loop Safety", GREEN, [
            "Fixer.ai advises, guides, and calculates — but NEVER takes autonomous physical control of factory actuators.",
            "A human technician must review and authorize any maintenance work order.",
            "Safety interlocks remain under physical PLC and E-stop relay control.",
            "Prevents unauthorized machine modifications."
        ]),
        ("💾 Context-Aware Retention", AMBER, [
            "Aerospace standards require 5-to-10 year audit records of maintenance actions.",
            "Fixer.ai stores lightweight incident tokens, diagnosis logs, and technician feedback forever.",
            "Raw high-frequency telemetry is pruned intelligently after 30 days of nominal operation.",
            "Guarantees compliance without blowing edge server disk limits."
        ])
    ]
    for i, (title, color, points) in enumerate(reg_cards):
        x = Inches(0.8) + i * (col_w + Inches(0.3))
        add_card(slide9, x, Inches(1.6), col_w, col_h, CARD_BG, CARD_BORDER)
        add_header_text(slide9, x, Inches(1.6), col_w, col_h, title, points, color)

    # -------------------------------------------------------------
    # SLIDE 10: PRODUCT SHOWCASE & WORKING PROTOTYPE
    # -------------------------------------------------------------
    slide10 = create_base_slide(prs, "Chapter 09 // Live Product", "Live Working Prototype & UI Showcase", "A production-grade React + Three.js digital twin operational cockpit")
    
    # We will embed 2 UI images
    img1 = get_image_path("dashboard_overview_1790144001646.png")
    img2 = get_image_path("m01_tuned_1790089080096.png")
    
    card1_w = Inches(5.6)
    card1_h = Inches(4.2)
    add_card(slide10, Inches(0.8), Inches(1.6), card1_w, card1_h, CARD_BG, CARD_BORDER)
    if img1:
        slide10.shapes.add_picture(img1, Inches(0.9), Inches(1.7), Inches(5.4), Inches(3.2))
    tx1 = slide10.shapes.add_textbox(Inches(0.9), Inches(5.0), Inches(5.4), Inches(0.7))
    tx1.text_frame.word_wrap = True
    p = tx1.text_frame.paragraphs[0]
    p.text = "🖥️ Fleet Overview Dashboard: Overall plant health, financial downtime avoided, OEE metrics, and 4 connected machine asset cards."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY
    
    add_card(slide10, Inches(6.9), Inches(1.6), card1_w, card1_h, CARD_BG, CARD_BORDER)
    if img2:
        slide10.shapes.add_picture(img2, Inches(7.0), Inches(1.7), Inches(5.4), Inches(3.2))
    tx2 = slide10.shapes.add_textbox(Inches(7.0), Inches(5.0), Inches(5.4), Inches(0.7))
    tx2.text_frame.word_wrap = True
    p = tx2.text_frame.paragraphs[0]
    p.text = "🎥 3D CCTV Digital Twin Cockpit: Real-time spatial twin with live telemetry waveforms, shudder simulation, and multimodal AI assistant."
    p.font.size = Pt(11)
    p.font.color.rgb = TEXT_BODY
    
    # Bottom Demo note
    add_card(slide10, Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.9), CARD_BG, GOLD)
    tx_demo = slide10.shapes.add_textbox(Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.9))
    tx_demo.text_frame.margin_left = Inches(0.3)
    tx_demo.text_frame.margin_top = Inches(0.15)
    p_d = tx_demo.text_frame.paragraphs[0]
    p_d.text = "⚡ Secret Weapon for Hackathon Demo: Standalone Simulation Command Center (/sim). With a single click, we inject physical degradation on stage, trigger visual shuddering & red alarms, and demonstrate instant AI resolution!"
    p_d.font.size = Pt(11.5)
    p_d.font.bold = True
    p_d.font.color.rgb = GOLD

    # -------------------------------------------------------------
    # SLIDE 11: BUSINESS MODEL & ROI IN RUPEES
    # -------------------------------------------------------------
    slide11 = create_base_slide(prs, "Chapter 10 // Market Opportunity", "Business Model & Unbeatable ROI in Rupees (₹)", "A compelling B2B SaaS deployment model delivering 75x+ return on investment")
    
    # Left Card: Pricing & Delivery
    add_card(slide11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, GREEN)
    add_header_text(slide11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.1),
        "💼 Deployment & Pricing Structure", [
            "Target Customers: Automotive OEMs (Tata, Mahindra, Hyundai), Aerospace suppliers, and Robotics manufacturing plants.",
            "Delivery: Packaged as a self-contained on-prem Docker container. Field Deployment Engineer (FDE) assists initial 2-day setup.",
            "Subscription Model: ₹20,000 per critical machine / month.",
            "Standard Factory Cell (4 Critical Machines): ₹80,000 / month (₹9,60,000 / year).",
            "Enterprise Tier: Includes dedicated FDE support, custom PLC OPC-UA connectors, and continuous LoRA adapter training."
        ], GREEN)
        
    # Right Card: The ROI Math in Rupees
    add_card(slide11, Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1), CARD_BG, GOLD)
    tx_roi = slide11.shapes.add_textbox(Inches(6.9), Inches(1.6), Inches(5.6), Inches(5.1))
    tf_roi = tx_roi.text_frame
    tf_roi.word_wrap = True
    tf_roi.margin_left = tf_roi.margin_right = Inches(0.3)
    tf_roi.margin_top = Inches(0.3)
    
    p = tf_roi.paragraphs[0]
    p.text = "💰 The Math of Why Plants Buy Instantly"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = GOLD
    p.space_after = Pt(12)
    
    roi_points = [
        "Unplanned Downtime Cost: ₹18,00,000 per minute.",
        "A single 10-minute robot lockup costs the plant ₹1,80,00,000 (₹1.8 Crore!).",
        "Annual Fixer.ai Subscription for 4 Machines: ₹9,60,000 / year.",
        "THE BOTTOM LINE: Catching just ONE single 10-minute failure pays for the entire software subscription for nearly 19 YEARS.",
        "Preventative Scrap Savings: Eliminating premature 6-month part replacements saves an additional ₹40,00,000 annually per line.",
        "Estimated ROI: Exceeds 7,500% in Year 1."
    ]
    for rpt in roi_points:
        p = tf_roi.add_paragraph()
        p.text = "• " + rpt
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_BODY
        p.space_after = Pt(7)

    # -------------------------------------------------------------
    # SLIDE 12: WHY FIXER.AI WINS HACKFINIX 2026
    # -------------------------------------------------------------
    slide12 = create_base_slide(prs, "Chapter 11 // HackfiniX Alignment", "Why Fixer.ai Wins HackfiniX 2026", "A direct checklist against the official Finals Day judging criteria")
    
    criteria = [
        ("1. Innovation & Creativity", "Novel 'permanent technician' concept with isolated per-machine RAG memory instead of generic document search.", CYAN),
        ("2. Technical Implementation", "Full stack: FastAPI backend, ChromaDB vector store, Three.js CCTV digital twin, real-time WebSocket telemetry.", PURPLE),
        ("3. Functionality & Feasibility", "100% working live prototype with live fault injection via /sim. Dockerized deployment realistic for real factories.", GREEN),
        ("4. Impact & Relevance", "Solves the multi-crore downtime crisis (₹18L/min) in India's booming aerospace and automotive corridors.", ROSE),
        ("5. Presentation & UI/UX", "High-aesthetic CCTV interface built for Best UI/UX Award (₹10,000) and Incubation Support (Up to ₹10 Lakhs).", GOLD)
    ]
    
    c_w = Inches(11.7)
    c_h = Inches(0.85)
    start_y = Inches(1.6)
    gap_y = Inches(0.18)
    
    for i, (c_name, c_desc, c_color) in enumerate(criteria):
        y = start_y + i * (c_h + gap_y)
        add_card(slide12, Inches(0.8), y, c_w, c_h, CARD_BG, CARD_BORDER)
        tx = slide12.shapes.add_textbox(Inches(0.8), y, c_w, c_h)
        tf_c = tx.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = Inches(0.25)
        tf_c.margin_top = Inches(0.12)
        
        p = tf_c.paragraphs[0]
        p.text = c_name + ": "
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = c_color
        
        run = p.add_run()
        run.text = c_desc
        run.font.size = Pt(12)
        run.font.bold = False
        run.font.color.rgb = TEXT_BODY
        
    output_path = r"c:\Users\Aswin K J\Documents\Projects\fixer.ai\FixerAI_Hackathon_Pitch_Deck.pptx"
    prs.save(output_path)
    print(f"SUCCESS: Generated PowerPoint presentation at {output_path}")

if __name__ == "__main__":
    build_presentation()
