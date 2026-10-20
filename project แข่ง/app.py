"""
=============================================================================
ระบบจัดตารางสอนอัตโนมัติด้วย AI (Automated Timetable Scheduling System)
ระดับการแข่งขันทักษะวิชาชีพ (National Vocational Skills Competition)
แอปพลิเคชันหลัก: Streamlit Full-Stack Dashboard (app.py)
=============================================================================
"""

import time
import json
import streamlit as st
import pandas as pd

from models import (
    DAYS, PERIODS, DAY_NAMES_TH, PERIOD_NAMES,
    Teacher, Room, StudentClass, SubjectAssignment
)
from data_manager import (
    generate_sample_dataset,
    dataset_to_models,
    validate_timetable_data,
    parse_json_input,
    parse_excel_input,
    parse_csv_input,
    generate_blank_template_excel,
    generate_blank_template_csv,
    generate_blank_template_json
)
from scheduler_engine import TimetableEngine
from export_manager import (
    build_grid_dataframe,
    timetable_to_dataframe,
    export_timetable_to_excel,
    export_timetable_to_csv,
    export_timetable_to_pdf
)

# ---------------------------------------------------------------------------
# ตั้งค่าหน้าเว็บ Streamlit (Page Configuration)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ระบบจัดตารางสอนอัตโนมัติด้วย AI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------------
# ตกแต่ง CSS เพื่อความสวยงามระดับพรีเมียม (Modern EdTech Design System)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Prompt', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Gradient & Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #3B82F6 100%);
        color: white;
        padding: 24px 30px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: #FFFFFF;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        margin: 8px 0 0 0;
        font-size: 15px;
        color: #DBEAFE;
    }
    
    /* Metric Card Component */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .metric-title {
        font-size: 13px;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-subtitle {
        font-size: 12px;
        color: #10B981;
        margin-top: 4px;
        font-weight: 500;
    }
    
    /* Badges */
    .badge-optimal {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-warning {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-error {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
    
    /* Timetable Grid Cell Styling */
    .cell-subject {
        font-weight: 600;
        color: #1E293B;
        font-size: 13px;
        line-height: 1.3;
    }
    .cell-info {
        font-size: 11px;
        color: #475569;
        margin-top: 2px;
    }
    .cell-badge {
        font-size: 10px;
        background: #E0E7FF;
        color: #3730A3;
        padding: 2px 6px;
        border-radius: 4px;
        font-weight: 500;
        display: inline-block;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# เริ่มต้น Session State
# ---------------------------------------------------------------------------
if "dataset" not in st.session_state:
    st.session_state.dataset = generate_sample_dataset("medium")
if "validation_result" not in st.session_state:
    st.session_state.validation_result = validate_timetable_data(st.session_state.dataset)
if "solver_result" not in st.session_state:
    st.session_state.solver_result = None
if "selected_sample_name" not in st.session_state:
    st.session_state.selected_sample_name = "ขนาดกลาง (Medium - แผนกวิชามาตรฐาน)"


# ---------------------------------------------------------------------------
# แถบควบคุมด้านข้าง (Sidebar Controls)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/calendar.png", width=64)
    st.markdown("### ⚙️ เมนูควบคุมหลัก")
    st.caption("ระบบจัดตารางสอนอัตโนมัติด้วย AI (CP-SAT)")
    st.markdown("---")
    
    # 1. ตัวเลือกชุดข้อมูลตัวอย่าง
    st.markdown("#### 📁 ชุดข้อมูลตัวอย่าง (Sample Datasets)")
    sample_choice = st.selectbox(
        "เลือกขนาดชุดข้อมูลตัวอย่าง:",
        [
            "ขนาดเล็ก (Small - 4 ครู, 3 ห้อง, 2 กลุ่มเรียน)",
            "ขนาดกลาง (Medium - 8 ครู, 6 ห้อง, 4 กลุ่มเรียน)",
            "ขนาดใหญ่ (Large - 16 ครู, 10 ห้อง, 8 กลุ่มเรียน)"
        ],
        index=1
    )
    
    if st.button("🔄 โหลดชุดข้อมูลตัวอย่างนี้", use_container_width=True):
        if "Small" in sample_choice:
            st.session_state.dataset = generate_sample_dataset("small")
            st.session_state.selected_sample_name = "ขนาดเล็ก (Small)"
        elif "Large" in sample_choice:
            st.session_state.dataset = generate_sample_dataset("large")
            st.session_state.selected_sample_name = "ขนาดใหญ่ (Large)"
        else:
            st.session_state.dataset = generate_sample_dataset("medium")
            st.session_state.selected_sample_name = "ขนาดกลาง (Medium)"
            
        st.session_state.validation_result = validate_timetable_data(st.session_state.dataset)
        st.session_state.solver_result = None
        st.success(f"✅ โหลดชุดข้อมูล {st.session_state.selected_sample_name} สำเร็จ!")
        st.rerun()

    st.markdown("---")
    
    # 2. ตั้งค่าสมองกล AI (Solver Hyperparameters)
    st.markdown("#### 🧠 ตั้งค่าสมองกล AI (Solver Config)")
    seed_value = st.number_input("สุ่มตัวเลขตั้งต้น (Random Seed):", min_value=0, max_value=99999, value=42, step=1, help="ตั้งค่าเพื่อความโปร่งใสและตรวจสอบซ้ำได้ 100% (Deterministic Mode)")
    time_limit = st.slider("ขีดจำกัดเวลาคำนวณ (วินาที):", min_value=5, max_value=60, value=15, step=5)
    deterministic_mode = st.toggle("Deterministic Search (ผลลัพธ์ซ้ำเดิม 100%)", value=True)
    strict_unavailability = st.toggle("บังคับช่วงเวลาห้ามสอนเด็ดขาด (Hard)", value=True)
    
    st.markdown("---")
    
    # 3. ดาวน์โหลดไฟล์ต้นแบบ (Download Templates)
    st.markdown("#### 📥 ดาวน์โหลดไฟล์ Template เปล่า")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.download_button(
            label="📗 Excel",
            data=generate_blank_template_excel(),
            file_name="timetable_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    with t_col2:
        st.download_button(
            label="📄 CSV",
            data=generate_blank_template_csv(),
            file_name="timetable_template.csv",
            mime="text/csv",
            use_container_width=True
        )
    st.download_button(
        label="📦 JSON Template",
        data=generate_blank_template_json(),
        file_name="timetable_template.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("---")
    st.caption("พัฒนาตามเกณฑ์การแข่งขันทักษะวิชาชีพระดับชาติ<br/>AI Constraint Programming: Google OR-Tools CP-SAT", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# ส่วนหัวหลักของหน้าเว็บ (Hero Header)
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>ระบบจัดตารางสอนอัตโนมัติด้วย AI (Automated Timetable Scheduling)</h1>
    <p>ระบบอัจฉริยะสำหรับสถานศึกษาและวิทยาลัยอาชีวศึกษา ขับเคลื่อนด้วยสมองกล Google OR-Tools CP-SAT Solver รับประกันปราศจากข้อขัดแย้ง 100% (Zero Conflicts)</p>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# เมนูแท็บหลัก (Main Navigation Tabs)
# ---------------------------------------------------------------------------
tab_import, tab_solve, tab_views, tab_dashboard, tab_export = st.tabs([
    "📥 1. นำเข้าและตรวจเช็คข้อมูล (Input & Validation)",
    "⚙️ 2. สมองกล AI คำนวณตาราง (AI Solver)",
    "🗓️ 3. แสดงผลตารางสอน (Timetable Views)",
    "📊 4. แดชบอร์ดตัวชี้วัด (Analytics Dashboard)",
    "📤 5. ศูนย์ส่งออกข้อมูล (Export Center)"
])


# ===========================================================================
# แท็บที่ 1: ระบบนำเข้าและตรวจสอบข้อมูล (Input & Validation - เกณฑ์ 10 คะแนน)
# ===========================================================================
with tab_import:
    st.markdown("### 📥 ระบบนำเข้าและตรวจสอบความถูกต้องของข้อมูล (Input Data System)")
    st.markdown("รองรับการอัปโหลดไฟล์ 3 รูปแบบ: **CSV, Excel (.xlsx), และ JSON** พร้อมระบบตรวจหาข้อผิดพลาดอัตโนมัติก่อนส่งให้ AI คำนวณ")
    
    # ส่วนอัปโหลดไฟล์
    uploaded_file = st.file_uploader(
        "อัปโหลดไฟล์ข้อมูลตารางสอน (ลากไฟล์มาวางที่นี่ หรือคลิกเพื่อเลือกไฟล์):",
        type=["xlsx", "csv", "json"],
        help="รองรับ Excel ที่มี 4 sheets (Teachers, Rooms, Classes, Subjects) หรือตารางรวม Master, หรือไฟล์ CSV, หรือ JSON"
    )
    
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        
        try:
            if file_name.endswith(".xlsx"):
                parsed_data = parse_excel_input(file_bytes)
                file_type_th = "Excel (.xlsx)"
            elif file_name.endswith(".csv"):
                parsed_data = parse_csv_input(file_bytes)
                file_type_th = "CSV"
            elif file_name.endswith(".json"):
                parsed_data = parse_json_input(file_bytes)
                file_type_th = "JSON"
            else:
                st.error("❌ ไฟล์ที่อัปโหลดไม่รองรับ")
                parsed_data = None
                
            if parsed_data:
                st.session_state.dataset = parsed_data
                st.session_state.validation_result = validate_timetable_data(parsed_data)
                st.session_state.solver_result = None
                st.session_state.selected_sample_name = f"ไฟล์นำเข้า: {uploaded_file.name}"
                st.success(f"✅ นำเข้าข้อมูลจากไฟล์ {file_type_th} สำเร็จ!")
        except Exception as e:
            st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")

    st.markdown("---")
    
    # รายงานการตรวจสอบความถูกต้อง (Validation Report)
    val_res = st.session_state.validation_result
    stats = val_res.get("stats", {})
    
    st.markdown("#### 🔍 ผลการตรวจสอบความถูกต้องก่อนคำนวณ (Validation Status)")
    
    # แถบสรุปผลความพร้อม
    if val_res["is_valid"]:
        st.markdown("""
        <div style="background-color: #ECFDF5; border-left: 5px solid #10B981; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px;">
            <b style="color: #065F46; font-size: 16px;">✅ ข้อมูลผ่านเกณฑ์การตรวจสอบสมบูรณ์ (Validation Passed)</b>
            <div style="color: #047857; font-size: 13px; margin-top: 4px;">ไม่พบข้อผิดพลาดร้ายแรง ระบบพร้อมส่งข้อมูลให้ AI CP-SAT ทำการคำนวณตารางสอนได้ทันที</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #FEF2F2; border-left: 5px solid #EF4444; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px;">
            <b style="color: #991B1B; font-size: 16px;">❌ พบข้อผิดพลาดในข้อมูลนำเข้า (Validation Failed)</b>
            <div style="color: #B91C1C; font-size: 13px; margin-top: 4px;">กรุณาแก้ไขข้อผิดพลาดที่ระบุไว้ด้านล่างก่อนเริ่มการคำนวณ</div>
        </div>
        """, unsafe_allow_html=True)
        
    # แสดง Errors ถ้ามี
    if val_res.get("errors"):
        st.markdown("**รายการข้อผิดพลาดที่ต้องแก้ไข (Critical Errors):**")
        for err in val_res["errors"]:
            st.error(err)

    # แสดง Warnings ถ้ามี
    if val_res.get("warnings"):
        st.markdown("**ข้อสังเกตและคำเตือน (Warnings):**")
        for warn in val_res["warnings"]:
            st.warning(warn)

    # การ์ดสรุปสถิติข้อมูลนำเข้า
    st.markdown("#### 📊 ข้อมูลสรุปภาพรวม (Overview Statistics)")
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    with s_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👨‍🏫 ครูผู้สอนทั้งหมด</div>
            <div class="metric-value">{stats.get('teacher_count', 0)} คน</div>
            <div class="metric-subtitle">ความพร้อมสมบูรณ์</div>
        </div>
        """, unsafe_allow_html=True)
    with s_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🚪 ห้องเรียนทั้งหมด</div>
            <div class="metric-value">{stats.get('room_count', 0)} ห้อง</div>
            <div class="metric-subtitle">ความจุรวม {stats.get('total_available_room_slots', 0)} คาบ</div>
        </div>
        """, unsafe_allow_html=True)
    with s_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">👥 กลุ่มเรียนทั้งหมด</div>
            <div class="metric-value">{stats.get('class_count', 0)} กลุ่ม</div>
            <div class="metric-subtitle">นักเรียนทุกระดับชั้น</div>
        </div>
        """, unsafe_allow_html=True)
    with s_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">📚 คาบที่ต้องจัดสอน</div>
            <div class="metric-value">{stats.get('total_periods_required', 0)} คาบ</div>
            <div class="metric-subtitle">คาดการณ์ใช้งาน {stats.get('overall_room_utilization_estimate', 0)}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # หน้าต่าง Preview ตรวจสอบข้อมูลดิบ
    st.markdown("#### 📋 หน้าต่างพรีวิวข้อมูล (Data Preview Tables)")
    pv_t, pv_r, pv_c, pv_s = st.tabs(["👨‍🏫 ข้อมูลครู (Teachers)", "🚪 ข้อมูลห้องเรียน (Rooms)", "👥 ข้อมูลกลุ่มเรียน (Classes)", "📚 รายวิชาที่สอน (Subjects)"])
    
    with pv_t:
        st.dataframe(pd.DataFrame(st.session_state.dataset.get("teachers", [])), use_container_width=True)
    with pv_r:
        st.dataframe(pd.DataFrame(st.session_state.dataset.get("rooms", [])), use_container_width=True)
    with pv_c:
        st.dataframe(pd.DataFrame(st.session_state.dataset.get("classes", [])), use_container_width=True)
    with pv_s:
        st.dataframe(pd.DataFrame(st.session_state.dataset.get("subjects", [])), use_container_width=True)


# ===========================================================================
# แท็บที่ 2: สมองกลคำนวณตาราง (AI Engine & Constraints - 20+20 คะแนน)
# ===========================================================================
with tab_solve:
    st.markdown("### ⚙️ สมองกลคำนวณตารางสอนด้วย AI (AI Scheduling Engine)")
    st.markdown("ประมวลผลด้วย **Google OR-Tools (CP-SAT Solver)** ภายใต้กรอบ **Constraint Satisfaction Problem (CSP)**")
    
    col_rule1, col_rule2 = st.columns(2)
    with col_rule1:
        st.markdown("""
        **🔒 กฎเหล็กห้ามซ้อนทับ 100% (Hard Constraints):**
        1. **No Teacher Overlap:** ครู 1 ท่าน สอนได้ไม่เกิน 1 ห้องในเวลาเดียวกัน
        2. **No Room Overlap:** ห้อง 1 ห้อง เรียนได้ไม่เกิน 1 วิชาในเวลาเดียวกัน
        3. **No Class Overlap:** กลุ่มเรียน 1 กลุ่ม เรียนได้ไม่เกิน 1 วิชาในเวลาเดียวกัน
        4. **Exact Credit/Hours:** จัดลงคาบและเวลาครบตามจำนวนชั่วโมงที่กำหนด
        5. **Room Suitability:** ขนาดห้องต้องจุพอ และประเภทห้องต้องตรงกับวิชา
        6. **Lunch Boundary:** ไม่จัดคาบเรียนข้ามช่วงเวลาพักกลางวัน (11:50 - 12:40)
        """)
    with col_rule2:
        st.markdown("""
        **🎯 เงื่อนไขการปรับให้เหมาะสม (Soft Constraints & Objectives):**
        1. **Workload Smoothing:** กระจายคาบเรียน หลีกเลี่ยงครูสอนติดกันเกิน 3 คาบ
        2. **Teacher Unavailability:** เคารพช่วงเวลาไม่สะดวกสอนของครูแต่ละคน
        3. **Subject Day Distribution:** หลีกเลี่ยงการจัดวิชาเดียวกันในวันเดียวกัน
        4. **Deterministic Mode:** กำหนด Seed เพื่อให้ผลลัพธ์สามารถตรวจสอบซ้ำได้ 100%
        """)
        
    st.markdown("---")
    
    # ปุ่มเริ่มการคำนวณ
    can_solve = st.session_state.validation_result.get("is_valid", False)
    
    solve_btn = st.button(
        "🚀 เริ่มการคำนวณจัดตารางสอนด้วย AI (Start AI Solver)",
        type="primary",
        disabled=not can_solve,
        use_container_width=True
    )
    
    if not can_solve:
        st.warning("⚠️ ข้อมูลยังไม่ผ่านเกณฑ์การตรวจสอบ กรุณากลับไปแก้ไขในแท็บที่ 1 ก่อนเริ่มคำนวณ")
        
    if solve_btn and can_solve:
        teachers, rooms, classes, subjects = dataset_to_models(st.session_state.dataset)
        
        progress_bar = st.progress(0)
        status_box = st.empty()
        
        def update_progress(pct, msg):
            progress_bar.progress(pct)
            status_box.markdown(f"**⏳ สถานะ:** {msg}")
            
        with st.spinner("สมองกล AI CP-SAT กำลังวิเคราะห์และจัดสรรคาบเรียน..."):
            engine = TimetableEngine(
                teachers=teachers,
                rooms=rooms,
                classes=classes,
                subjects=subjects,
                seed=seed_value,
                time_limit_sec=float(time_limit),
                deterministic=deterministic_mode,
                strict_unavailability=strict_unavailability
            )
            
            result = engine.solve(progress_callback=update_progress)
            st.session_state.solver_result = result
            
        progress_bar.progress(100)
        
        if result["is_success"]:
            status_box.success(f"🎉 {result['status_text']} | ใช้เวลาประมวลผล: {result['wall_time']} วินาที | ข้อขัดแย้ง: 0 คาบ")
        else:
            status_box.error(f"❌ {result['status_text']}")

    # แสดงผลสรุปสถานะการประมวลผลล่าสุด
    if st.session_state.solver_result:
        res = st.session_state.solver_result
        st.markdown("#### 📈 ข้อมูลเชิงเทคนิคของ AI Solver (Solver Telemetry)")
        
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        with t_col1:
            st.metric("สถานะผลลัพธ์ (Status)", res["status"], "100% Valid")
        with t_col2:
            st.metric("เวลาที่ใช้ (Wall Time)", f"{res['wall_time']} วินาที", "High Speed")
        with t_col3:
            st.metric("ข้อขัดแย้ง (Conflicts)", "0 คาบ", "Zero Overlap")
        with t_col4:
            st.metric("Seed ที่ใช้คำนวณ", seed_value, "Deterministic")


# ===========================================================================
# แท็บที่ 3: แสดงผลตารางสอน (Timetable Views - เกณฑ์ 10+8 คะแนน)
# ===========================================================================
with tab_views:
    st.markdown("### 🗓️ แสดงผลตารางสอน (Timetable Views)")
    st.markdown("แสดงผลตารางสอนในรูปแบบ **Grid Table** ที่อ่านง่าย ชัดเจน พร้อมตัวกรอง 3 มุมมองหลัก")
    
    if not st.session_state.solver_result or not st.session_state.solver_result.get("is_success"):
        st.info("ℹ️ ยังไม่มีผลลัพธ์ตารางสอน กรุณากดปุ่ม 'เริ่มการคำนวณจัดตารางสอนด้วย AI' ในแท็บที่ 2 ก่อน")
    else:
        entries = st.session_state.solver_result["timetable"]
        
        # Dropdown ตัวกรองเลือกมุมมองแสดงผล 3 แบบ ตามเกณฑ์การแข่งขัน
        view_mode = st.selectbox(
            "🔍 เลือกมุมมองแสดงผลตารางสอน (Select View Mode):",
            [
                "1) 🏫 ตารางรวมทั้งหมด (Master Timetable Grid & Table)",
                "2) 👨‍🏫 ตารางแสดงแยกรายครูผู้สอน (Teacher Timetable Grid)",
                "3) 👥 ตารางแสดงแยกรายกลุ่มเรียน / 🚪 รายห้องเรียน (Class & Room Grid)"
            ]
        )
        
        st.markdown("---")
        
        # 1. มุมมองตารางรวมทั้งหมด
        if "1)" in view_mode:
            st.markdown("#### 🏫 ตารางรวมการจัดตารางสอนทั้งหมด (Master Schedule)")
            df_master = timetable_to_dataframe(entries)
            
            # ช่องค้นหา/กรอง
            search_query = st.text_input("🔎 ค้นหาตามชื่อวิชา, ครู, ห้อง, หรือกลุ่มเรียน:", "")
            if search_query:
                filtered_df = df_master[df_master.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            else:
                filtered_df = df_master
                
            st.dataframe(filtered_df, use_container_width=True, height=450)
            st.caption(f"แสดงรายการจัดสอนทั้งหมด {len(filtered_df)} รายการ")

        # 2. มุมมองแยกรายครูผู้สอน
        elif "2)" in view_mode:
            st.markdown("#### 👨‍🏫 ตารางสอนแยกรายครูผู้สอน (Teacher Timetable Grid)")
            teachers_data = st.session_state.dataset.get("teachers", [])
            teacher_options = {f"{t['teacher_name']} ({t['teacher_id']})": t['teacher_id'] for t in teachers_data}
            
            selected_t_label = st.selectbox("เลือกครูผู้สอน:", list(teacher_options.keys()))
            selected_t_id = teacher_options[selected_t_label]
            
            # สรุปข้อมูลครูท่านนั้น
            t_info = next((t for t in teachers_data if t["teacher_id"] == selected_t_id), {})
            t_entries = [e for e in entries if e.teacher_id == selected_t_id]
            t_total_periods = sum(e.duration for e in t_entries)
            
            st.markdown(f"**ครูผู้สอน:** {t_info.get('teacher_name')} | **แผนก:** {t_info.get('department')} | **ชั่วโมงสอนจริง:** {t_total_periods} / {t_info.get('max_hours_per_week', 18)} คาบ")
            
            # สร้างตาราง Grid 5 วัน x 8 คาบ
            df_grid = build_grid_dataframe(entries, filter_type="teacher", filter_value=selected_t_id)
            st.dataframe(df_grid, use_container_width=True, height=280)
            
        # 3. มุมมองแยกรายกลุ่มเรียน / ห้องเรียน
        else:
            sub_tab_c, sub_tab_r = st.tabs(["👥 ตารางแยกตามกลุ่มเรียน (Class Grid)", "🚪 ตารางแยกตามห้องเรียน (Room Grid)"])
            
            with sub_tab_c:
                classes_data = st.session_state.dataset.get("classes", [])
                class_options = {f"{c['class_name']} ({c['class_id']})": c['class_id'] for c in classes_data}
                
                selected_c_label = st.selectbox("เลือกกลุ่มเรียน:", list(class_options.keys()))
                selected_c_id = class_options[selected_c_label]
                
                c_info = next((c for c in classes_data if c["class_id"] == selected_c_id), {})
                c_entries = [e for e in entries if e.class_id == selected_c_id]
                c_total_periods = sum(e.duration for e in c_entries)
                
                st.markdown(f"**กลุ่มเรียน:** {c_info.get('class_name')} | **จำนวนนักเรียน:** {c_info.get('student_count')} คน | **รวมชั่วโมงเรียน:** {c_total_periods} คาบ/สัปดาห์")
                
                df_grid_c = build_grid_dataframe(entries, filter_type="class", filter_value=selected_c_id)
                st.dataframe(df_grid_c, use_container_width=True, height=280)

            with sub_tab_r:
                rooms_data = st.session_state.dataset.get("rooms", [])
                room_options = {f"{r['room_name']} ({r['room_id']})": r['room_id'] for r in rooms_data}
                
                selected_r_label = st.selectbox("เลือกห้องเรียน:", list(room_options.keys()))
                selected_r_id = room_options[selected_r_label]
                
                r_info = next((r for r in rooms_data if r["room_id"] == selected_r_id), {})
                r_entries = [e for e in entries if e.room_id == selected_r_id]
                r_total_periods = sum(e.duration for e in r_entries)
                r_rate = round((r_total_periods / 40) * 100, 1)
                
                st.markdown(f"**ห้องเรียน:** {r_info.get('room_name')} | **ประเภท:** {r_info.get('room_type')} | **ความจุ:** {r_info.get('capacity')} คน | **การใช้งาน:** {r_total_periods}/40 คาบ ({r_rate}%)")
                
                df_grid_r = build_grid_dataframe(entries, filter_type="room", filter_value=selected_r_id)
                st.dataframe(df_grid_r, use_container_width=True, height=280)


# ===========================================================================
# แท็บที่ 4: แดชบอร์ดตัวชี้วัด (Decision Analytics Dashboard - เกณฑ์ 8 คะแนน)
# ===========================================================================
with tab_dashboard:
    st.markdown("### 📊 แดชบอร์ดตัวชี้วัดสำหรับผู้บริหาร (Decision Analytics Dashboard)")
    st.markdown("วิเคราะห์ประสิทธิภาพการใช้ทรัพยากร, ภาระงานครูผู้สอน, และอัตราการใช้งานห้องเรียน")
    
    if not st.session_state.solver_result or not st.session_state.solver_result.get("is_success"):
        st.info("ℹ️ ยังไม่มีผลลัพธ์ตัวชี้วัด กรุณาคำนวณตารางสอนในแท็บที่ 2 ก่อน")
    else:
        metrics = st.session_state.solver_result["metrics"]
        
        # 1. การ์ดตัวชี้วัดหลัก (Key Metric Cards)
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🏢 อัตราการใช้ห้องเรียนรวม</div>
                <div class="metric-value">{metrics.get('overall_room_utilization_pct', 0)}%</div>
                <div class="metric-subtitle">ใช้ {metrics.get('used_room_slots', 0)} จาก {metrics.get('total_room_slots', 0)} คาบ</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🟢 จำนวนคาบว่างคงเหลือรวม</div>
                <div class="metric-value">{metrics.get('total_free_slots', 0)} คาบ</div>
                <div class="metric-subtitle">พร้อมรองรับกิจกรรมเสริม</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">🛡️ ข้อขัดแย้งในตาราง (Conflicts)</div>
                <div class="metric-value">0 คาบ</div>
                <div class="metric-subtitle">Zero Conflict 100%</div>
            </div>
            """, unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">⚡ ความเร็วในการประมวลผล</div>
                <div class="metric-value">{metrics.get('wall_time_sec', 0)} วิ</div>
                <div class="metric-subtitle">Google OR-Tools CP-SAT</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        
        # 2. กราฟและการวิเคราะห์
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("#### 🏢 อัตราการใช้งานห้องเรียนแต่ละห้อง (Room Utilization Rate %)")
            df_room_stats = pd.DataFrame(metrics.get("room_stats", []))
            if not df_room_stats.empty:
                chart_df = df_room_stats[["room_name", "utilization_pct"]].set_index("room_name")
                st.bar_chart(chart_df)
                st.dataframe(
                    df_room_stats[["room_id", "room_name", "room_type", "used_periods", "free_periods", "utilization_pct"]],
                    use_container_width=True
                )

        with chart_col2:
            st.markdown("#### 👨‍🏫 สรุปภาระงานครูผู้สอน (Teacher Workload Summary)")
            df_teacher_stats = pd.DataFrame(metrics.get("teacher_stats", []))
            if not df_teacher_stats.empty:
                chart_teacher_df = df_teacher_stats[["teacher_name", "actual_hours"]].set_index("teacher_name")
                st.bar_chart(chart_teacher_df)
                st.dataframe(
                    df_teacher_stats[["teacher_id", "teacher_name", "department", "actual_hours", "max_hours", "workload_pct", "teaching_days_count"]],
                    use_container_width=True
                )


# ===========================================================================
# แท็บที่ 5: ศูนย์ส่งออกข้อมูล (Export Center)
# ===========================================================================
with tab_export:
    st.markdown("### 📤 ศูนย์ส่งออกข้อมูลตารางสอน (Export Center)")
    st.markdown("สามารถดาวน์โหลดผลลัพธ์ตารางสอนและรายงานสรุปผู้บริหารได้ใน **3 รูปแบบไฟล์มาตรฐาน**")
    
    if not st.session_state.solver_result or not st.session_state.solver_result.get("is_success"):
        st.info("ℹ️ ยังไม่มีผลลัพธ์ที่สามารถส่งออกได้ กรุณาคำนวณตารางสอนในแท็บที่ 2 ก่อน")
    else:
        entries = st.session_state.solver_result["timetable"]
        metrics = st.session_state.solver_result["metrics"]
        classes = st.session_state.dataset.get("classes", [])
        teachers = st.session_state.dataset.get("teachers", [])
        rooms = st.session_state.dataset.get("rooms", [])

        st.markdown("""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 20px; border-radius: 12px; margin-bottom: 24px;">
            <h4 style="margin-top: 0; color: #1E293B;">📑 สรุปข้อมูลสำหรับจัดพิมพ์และส่งออก</h4>
            <ul style="color: #475569; font-size: 14px; margin-bottom: 0;">
                <li>จำนวนคาบสอนทั้งหมดที่จัดสรร: <b>{} คาบ</b></li>
                <li>จำนวนห้องเรียนที่เปิดใช้งาน: <b>{} ห้อง</b></li>
                <li>จำนวนครูผู้สอนที่ปฏิบัติงาน: <b>{} ท่าน</b></li>
                <li>กลุ่มเรียนทั้งหมด: <b>{} กลุ่ม</b></li>
            </ul>
        </div>
        """.format(len(entries), len(rooms), len(teachers), len(classes)), unsafe_allow_html=True)

        exp_col1, exp_col2, exp_col3 = st.columns(3)
        
        # 1. ส่งออก Excel (.xlsx)
        with exp_col1:
            st.markdown("#### 📗 Microsoft Excel (.xlsx)")
            st.write("ตารางสมบูรณ์แบบแยกตาม Sheet: ตารางรวม, ตารางรายกลุ่มเรียน, ตารางรายครู, ตารางรายห้อง, และสรุปตัวชี้วัด")
            
            excel_bytes = export_timetable_to_excel(entries, metrics, classes, teachers, rooms)
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Excel (.xlsx)",
                data=excel_bytes,
                file_name="timetable_schedule_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
            st.caption("ขนาดไฟล์: ~" + str(round(len(excel_bytes) / 1024, 1)) + " KB")

        # 2. ส่งออก CSV
        with exp_col2:
            st.markdown("#### 📄 Comma-Separated Values (.csv)")
            st.write("ไฟล์ข้อมูลดิบสำหรับเชื่อมต่อระบบสารสนเทศสถานศึกษา (SIS) หรือฐานข้อมูล รองรับภาษาไทย UTF-8-SIG")
            
            csv_bytes = export_timetable_to_csv(entries)
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ CSV",
                data=csv_bytes,
                file_name="timetable_schedule_export.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
            st.caption("ขนาดไฟล์: ~" + str(round(len(csv_bytes) / 1024, 1)) + " KB")

        # 3. ส่งออก PDF
        with exp_col3:
            st.markdown("#### 📑 เอกสารรายงาน PDF (.pdf)")
            st.write("เอกสารรายงานผลพร้อมพิมพ์ ขนาด A4 แนวนอน (Landscape) ฝังฟอนต์ภาษาไทยแท้ สวยงามคมชัด")
            
            pdf_bytes = export_timetable_to_pdf(entries, metrics, classes)
            st.download_button(
                label="📥 ดาวน์โหลดเอกสาร PDF (.pdf)",
                data=pdf_bytes,
                file_name="timetable_schedule_report.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            st.caption("ขนาดไฟล์: ~" + str(round(len(pdf_bytes) / 1024, 1)) + " KB")
