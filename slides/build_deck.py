#!/usr/bin/env python3
"""
Convert root-cause-analytics-engine/slides/deck.md into KCD PowerPoint presentation
with human-flow narrative titles, speaker name, vertical architecture diagram,
and verified visual alignment.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml import parse_xml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, "template.pptx")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "kcd-root-cause-analytics-engine.pptx")
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")

COLOR_NAVY = RGBColor(0x05, 0x05, 0x2D)
COLOR_BLUE = RGBColor(0x0A, 0x61, 0xF4)
COLOR_CYAN = RGBColor(0x43, 0xD4, 0xFE)
COLOR_MUTED = RGBColor(0x48, 0x65, 0x81)
COLOR_TEXT = RGBColor(0x10, 0x2A, 0x43)
COLOR_CARD_BG = RGBColor(0xF0, 0xF7, 0xFA)

def set_font(run, font_name="Arial", size_pt=13, color=COLOR_TEXT, bold=False):
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.color.rgb = color
    run.font.bold = bold

def disable_bullet(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        if child.tag.endswith('buNone') or child.tag.endswith('buChar') or child.tag.endswith('buAutoNum'):
            pPr.remove(child)
    pPr.append(parse_xml('<a:buNone xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>'))

def set_hanging_bullet(paragraph, char="•", indent_pts=18):
    pPr = paragraph._p.get_or_add_pPr()
    for child in list(pPr):
        if child.tag.endswith('buNone') or child.tag.endswith('buChar') or child.tag.endswith('buAutoNum'):
            pPr.remove(child)
    emu_val = str(int(indent_pts * 12700))
    pPr.set('marL', emu_val)
    pPr.set('indent', f"-{emu_val}")
    buChar = parse_xml(f'<a:buChar xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" char="{char}"/>')
    pPr.append(buChar)

def add_notes(slide, goal, talk_track, transition=""):
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.clear()
    
    p_goal = tf.paragraphs[0]
    p_goal.text = f"GOAL: {goal}"
    
    p_track_head = tf.add_paragraph()
    p_track_head.text = "\nTALK TRACK:"
    
    for item in talk_track:
        p_item = tf.add_paragraph()
        p_item.text = f"• {item}"
        
    if transition:
        p_trans = tf.add_paragraph()
        p_trans.text = f"\nTRANSITION: {transition}"

def create_deck():
    prs = Presentation(TEMPLATE_PATH)
    layouts = prs.slide_layouts
    initial_slide_count = len(prs.slides)

    def populate_slide_number(slide, num_str):
        tx = slide.shapes.add_textbox(Inches(9.4), Inches(5.20), Inches(0.55), Inches(0.3))
        tf = tx.text_frame
        tf.word_wrap = False
        tf.margin_left = Inches(0)
        tf.margin_right = Inches(0)
        tf.margin_top = Inches(0)
        tf.margin_bottom = Inches(0)
        p = tf.paragraphs[0]
        disable_bullet(p)
        p.alignment = PP_ALIGN.CENTER
        p.text = num_str
        for r in p.runs:
            set_font(r, font_name="Arial", size_pt=10, color=COLOR_MUTED)

    # ====================================================
    # SLIDE 1: Title Slide (Layout 4: TITLE_1) - With Speaker Name!
    # ====================================================
    s1 = prs.slides.add_slide(layouts[4])
    p0 = s1.placeholders[0]
    p0.text_frame.word_wrap = True
    p0.text_frame.text = "Building a Root Cause Analytics Engine\nwith Prometheus, Grafana, and MCP"
    for p in p0.text_frame.paragraphs:
        disable_bullet(p)
        for r in p.runs:
            set_font(r, font_name="Arial", size_pt=26, color=COLOR_NAVY, bold=True)
            
    p1 = s1.placeholders[1]
    p1.text_frame.word_wrap = True
    p1.text_frame.text = "El Muhammad Cholid H.  ·  Founder, DevOps Focus Group\nKubernetes Community Days Indonesia 2026"
    for p in p1.text_frame.paragraphs:
        disable_bullet(p)
        for r in p.runs:
            set_font(r, font_name="Arial", size_pt=14, color=COLOR_BLUE)
            
    add_notes(
        s1,
        goal="Frame the talk and set immediate expectations.",
        talk_track=[
            "Welcome everyone. This architecture started at a real fintech client with strict regulatory constraints.",
            "Today's demo runs on synthetic data and fits in a public repo you can test on your laptop.",
            "Two clear non-goals: this is NOT autonomous remediation, and it does NOT replace on-call engineers."
        ],
        transition="Let's look at what actually happens when an incident wakes you up."
    )

    # ====================================================
    # SLIDE 2: Act 1 - The 3am Problem (Layout 12)
    # Narrative Title: "When an alert fires at 3am, the clock starts ticking"
    # ====================================================
    s2 = prs.slides.add_slide(layouts[12])
    p0 = s2.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "When an alert fires at 3am,\nthe clock starts ticking"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Alerts tell you users are hurting, but never why"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s2.placeholders[1].text_frame.clear()
    tb2 = s2.shapes.add_textbox(Inches(4.6), Inches(0.9), Inches(4.8), Inches(4.0))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    
    p2_head = tf2.paragraphs[0]
    disable_bullet(p2_head)
    p2_head.text = "The hardest part of on-call isn't typing the fix:"
    p2_head.space_after = Pt(14)
    for r in p2_head.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    items2 = [
        "What changed first in the distributed system",
        "Which service is the real root cause versus cascade victim",
        "How far the blast radius has spread across dependencies",
        "What exact hypothesis to verify next without guessing"
    ]
    for it in items2:
        p = tf2.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        p.text = it
        p.space_after = Pt(8)
        for r in p.runs:
            set_font(r, size_pt=13, color=COLOR_TEXT)

    p2_call = tf2.add_paragraph()
    disable_bullet(p2_call)
    p2_call.text = "\nThe on-call reality:\nYou spend 40 minutes jumping across 12 dashboard tabs, grep-ing endless logs, and hoping your intuition holds."
    p2_call.space_before = Pt(8)
    for r in p2_call.runs:
        set_font(r, size_pt=12, color=COLOR_BLUE, bold=True)

    add_notes(
        s2,
        goal="Connect with the audience's shared pain of on-call triage.",
        talk_track=[
            "Ask the room: who has spent 40 minutes at 3am clicking 12 dashboard tabs while Slack explodes?",
            "Typing a kubectl command or applying a patch takes 2 minutes. Finding WHAT to fix takes 40 minutes.",
            "Alerts tell you symptoms, never the root cause."
        ],
        transition="The natural reaction today is: why not just hand the logs to an LLM?"
    )

    # ====================================================
    # SLIDE 3: Act 1 - The Naive Trap (Layout 8: Wide Canvas)
    # Narrative Title: "The obvious instinct is to point an LLM at your logs"
    # Uses clean diagram (naive_flow_diagram.png) on right!
    # ====================================================
    s3 = prs.slides.add_slide(layouts[8])
    tx3 = s3.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.6), Inches(4.2))
    tf3 = tx3.text_frame
    tf3.word_wrap = True
    
    p3_t = tf3.paragraphs[0]
    disable_bullet(p3_t)
    p3_t.text = "The obvious instinct is to\npoint an LLM at your logs"
    p3_t.space_after = Pt(6)
    for r in p3_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p3_s = tf3.add_paragraph()
    disable_bullet(p3_s)
    p3_s.text = "Why unconstrained diagnostic agents break down:"
    p3_s.space_after = Pt(14)
    for r in p3_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    reasons3 = [
        ("Massive context waste", "Dumping gigabytes of raw logs floods context windows with irrelevant noise."),
        ("Hallucinated causality", "Models mistake downstream cascade symptoms for primary root causes."),
        ("Unbounded latency & cost", "Open-ended exploration spins on endless log streams."),
        ("Security hazard", "Broad kubectl or cluster-admin privileges handed to model prompts.")
    ]
    for title, desc in reasons3:
        p = tf3.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    img3 = os.path.join(ASSETS_DIR, "naive_flow_diagram.png")
    if os.path.exists(img3):
        s3.shapes.add_picture(img3, Inches(5.4), Inches(1.0), width=Inches(4.0))

    add_notes(
        s3,
        goal="Deconstruct why naive LLM debugging fails in production.",
        talk_track=[
            "Walk through the diagram: alert triggers -> LLM gets broad kubectl access -> dumps gigabytes of logs.",
            "Result: 100k tokens burned, context exhausted, and the model confuses cascade noise for the real bug.",
            "Worse: giving an unconstrained prompt cluster-admin credentials is a critical security hole."
        ],
        transition="So how do disciplined SREs actually solve this? They bound the evidence first."
    )

    # ====================================================
    # SLIDE 4: Act 1 - The Solution (Layout 8: 3 Visual Cards)
    # Narrative Title: "Instead of searching blindly, bound the evidence first"
    # ====================================================
    s4 = prs.slides.add_slide(layouts[8])
    tx4_top = s4.shapes.add_textbox(Inches(0.6), Inches(0.7), Inches(8.8), Inches(1.0))
    tf4 = tx4_top.text_frame
    tf4.word_wrap = True
    p4_t = tf4.paragraphs[0]
    disable_bullet(p4_t)
    p4_t.text = "Instead of searching blindly, bound the evidence first"
    p4_t.space_after = Pt(4)
    for r in p4_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p4_s = tf4.add_paragraph()
    disable_bullet(p4_s)
    p4_s.text = "Answer the first five minutes with three disciplined layers of proof:"
    for r in p4_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    cards_data = [
        ("1. Metrics (RED)", "Rate, Errors, Duration & Saturation",
         "Metrics establish correlation, not causation.\n\nTheir job is to isolate when the anomaly began and narrow candidate services to a small set.",
         Inches(0.6)),
        ("2. Traces (Path)", "Distributed Call Graph",
         "Traces bound the path across services.\n\nThey identify which upstream caller triggered which failing downstream dependency in the call tree.",
         Inches(3.6)),
        ("3. Logs (Targeted)", "Exception & Stack Proof",
         "Targeted error signature proof.\n\nQueried ONLY after metrics and traces isolate the time window to seconds and target to one pod. Used for confirmation, never discovery.",
         Inches(6.6))
    ]

    for title, subtitle, desc, left_pos in cards_data:
        card = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.8), Inches(2.8), Inches(3.2))
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD_BG
        card.line.color.rgb = COLOR_BLUE
        card.line.width = Pt(1.5)
        
        tf_c = card.text_frame
        tf_c.word_wrap = True
        tf_c.margin_left = Inches(0.2)
        tf_c.margin_right = Inches(0.2)
        tf_c.margin_top = Inches(0.25)
        
        p1 = tf_c.paragraphs[0]
        disable_bullet(p1)
        p1.text = title
        p1.space_after = Pt(4)
        for r in p1.runs:
            set_font(r, size_pt=15, color=COLOR_NAVY, bold=True)
            
        p2 = tf_c.add_paragraph()
        disable_bullet(p2)
        p2.text = subtitle
        p2.space_after = Pt(10)
        for r in p2.runs:
            set_font(r, size_pt=11, color=COLOR_BLUE, bold=True)
            
        p3 = tf_c.add_paragraph()
        disable_bullet(p3)
        p3.text = desc
        for r in p3.runs:
            set_font(r, size_pt=12, color=COLOR_TEXT)

    add_notes(
        s4,
        goal="Explain the strict evidence hierarchy: Metrics -> Traces -> Logs.",
        talk_track=[
            "Step 1: Metrics isolate the anomaly window and narrow candidates. They prove correlation, not causation.",
            "Step 2: Traces bound the exact distributed path. Who called who, where did the latency spike?",
            "Step 3: Logs are queried last, for confirmation, never discovery. Querying 30 seconds of targeted logs costs nothing."
        ],
        transition="Where do we correlate all three? Grafana."
    )

    # ====================================================
    # SLIDE 5: Act 2 - The Evidence Plane (Layout 8: Wide Canvas)
    # Narrative Title: "Grafana is where telemetry turns into correlation"
    # ====================================================
    s5 = prs.slides.add_slide(layouts[8])
    tx5 = s5.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(8.8), Inches(1.1))
    tf5 = tx5.text_frame
    tf5.word_wrap = True
    p5 = tf5.paragraphs[0]
    disable_bullet(p5)
    p5.text = "Grafana is where telemetry turns into correlation"
    p5.space_after = Pt(4)
    for r in p5.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p5_sub = tf5.add_paragraph()
    disable_bullet(p5_sub)
    p5_sub.text = "Prometheus, Loki, and Tempo hold the data. Grafana correlates them, and MCP exposes read-only questions."
    for r in p5_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    img5 = os.path.join(ASSETS_DIR, "evidence-plane.png")
    if os.path.exists(img5):
        s5.shapes.add_picture(img5, Inches(0.6), Inches(2.1), width=Inches(8.8))

    add_notes(
        s5,
        goal="Establish Grafana, not the AI, as the center of evidence correlation.",
        talk_track=[
            "Many expect MCP or an LLM to be the core architecture. It isn't.",
            "Grafana is already your federation engine: it connects Prometheus, Loki, and Tempo with unified dashboards.",
            "MCP is simply a thin read-only interface letting our engine query existing Grafana datasources safely."
        ],
        transition="Here is how we translated this enterprise pattern into an open repo."
    )

    # ====================================================
    # SLIDE 6: Act 2 - Moving to Open Source (Layout 13: Inverted 2-Column)
    # Narrative Title: "Taking an enterprise pattern and making it reproducible"
    # ====================================================
    s6 = prs.slides.add_slide(layouts[13])
    p6_right = s6.placeholders[0]
    tf6_r = p6_right.text_frame
    tf6_r.word_wrap = True
    tf6_r.clear()
    p = tf6_r.paragraphs[0]
    disable_bullet(p)
    p.text = "Taking an enterprise pattern\nand making it reproducible"
    p.space_after = Pt(10)
    for r in p.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf6_r.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "How we rebuilt proprietary production controls into an open demo"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    p6_left = s6.placeholders[1]
    tf6_l = p6_left.text_frame
    tf6_l.word_wrap = True
    tf6_l.clear()

    table_data = [
        ("Evidence Queries", "Client: internal telemetry / Repo: fixed templates over 3 services"),
        ("Correlation Plane", "Client: enterprise Grafana / Repo: public starter dashboard"),
        ("MCP Gateway", "Client: internal auth proxy / Repo: standalone read-only server"),
        ("Incident State", "Client: full incident ticketing / Repo: clean persisted state machine"),
        ("Validation", "Client: canary check suite / Repo: one-click fault toggle")
    ]
    for i, (k, v) in enumerate(table_data):
        p = tf6_l.paragraphs[0] if i == 0 else tf6_l.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{k}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = v
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s6,
        goal="Show that the demo retains genuine enterprise design principles.",
        talk_track=[
            "Everything in proprietary production has a 1-to-1 open equivalent in the repo.",
            "Client auth proxies become standalone MCP servers; internal telemetry becomes synthetic RED metrics.",
            "You get the exact same state machine and validation loops in a simple Docker Compose setup."
        ],
        transition="Now, rule number one for production safety."
    )

    # ====================================================
    # SLIDE 7: Act 2 - Core Safety Rule 1 (Layout 8: Left Text + Right IDE Code Image)
    # Narrative Title: "Never let an LLM write raw PromQL in production"
    # ====================================================
    s7 = prs.slides.add_slide(layouts[8])
    tx7 = s7.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.5), Inches(4.2))
    tf7 = tx7.text_frame
    tf7.word_wrap = True
    p7_t = tf7.paragraphs[0]
    disable_bullet(p7_t)
    p7_t.text = "Never let an LLM write\nraw PromQL in production"
    p7_t.space_after = Pt(6)
    for r in p7_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p7_s = tf7.add_paragraph()
    disable_bullet(p7_s)
    p7_s.text = "The gateway translates intent into verified recording rules"
    p7_s.space_after = Pt(14)
    for r in p7_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    pts7 = [
        ("Hallucination Risk", "Models hallucinate metric names and label keys under incident stress."),
        ("Cluster Safety", "Unguarded regex PromQL can easily crash production Prometheus instances."),
        ("Deterministic RED", "Vetted recording rules pre-compute RED metrics deterministically."),
        ("Parameter Injection", "The model supplies parameters; the gateway executes verified templates.")
    ]
    for title, desc in pts7:
        p = tf7.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    img7 = os.path.join(ASSETS_DIR, "code_promql.png")
    if os.path.exists(img7):
        s7.shapes.add_picture(img7, Inches(5.3), Inches(1.1), width=Inches(4.2))

    add_notes(
        s7,
        goal="Explain why dynamic PromQL generation is banned.",
        talk_track=[
            "Never give an LLM an open PromQL prompt in production.",
            "Why? Complex regex or unindexed label queries can crash your Prometheus cluster right during an active incident.",
            "Instead, SREs pre-vetted recording rules. The engine exposes named tools, and the gateway fills parameters into fixed queries."
        ],
        transition="And we enforce this boundary with strict schemas."
    )

    # ====================================================
    # SLIDE 8: Act 2 - Core Safety Rule 2 (Layout 8: Left Text + Right IDE Code Image)
    # Narrative Title: "Enforce security in schemas, not in prompts"
    # ====================================================
    s8 = prs.slides.add_slide(layouts[8])
    tx8 = s8.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.5), Inches(4.2))
    tf8 = tx8.text_frame
    tf8.word_wrap = True
    p8_t = tf8.paragraphs[0]
    disable_bullet(p8_t)
    p8_t.text = "Enforce security in schemas,\nnot in prompts"
    p8_t.space_after = Pt(6)
    for r in p8_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p8_s = tf8.add_paragraph()
    disable_bullet(p8_s)
    p8_s.text = "Tool schemas act as executable, hard-coded guardrails"
    p8_s.space_after = Pt(14)
    for r in p8_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    b_items8 = [
        ("No Extra Properties", "additionalProperties: false rejects injected unexpected arguments."),
        ("Enum Constrained", "Enums constrain targets to verified service catalog entries only."),
        ("Bounded Windows", "Time windows are bounded: impossible to query full year history."),
        ("Immediate Rejection", "Violations reject instantly at MCP layer before touching datasources.")
    ]
    for title, desc in b_items8:
        p = tf8.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    img8 = os.path.join(ASSETS_DIR, "code_schema.png")
    if os.path.exists(img8):
        s8.shapes.add_picture(img8, Inches(5.3), Inches(1.1), width=Inches(4.2))

    add_notes(
        s8,
        goal="Show how JSON Schema provides deterministic policy enforcement.",
        talk_track=[
            "Prompt instructions like 'please do not query broad time windows' fail under pressure.",
            "Schemas don't negotiate: 'additionalProperties: false', enum-constrained service names, and bounded duration limits.",
            "If an argument doesn't validate, the MCP gateway rejects it before the packet ever hits Grafana."
        ],
        transition="Once tools are safe, how do we structure the investigation flow?"
    )

    # ====================================================
    # SLIDE 9: Act 3 - The State Machine (Layout 8: Wide Canvas)
    # Narrative Title: "Every state change must be an auditable human decision"
    # ====================================================
    s9 = prs.slides.add_slide(layouts[8])
    tx9 = s9.shapes.add_textbox(Inches(0.6), Inches(0.7), Inches(8.8), Inches(1.0))
    tf9 = tx9.text_frame
    tf9.word_wrap = True
    p9 = tf9.paragraphs[0]
    disable_bullet(p9)
    p9.text = "Every state change must be an auditable human decision"
    p9.space_after = Pt(4)
    for r in p9.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p9_sub = tf9.add_paragraph()
    disable_bullet(p9_sub)
    p9_sub.text = "An explicit state machine where transitions require proof, and automated actions remain locked."
    for r in p9_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    img9 = os.path.join(ASSETS_DIR, "incident-state-wide.png")
    if os.path.exists(img9):
        # 2976 x 920 aspect ratio is ~3.23 : 1. Width 8.8 in -> Height ~2.72 in
        s9.shapes.add_picture(img9, Inches(0.6), Inches(1.85), width=Inches(8.8), height=Inches(2.72))

    add_notes(
        s9,
        goal="Walk the 10-stage auditable state machine.",
        talk_track=[
            "State transitions are persisted records in a database, not internal loops in an agent's memory.",
            "Follow the flow: Received -> Planned -> Collecting -> Synthesizing -> Human Gate.",
            "Notice node 5: rejecting a hypothesis explicitly returns to planning. Notice 7b: automated patching is disabled by policy."
        ],
        transition="Let's look at how that initial plan is scoped."
    )

    # ====================================================
    # SLIDE 10: Act 3 - Explicit Scope (Layout 8: Left Text + Right IDE Code Image)
    # Narrative Title: "The alert builds a shared plan before anyone runs queries"
    # ====================================================
    s10 = prs.slides.add_slide(layouts[8])
    tx10 = s10.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.5), Inches(4.2))
    tf10 = tx10.text_frame
    tf10.word_wrap = True
    p10_t = tf10.paragraphs[0]
    disable_bullet(p10_t)
    p10_t.text = "The alert builds a shared plan\nbefore anyone runs queries"
    p10_t.space_after = Pt(6)
    for r in p10_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p10_s = tf10.add_paragraph()
    disable_bullet(p10_s)
    p10_s.text = "Persisted incident scope created immediately upon trigger"
    p10_s.space_after = Pt(14)
    for r in p10_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    pts10 = [
        ("Persisted State", "Plan is persisted to storage before any worker executes diagnostic queries."),
        ("Live Collaboration", "Engineers can view and edit the hypothesis queue live in incident chat."),
        ("No Runaway Loops", "Prevents duplicate queries and runaway investigation branches.")
    ]
    for title, desc in pts10:
        p = tf10.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(8)

    img10 = os.path.join(ASSETS_DIR, "code_plan.png")
    if os.path.exists(img10):
        s10.shapes.add_picture(img10, Inches(5.3), Inches(1.1), width=Inches(4.2))

    add_notes(
        s10,
        goal="Explain why planning happens before execution.",
        talk_track=[
            "When the alert fires, it first builds a visible plan: services in scope, time boundaries, and initial hypotheses.",
            "This plan is posted into the incident channel immediately.",
            "If an on-call engineer joins 10 minutes late, they read a clear checklist instead of guessing what the bot is doing."
        ],
        transition="Who actually runs the checks? Five narrow workers."
    )

    # ====================================================
    # SLIDE 11: Act 3 - Parallel Roles (Layout 12)
    # Narrative Title: "Five focused workers asking five narrow questions"
    # ====================================================
    s11 = prs.slides.add_slide(layouts[12])
    p0 = s11.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "Five focused workers asking\nfive narrow questions"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Parallel investigation without ambient cluster authority"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s11.placeholders[1].text_frame.clear()
    tb11 = s11.shapes.add_textbox(Inches(4.6), Inches(0.9), Inches(4.8), Inches(4.0))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    p_head11 = tf11.paragraphs[0]
    disable_bullet(p_head11)
    p_head11.text = "Worker Boundaries:"
    p_head11.space_after = Pt(10)
    for r in p_head11.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    workers = [
        ("Metrics Worker", "Queries RED metrics & saturation. Zero PromQL."),
        ("Logs Worker", "Queries error signatures in a 3-minute window."),
        ("Trace Worker", "Inspects top 5 slowest/failing spans only."),
        ("Topology Worker", "Resolves service dependency tree from catalog."),
        ("Changes Worker", "Checks recent deployments & config diffs in past 30m.")
    ]
    for name, desc in workers:
        p = tf11.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        r1 = p.add_run()
        r1.text = f"{name}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s11,
        goal="Present the division of labor across specialized workers.",
        talk_track=[
            "Instead of one massive agent that does everything, we deploy five bounded workers.",
            "Each worker answers one question: Metrics checks RED; Logs checks 3 minutes; Traces checks top 5 spans; Topology checks dependencies; Changes checks recent deploys.",
            "None of them has ambient access to explore outside their lane."
        ],
        transition="And what do they return? Structured verdicts."
    )

    # ====================================================
    # SLIDE 12: Act 3 - Structured Verdicts (Layout 8: Left Text + Right IDE Code Image)
    # Narrative Title: "Ruling out a false lead is just as valuable as finding the bug"
    # ====================================================
    s12 = prs.slides.add_slide(layouts[8])
    tx12 = s12.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.5), Inches(4.2))
    tf12 = tx12.text_frame
    tf12.word_wrap = True
    p12_t = tf12.paragraphs[0]
    disable_bullet(p12_t)
    p12_t.text = "Ruling out a false lead is\njust as valuable as the fix"
    p12_t.space_after = Pt(6)
    for r in p12_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p12_s = tf12.add_paragraph()
    disable_bullet(p12_s)
    p12_s.text = "Structured evidence verdicts eliminate subjective debate"
    p12_s.space_after = Pt(14)
    for r in p12_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    pts12 = [
        ("Equally Valuable", "A rejected hypothesis is as valuable as a confirmed one."),
        ("Clear Auditing", "Engineers immediately see what was ruled out and why."),
        ("No Circular Logic", "Prevents circular arguments and re-testing known good subsystems."),
        ("Restricted Context", "Coordinator receives structured verdicts, never raw dumps.")
    ]
    for title, desc in pts12:
        p = tf12.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    img12 = os.path.join(ASSETS_DIR, "code_evidence.png")
    if os.path.exists(img12):
        s12.shapes.add_picture(img12, Inches(5.3), Inches(1.1), width=Inches(4.2))

    add_notes(
        s12,
        goal="Highlight that negative evidence stops engineers from wasting time.",
        talk_track=[
            "Proving that the database is healthy is just as valuable as finding an error in the auth pod.",
            "Workers return structured JSON verdicts: 'status: rejected', with exact metric proofs.",
            "This eliminates circular arguments and prevents people from re-checking components that are operating normally."
        ],
        transition="Here is the complete sequence in motion."
    )

    # ====================================================
    # SLIDE 13: Act 3 - Sequence Flow (Layout 8: Wide Canvas)
    # Narrative Title: "How the entire investigation unfolds end to end"
    # ====================================================
    s13 = prs.slides.add_slide(layouts[8])
    tx13 = s13.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(8.8), Inches(1.1))
    tf13 = tx13.text_frame
    tf13.word_wrap = True
    p13 = tf13.paragraphs[0]
    disable_bullet(p13)
    p13.text = "How the entire investigation unfolds end to end"
    p13.space_after = Pt(4)
    for r in p13.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p13_sub = tf13.add_paragraph()
    disable_bullet(p13_sub)
    p13_sub.text = "Alert ➔ Incident plan ➔ Parallel workers ➔ Synthesized root cause ➔ Human gate"
    for r in p13_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    img13 = os.path.join(ASSETS_DIR, "investigation-sequence.png")
    if os.path.exists(img13):
        s13.shapes.add_picture(img13, Inches(2.3), Inches(1.9), height=Inches(3.2))

    add_notes(
        s13,
        goal="Walk the end-to-end timeline smoothly.",
        talk_track=[
            "Walk through the steps: Alert fires -> Coordinator creates incident record -> 5 workers fan out concurrently.",
            "Results collect -> Synthesis correlates timeline -> Root cause proposed -> Human approval gate.",
            "Total elapsed time: under 45 seconds from initial trigger to actionable verdict."
        ],
        transition="Now let's examine the security boundaries that make this safe."
    )

    # ====================================================
    # SLIDE 14: Act 4 - Zero Trust (Layout 8: Left Vertical Diagram + Right Text Cards)
    # Narrative Title: "Architecture enforces trust, not polite prompts"
    # Uses clear vertical architecture diagram (dependency_vertical.png) on left!
    # ====================================================
    s14 = prs.slides.add_slide(layouts[8])
    
    # Left diagram
    img14 = os.path.join(ASSETS_DIR, "dependency_vertical.png")
    if os.path.exists(img14):
        s14.shapes.add_picture(img14, Inches(0.6), Inches(1.0), width=Inches(3.4))

    # Right text
    tx14 = s14.shapes.add_textbox(Inches(4.3), Inches(0.8), Inches(5.1), Inches(4.2))
    tf14 = tx14.text_frame
    tf14.word_wrap = True
    
    p14_t = tf14.paragraphs[0]
    disable_bullet(p14_t)
    p14_t.text = "Architecture enforces trust,\nnot polite prompts"
    p14_t.space_after = Pt(6)
    for r in p14_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p14_s = tf14.add_paragraph()
    disable_bullet(p14_s)
    p14_s.text = "Strict least-privilege security controls across four layers:"
    p14_s.space_after = Pt(14)
    for r in p14_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    boundaries = [
        ("Orchestrator", "Schedules tasks & state. Has ZERO Grafana source credentials."),
        ("MCP Gateway", "Read-only access to Grafana. Rejects all mutations and write calls."),
        ("Workers", "Ephemeral processes with single-purpose schema tokens."),
        ("Mitigation Engine", "Requires explicit cryptographic token from human chat approval.")
    ]
    for comp, bound in boundaries:
        p = tf14.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{comp}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = bound
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s14,
        goal="Explain why prompt injection cannot compromise cluster infrastructure.",
        talk_track=[
            "Notice how permissions are isolated across all four tiers:",
            "The Orchestrator holds no Grafana credentials. The MCP Gateway has zero write endpoints.",
            "Even if someone injected malicious text into an application log, the gateway physically cannot execute write commands."
        ],
        transition="What about Slack and Teams interaction? How do chat buttons work?"
    )

    # ====================================================
    # SLIDE 15: Act 4 - Interactive Ops (Layout 8: Left Text + Right IDE Code Image)
    # Narrative Title: "Chat buttons request actions, but the backend verifies"
    # ====================================================
    s15 = prs.slides.add_slide(layouts[8])
    tx15 = s15.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(4.5), Inches(4.2))
    tf15 = tx15.text_frame
    tf15.word_wrap = True
    p15_t = tf15.paragraphs[0]
    disable_bullet(p15_t)
    p15_t.text = "Chat buttons request actions,\nbut the backend verifies"
    p15_t.space_after = Pt(6)
    for r in p15_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p15_s = tf15.add_paragraph()
    disable_bullet(p15_s)
    p15_s.text = "Slack and Teams ChatOps pattern with cryptographic nonces"
    p15_s.space_after = Pt(14)
    for r in p15_s.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    pts15 = [
        ("No Direct Execution", "A chat button never triggers an action or shell script directly."),
        ("Server-Side RBAC", "The server validates actor identity, incident phase, and nonce freshness."),
        ("Replay Protection", "Stale or duplicate button clicks are rejected harmlessly."),
        ("Cryptographic Tokens", "Approved actions receive single-use scoped execution tokens.")
    ]
    for title, desc in pts15:
        p = tf15.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_NAVY, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(6)

    img15 = os.path.join(ASSETS_DIR, "code_chat_button.png")
    if os.path.exists(img15):
        s15.shapes.add_picture(img15, Inches(5.3), Inches(1.1), width=Inches(4.2))

    add_notes(
        s15,
        goal="Explain secure ChatOps button handling.",
        talk_track=[
            "A Slack button click never runs a script directly.",
            "It sends an intent payload to the backend server with a single-use cryptographic nonce.",
            "The server verifies caller RBAC, ensures the incident is in the correct state, and rejects duplicate or stale clicks."
        ],
        transition="Once mitigation is approved and applied, how do we confirm recovery?"
    )

    # ====================================================
    # SLIDE 16: Act 4 - Verified Recovery (Layout 12)
    # Narrative Title: "A human applies the fix, but telemetry proves it worked"
    # ====================================================
    s16 = prs.slides.add_slide(layouts[12])
    p0 = s16.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "A human applies the fix,\nbut telemetry proves it worked"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Closing the loop with automated verification cycles"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s16.placeholders[1].text_frame.clear()
    tb16 = s16.shapes.add_textbox(Inches(4.6), Inches(0.9), Inches(4.8), Inches(4.0))
    tf16 = tb16.text_frame
    tf16.word_wrap = True

    p_head16 = tf16.paragraphs[0]
    disable_bullet(p_head16)
    p_head16.text = "Post-Mitigation Validation Cycle:"
    p_head16.space_after = Pt(10)
    for r in p_head16.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    steps16 = [
        ("Mitigation Applied", "Engineer approves deployment rollback or traffic re-route."),
        ("Automated Health Check", "Gateway monitors 3 consecutive evaluation cycles (3x 60s)."),
        ("Error Rate Re-check", "Verifies payment-service error rate drops below 0.1% SLO threshold."),
        ("Auto-Resolution", "Transitions state to Resolved only when telemetry proves recovery.")
    ]
    for step, desc in steps16:
        p = tf16.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        r1 = p.add_run()
        r1.text = f"{step}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s16,
        goal="Describe closed-loop validation after applying a fix.",
        talk_track=[
            "Applying a fix isn't the end of an incident.",
            "The engine waits for 3 consecutive evaluation windows (3x 60s) to verify error rates return below SLO thresholds.",
            "Only when metrics confirm recovery does the state machine transition to Resolved."
        ],
        transition="And when it resolves, the post-mortem is already finished."
    )

    # ====================================================
    # SLIDE 17: Act 5 - Post-Mortem Automation (Layout 8: Wide Canvas)
    # Narrative Title: "The post-mortem assembles itself while you fix the incident"
    # ====================================================
    s17 = prs.slides.add_slide(layouts[8])
    tx17 = s17.shapes.add_textbox(Inches(0.6), Inches(0.8), Inches(8.8), Inches(1.0))
    tf17 = tx17.text_frame
    tf17.word_wrap = True
    p17 = tf17.paragraphs[0]
    disable_bullet(p17)
    p17.text = "The post-mortem assembles itself while you fix the incident"
    p17.space_after = Pt(4)
    for r in p17.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p17_sub = tf17.add_paragraph()
    disable_bullet(p17_sub)
    p17_sub.text = "The draft builds deterministically from the audit trail, waiting for human sign-off."
    for r in p17_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    img17 = os.path.join(ASSETS_DIR, "rca-draft-lifecycle.png")
    if os.path.exists(img17):
        s17.shapes.add_picture(img17, Inches(0.6), Inches(1.9), width=Inches(8.8))

    tx17_body = s17.shapes.add_textbox(Inches(0.6), Inches(2.7), Inches(8.8), Inches(2.4))
    tf17_body = tx17_body.text_frame
    tf17_body.word_wrap = True
    p17_b = tf17_body.paragraphs[0]
    disable_bullet(p17_b)
    p17_b.text = "Automated Post-Mortem Assembly Lifecycle:"
    p17_b.space_after = Pt(8)
    for r in p17_b.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    stages17 = [
        ("1. Resolution Acknowledged", "Incident recovery event freezes evidence collection and triggers post-mortem generation."),
        ("2. Structured Record Pull", "Gathers alert timestamps, hypotheses tested/rejected, and confirmed telemetry verdicts."),
        ("3. Template Merge", "Renders the data into the standardized incident report format without manual copy-pasting."),
        ("4. Draft Created", "Stores draft in designated incident review location with immutable audit links."),
        ("5. Human Review", "Engineer verifies accuracy, adds organizational context, and signs off."),
        ("6. Distribution", "Publishes final post-mortem report to incident channels and stakeholder teams.")
    ]
    for stage, desc in stages17:
        p = tf17_body.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{stage}: "
        set_font(r1, size_pt=11, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=11, color=COLOR_TEXT)
        p.space_after = Pt(4)

    add_notes(
        s17,
        goal="Showcase the immediate practical benefit: zero manual post-mortem writing.",
        talk_track=[
            "Nobody likes writing post-mortems days later when memory fades and metric charts have expired.",
            "Because our engine recorded every step as an auditable state transition, the post-mortem compiles automatically upon resolution.",
            "All timestamps, rejected hypotheses, and metric proofs are already organized for final human sign-off."
        ],
        transition="Let's summarize the architecture comparison side-by-side."
    )

    # ====================================================
    # SLIDE 18: Act 5 - Comparison (Layout 13: Inverted 2-Column)
    # Narrative Title: "Why bounding the evidence beats dumping the logs"
    # ====================================================
    s18 = prs.slides.add_slide(layouts[13])
    p18_right = s18.placeholders[0]
    tf18_r = p18_right.text_frame
    tf18_r.word_wrap = True
    tf18_r.clear()
    p = tf18_r.paragraphs[0]
    disable_bullet(p)
    p.text = "Why bounding the evidence\nbeats dumping the logs"
    p.space_after = Pt(10)
    for r in p.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf18_r.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Comparing the two architectures across five production dimensions"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    p18_left = s18.placeholders[1]
    tf18_l = p18_left.text_frame
    tf18_l.word_wrap = True
    tf18_l.clear()

    comparisons18 = [
        ("Query Scope", "Raw Log: unbounded dump / RCA Engine: bounded RED rules"),
        ("Plan State", "Raw Log: implicit model thoughts / RCA Engine: persisted, auditable state"),
        ("Token Cost", "Raw Log: 100k+ tokens / RCA Engine: < 4k structured tokens"),
        ("Security Privileges", "Raw Log: kubectl cluster-admin / RCA Engine: read-only scoped MCP"),
        ("Human Control", "Raw Log: hope model behaves / RCA Engine: state machine approval gates")
    ]
    for i, (k, v) in enumerate(comparisons18):
        p = tf18_l.paragraphs[0] if i == 0 else tf18_l.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{k}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = v
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s18,
        goal="Compare raw log dumping against bounded evidence.",
        talk_track=[
            "Be transparent about the trade-off: this requires building clean telemetry and recording rules.",
            "In exchange, you cut token usage from 100k down to 4k tokens, drop query latency from minutes to seconds, and eliminate cluster-admin security risks."
        ],
        transition="And we should be equally honest about what this engine cannot do."
    )

    # ====================================================
    # SLIDE 19: Act 5 - Reality Check (Layout 12)
    # Narrative Title: "Where this design deliberately stops"
    # ====================================================
    s19 = prs.slides.add_slide(layouts[12])
    p0 = s19.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "Where this design\ndeliberately stops"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Clear boundaries that maintain engineering credibility"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s19.placeholders[1].text_frame.clear()
    tb19 = s19.shapes.add_textbox(Inches(4.6), Inches(0.9), Inches(4.8), Inches(4.0))
    tf19 = tb19.text_frame
    tf19.word_wrap = True

    p_head19 = tf19.paragraphs[0]
    disable_bullet(p_head19)
    p_head19.text = "Hard Limits of the Engine:"
    p_head19.space_after = Pt(10)
    for r in p_head19.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    limits19 = [
        ("Metrics give correlation, not causation", "Proving services degraded together != physical proof of bug."),
        ("Cannot fix missing telemetry", "If a service exports no RED metrics, the gateway cannot invent data."),
        ("Unmaintained dependency graphs fail", "Stale service catalogs cause the coordinator to miss cascade paths."),
        ("Not autonomous remediation", "Does not restart pods or alter routing without explicit human signoff.")
    ]
    for title, desc in limits19:
        p = tf19.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s19,
        goal="Earn trust with senior engineers by stating hard limitations plainly.",
        talk_track=[
            "State these upfront: correlation is never causation, and no AI can invent metrics you didn't collect.",
            "If your service catalog is outdated or missing RED metrics, the engine cannot help you.",
            "Most importantly: this is NOT autonomous remediation. Humans stay in the loop."
        ],
        transition="How can teams start implementing this today?"
    )

    # ====================================================
    # SLIDE 20: Act 6 - Roadmap (Layout 12)
    # Narrative Title: "How to build this incrementally without boiling the ocean"
    # ====================================================
    s20 = prs.slides.add_slide(layouts[12])
    p0 = s20.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "How to build this incrementally\nwithout boiling the ocean"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "A 4-step adoption roadmap that delivers value from day one"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s20.placeholders[1].text_frame.clear()
    tb20 = s20.shapes.add_textbox(Inches(4.6), Inches(0.9), Inches(4.8), Inches(4.0))
    tf20 = tb20.text_frame
    tf20.word_wrap = True

    p_head20 = tf20.paragraphs[0]
    disable_bullet(p_head20)
    p_head20.text = "Phased Adoption Roadmap:"
    p_head20.space_after = Pt(10)
    for r in p_head20.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    phases20 = [
        ("Phase 1: Telemetry & Rules", "Standardize RED metrics and Prometheus recording rules on tier-1 services."),
        ("Phase 2: Grafana Correlation", "Build single-pane dashboard linking metrics, Loki logs, and Tempo traces."),
        ("Phase 3: Read-Only MCP Gateway", "Wrap dashboard queries in structured, parameterized tool schemas."),
        ("Phase 4: State Machine & RCA", "Add incident state machine, hypothesis queue, and chat approval gates.")
    ]
    for ph, desc in phases20:
        p = tf20.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        r1 = p.add_run()
        r1.text = f"{ph}: "
        set_font(r1, size_pt=12, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(6)

    add_notes(
        s20,
        goal="Provide a pragmatic, low-risk adoption path.",
        talk_track=[
            "Do not start by deploying AI agents.",
            "Phase 1 and Phase 2 are standard observability engineering: RED recording rules and correlated dashboards.",
            "Once human engineers have fast correlation dashboards, adding the MCP gateway and state machine is easy."
        ],
        transition="Here are the three big takeaways to bring home."
    )

    # ====================================================
    # SLIDE 21: Act 6 - Core Takeaways (Layout 16: Big Center Slide)
    # Narrative Title: "Three principles to take back to your team"
    # ====================================================
    s21 = prs.slides.add_slide(layouts[16])
    p21_c = s21.placeholders[0]
    tf21 = p21_c.text_frame
    tf21.word_wrap = True
    tf21.clear()
    
    p = tf21.paragraphs[0]
    disable_bullet(p)
    p.text = "Three principles to take back to your team"
    p.space_after = Pt(14)
    for r in p.runs:
        set_font(r, size_pt=24, color=COLOR_NAVY, bold=True)

    takeaways = [
        ("1. Put Grafana at the evidence plane", "Prometheus and Loki hold truth; Grafana correlates them. Build tooling at the correlation layer, not individual datasources."),
        ("2. The model never writes queries", "Tool schemas are executable policies. Expose narrow, parameterized questions with zero dynamic query syntax."),
        ("3. Persist the plan and the state", "Keep humans in control with auditable state transitions, visible hypotheses, and explicit approval gates.")
    ]
    for title, desc in takeaways:
        p = tf21.add_paragraph()
        set_hanging_bullet(p, indent_pts=16)
        r1 = p.add_run()
        r1.text = f"{title}: "
        set_font(r1, size_pt=13, color=COLOR_BLUE, bold=True)
        r2 = p.add_run()
        r2.text = desc
        set_font(r2, size_pt=12, color=COLOR_TEXT)
        p.space_after = Pt(8)

    add_notes(
        s21,
        goal="Deliver three clear takeaways slowly and deliberately.",
        talk_track=[
            "1. Put Grafana at the evidence plane: don't build integrations on raw Prometheus and Loki directly.",
            "2. Never let models write queries: schemas are hard policies that prevent crashes.",
            "3. Persist the plan and the state: keep humans in control with auditable transitions."
        ],
        transition="You can run the entire system on your laptop right now."
    )

    # ====================================================
    # SLIDE 22: Act 6 - The Demo (Layout 12)
    # Narrative Title: "Try the entire stack locally on your machine"
    # ====================================================
    s22 = prs.slides.add_slide(layouts[12])
    p0 = s22.placeholders[0]
    tf0 = p0.text_frame
    tf0.word_wrap = True
    tf0.clear()
    p_t = tf0.paragraphs[0]
    disable_bullet(p_t)
    p_t.text = "Try the entire stack locally\non your machine"
    p_t.space_after = Pt(12)
    for r in p_t.runs:
        set_font(r, size_pt=22, color=COLOR_NAVY, bold=True)
    p_sub = tf0.add_paragraph()
    disable_bullet(p_sub)
    p_sub.text = "Clone the repo and run the three-service demo with Docker Compose"
    for r in p_sub.runs:
        set_font(r, size_pt=13, color=COLOR_MUTED)

    s22.placeholders[1].text_frame.clear()
    tb22 = s22.shapes.add_textbox(Inches(4.4), Inches(0.9), Inches(5.1), Inches(4.2))
    tf22 = tb22.text_frame
    tf22.word_wrap = True

    p_head22 = tf22.paragraphs[0]
    disable_bullet(p_head22)
    p_head22.text = "Everything in this talk is runnable in the demo repo:"
    p_head22.space_after = Pt(10)
    for r in p_head22.runs:
        set_font(r, size_pt=14, color=COLOR_NAVY, bold=True)

    items22 = [
        "Prometheus recording rules & alert configurations",
        "Grafana correlation dashboard with RED metric panels",
        "Read-only Model Context Protocol (MCP) gateway server",
        "Contained fault-injection switch to trigger synthetic incidents",
        "Step-by-step Makefile: make up && make fault"
    ]
    for it in items22:
        p = tf22.add_paragraph()
        set_hanging_bullet(p, indent_pts=18)
        p.text = it
        p.space_after = Pt(6)
        for r in p.runs:
            set_font(r, size_pt=12, color=COLOR_TEXT)

    p_repo = tf22.add_paragraph()
    disable_bullet(p_repo)
    p_repo.text = "\nRepo: github.com/eltrovert/root-cause-analytics-engine"
    p_repo.space_before = Pt(8)
    for r in p_repo.runs:
        set_font(r, size_pt=12, color=COLOR_BLUE, bold=True)

    add_notes(
        s22,
        goal="Point audience to the working implementation.",
        talk_track=[
            "Everything shown today is open source: Prometheus configs, Grafana dashboards, and the MCP gateway.",
            "Run 'make up' to start the stack, and 'make fault' to simulate a real latency spike.",
            "Keep this URL on screen for Q&A."
        ],
        transition="Thank you everyone!"
    )

    # ====================================================
    # SLIDE 23: Thank You Slide (Template layout 17: THANK YOU)
    # ====================================================
    s23 = prs.slides.add_slide(layouts[17])
    add_notes(
        s23,
        goal="Close smoothly and open for Q&A.",
        talk_track=[
            "Thank the KCD Indonesia organizers, sponsors, and attendees.",
            "Open the floor for questions about Prometheus, MCP, or incident state machines."
        ]
    )

    # ----------------------------------------------------
    # Delete initial 18 placeholder template slides & set slide numbers
    # ----------------------------------------------------
    for _ in range(initial_slide_count):
        rId = prs.slides._sldIdLst[0].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[0]

    for idx, slide in enumerate(prs.slides):
        populate_slide_number(slide, str(idx + 1))

    prs.save(OUTPUT_PATH)
    print(f"Successfully generated {len(prs.slides)} slides in {OUTPUT_PATH}")

if __name__ == "__main__":
    create_deck()
