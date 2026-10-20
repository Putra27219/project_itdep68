"""
=============================================================================
ระบบจัดตารางสอนอัตโนมัติด้วย AI (Automated Timetable Scheduling System)
โมดูล: models.py - โครงสร้างข้อมูลพื้นฐาน (Data Models & Constants)
=============================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

# ---------------------------------------------------------------------------
# นิยามค่าคงที่ของวันและคาบเวลาในสัปดาห์ (วันจันทร์ - ศุกร์, 8 คาบ/วัน)
# ---------------------------------------------------------------------------
DAYS = [
    {"index": 0, "code": "MON", "name_th": "วันจันทร์", "name_en": "Monday"},
    {"index": 1, "code": "TUE", "name_th": "วันอังคาร", "name_en": "Tuesday"},
    {"index": 2, "code": "WED", "name_th": "วันพุธ", "name_en": "Wednesday"},
    {"index": 3, "code": "THU", "name_th": "วันพฤหัสบดี", "name_en": "Thursday"},
    {"index": 4, "code": "FRI", "name_th": "วันศุกร์", "name_en": "Friday"}
]

DAY_NAMES_TH = [d["name_th"] for d in DAYS]
DAY_CODES = [d["code"] for d in DAYS]

# คาบเรียน: 8 คาบต่อวัน (ช่วงเช้า 4 คาบ, พักกลางวัน, ช่วงบ่าย 4 คาบ)
PERIODS = [
    {"index": 0, "period_num": 1, "time_range": "08:30 - 09:20", "session": "morning"},
    {"index": 1, "period_num": 2, "time_range": "09:20 - 10:10", "session": "morning"},
    {"index": 2, "period_num": 3, "time_range": "10:10 - 11:00", "session": "morning"},
    {"index": 3, "period_num": 4, "time_range": "11:00 - 11:50", "session": "morning"},
    # พักกลางวัน: 11:50 - 12:40 (ไม่มีการจัดคาบสอนข้ามช่วงนี้)
    {"index": 4, "period_num": 5, "time_range": "12:40 - 13:30", "session": "afternoon"},
    {"index": 5, "period_num": 6, "time_range": "13:30 - 14:20", "session": "afternoon"},
    {"index": 6, "period_num": 7, "time_range": "14:20 - 15:10", "session": "afternoon"},
    {"index": 7, "period_num": 8, "time_range": "15:10 - 16:00", "session": "afternoon"},
]

PERIOD_NAMES = [f"คาบ {p['period_num']} ({p['time_range']})" for p in PERIODS]
MORNING_PERIODS = [0, 1, 2, 3]
AFTERNOON_PERIODS = [4, 5, 6, 7]
TOTAL_PERIODS_PER_DAY = len(PERIODS)
TOTAL_DAYS = len(DAYS)
TOTAL_SLOTS_PER_WEEK = TOTAL_DAYS * TOTAL_PERIODS_PER_DAY  # 40 คาบ/สัปดาห์


@dataclass
class Teacher:
    """ข้อมูลครูผู้สอน"""
    teacher_id: str                          # รหัสครู เช่น T01
    teacher_name: str                        # ชื่อ-นามสกุลครู
    department: str = "สามัญสัมพันธ์"         # แผนกวิชา
    max_hours_per_week: int = 18             # จำนวนคาบสูงสุดที่สอนได้ต่อสัปดาห์
    unavailable_slots: List[Dict[str, int]] = field(default_factory=list)
    # unavailable_slots เช่น [{"day": 0, "period": 0}, {"day": 2, "period": 7}]


@dataclass
class Room:
    """ข้อมูลห้องเรียน"""
    room_id: str                             # รหัสห้อง เช่น LAB-101
    room_name: str                           # ชื่อห้อง เช่น ห้องปฏิบัติการคอมพิวเตอร์ 1
    room_type: str = "ห้องเรียนทฤษฎี"         # ประเภทห้อง: ห้องเรียนทฤษฎี, ห้องปฏิบัติการคอมพิวเตอร์, โรงฝึกงาน
    capacity: int = 40                       # ความจุผู้เรียนสูงสุด (คน)
    building: str = "อาคารเรียนรวม"           # อาคารที่ตั้ง


@dataclass
class StudentClass:
    """ข้อมูลกลุ่มเรียน / ห้องนักเรียน"""
    class_id: str                            # รหัสกลุ่มเรียน เช่น IT-101
    class_name: str                          # ชื่อกลุ่มเรียน เช่น ปวช.1 เทคโนโลยีสารสนเทศ 1
    student_count: int = 30                  # จำนวนนักเรียนในกลุ่ม (คน)
    department: str = "เทคโนโลยีสารสนเทศ"    # แผนกวิชา


@dataclass
class SubjectAssignment:
    """ข้อมูลรายวิชาและการมอบหมายงานสอน (Curriculum Teaching Assignment)"""
    subject_id: str                          # รหัสวิชา เช่น 30204-2001
    subject_name: str                        # ชื่อวิชา เช่น การเขียนโปรแกรมเชิงวัตถุ
    teacher_id: str                          # รหัสครูผู้สอนที่รับผิดชอบ
    class_id: str                            # รหัสกลุ่มเรียนที่ลงทะเบียนเรียน
    room_type_required: str = "ห้องเรียนทฤษฎี"# ประเภทห้องที่จำเป็นต้องใช้
    periods_per_week: int = 2                # จำนวนคาบต่อสัปดาห์
    block_size: int = 2                      # คาบติดต่อกันต่อครั้ง (เช่น 2 คาบติดกัน หรือ 1 คาบ)
    preferred_room_id: Optional[str] = None  # รหัสห้องเรียนที่เจาะจง (ถ้ามี)
    credit: int = 2                          # จำนวนหน่วยกิต


@dataclass
class TimetableEntry:
    """ผลลัพธ์การจัดคาบเรียนแต่ละคาบ (Single Scheduled Period Unit)"""
    session_id: str
    subject_id: str
    subject_name: str
    teacher_id: str
    teacher_name: str
    class_id: str
    class_name: str
    room_id: str
    room_name: str
    day_index: int                           # 0..4 (วันจันทร์..ศุกร์)
    day_name: str
    start_period: int                        # คาบเริ่มต้น (0..7)
    duration: int                            # ความยาว (จำนวนคาบ)
    occupied_periods: List[int]              # คาบที่ครอบครอง เช่น [0, 1]
    time_range: str                          # ช่วงเวลา เช่น 08:30 - 10:10
