"""
=============================================================================
ระบบจัดตารางสอนอัตโนมัติด้วย AI (Automated Timetable Scheduling System)
โมดูล: data_manager.py - ระบบนำเข้า, ตรวจสอบ (Validation) และสร้างข้อมูลตัวอย่าง
=============================================================================
"""

import json
import io
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from models import (
    Teacher, Room, StudentClass, SubjectAssignment,
    DAYS, PERIODS, TOTAL_SLOTS_PER_WEEK
)


# ---------------------------------------------------------------------------
# 1. ระบบสร้างชุดข้อมูลตัวอย่าง (Sample Datasets: Small / Medium / Large)
# ---------------------------------------------------------------------------

def generate_sample_dataset(size: str = "medium") -> Dict[str, Any]:
    """
    สร้างชุดข้อมูลจำลองตามมาตรฐานสถานศึกษาอาชีวศึกษาไทย
    รองรับ 3 ขนาด:
      - 'small' : ขนาดเล็ก (สำหรับทดสอบเบื้องต้นและสาธิตการทำงานแบบรวดเร็ว)
      - 'medium': ขนาดกลาง (ขนาดมาตรฐานสำหรับ 1 แผนกวิชา)
      - 'large' : ขนาดใหญ่ (ขนาดโรงเรียน/วิทยาลัยเต็มรูปแบบ หลายแผนกวิชา)
    """
    size = size.lower()
    
    if size == "small":
        # ขนาดเล็ก: ครู 4 คน, ห้อง 3 ห้อง, กลุ่มเรียน 2 กลุ่ม, 6 วิชา (14 คาบ)
        teachers = [
            {"teacher_id": "T01", "teacher_name": "อ.สมศักดิ์ รักการสอน", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": [{"day": 0, "period": 0}]},
            {"teacher_id": "T02", "teacher_name": "อ.กัญญา โค้ดดิ้ง", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": [{"day": 4, "period": 7}]},
            {"teacher_id": "T03", "teacher_name": "อ.วิภา ภาษาพาที", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": []},
            {"teacher_id": "T04", "teacher_name": "อ.ธีรพล คณิตคิดเร็ว", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": [{"day": 2, "period": 4}]}
        ]
        
        rooms = [
            {"room_id": "LAB-101", "room_name": "ห้องปฏิบัติการคอมพิวเตอร์ 1", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 35, "building": "อาคาร 1 ชั้น 2"},
            {"room_id": "REC-201", "room_name": "ห้องเรียนทฤษฎี 201", "room_type": "ห้องเรียนทฤษฎี", "capacity": 40, "building": "อาคาร 2 ชั้น 2"},
            {"room_id": "REC-202", "room_name": "ห้องเรียนทฤษฎี 202", "room_type": "ห้องเรียนทฤษฎี", "capacity": 35, "building": "อาคาร 2 ชั้น 2"}
        ]
        
        classes = [
            {"class_id": "IT-101", "class_name": "ปวช.1 เทคโนโลยีสารสนเทศ 1", "student_count": 28, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "IT-201", "class_name": "ปวช.2 เทคโนโลยีสารสนเทศ 1", "student_count": 25, "department": "เทคโนโลยีสารสนเทศ"}
        ]
        
        subjects = [
            {"subject_id": "20001-1001", "subject_name": "ภาษาไทยพื้นฐาน", "teacher_id": "T03", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20001-2001", "subject_name": "คณิตศาสตร์พื้นฐานอาชีพ", "teacher_id": "T04", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20204-2001", "subject_name": "การเขียนโปรแกรมคอมพิวเตอร์", "teacher_id": "T01", "class_id": "IT-101", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-1002", "subject_name": "ภาษาอังกฤษเพื่อการสื่อสาร", "teacher_id": "T03", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20204-2004", "subject_name": "ระบบฐานข้อมูลเชิงสัมพันธ์", "teacher_id": "T02", "class_id": "IT-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-2002", "subject_name": "สถิติและการประยุกต์", "teacher_id": "T04", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2}
        ]

    elif size == "large":
        # ขนาดใหญ่: ครู 16 คน, ห้อง 10 ห้อง, กลุ่มเรียน 8 กลุ่ม, 36 วิชา (82 คาบ)
        teachers = [
            {"teacher_id": "T01", "teacher_name": "ดร.สมศักดิ์ รักการสอน", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 18, "unavailable_slots": [{"day": 0, "period": 0}, {"day": 0, "period": 1}]},
            {"teacher_id": "T02", "teacher_name": "อ.กัญญา โค้ดดิ้ง", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 18, "unavailable_slots": [{"day": 4, "period": 6}, {"day": 4, "period": 7}]},
            {"teacher_id": "T03", "teacher_name": "อ.วิภา ภาษาพาที", "department": "สามัญสัมพันธ์", "max_hours_per_week": 16, "unavailable_slots": [{"day": 2, "period": 0}]},
            {"teacher_id": "T04", "teacher_name": "อ.ธีรพล คณิตคิดเร็ว", "department": "สามัญสัมพันธ์", "max_hours_per_week": 16, "unavailable_slots": []},
            {"teacher_id": "T05", "teacher_name": "อ.ประวิทย์ เน็ตเวิร์ก", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 18, "unavailable_slots": [{"day": 1, "period": 2}]},
            {"teacher_id": "T06", "teacher_name": "อ.ดาริน การบัญชี", "department": "การบัญชี", "max_hours_per_week": 18, "unavailable_slots": []},
            {"teacher_id": "T07", "teacher_name": "อ.ชลิต ภาษีอากร", "department": "การบัญชี", "max_hours_per_week": 16, "unavailable_slots": [{"day": 3, "period": 5}]},
            {"teacher_id": "T08", "teacher_name": "อ.จินตนา การตลาดดิจิทัล", "department": "การตลาด", "max_hours_per_week": 16, "unavailable_slots": []},
            {"teacher_id": "T09", "teacher_name": "อ.ศิริพร วิทยาศาสตร์", "department": "สามัญสัมพันธ์", "max_hours_per_week": 16, "unavailable_slots": []},
            {"teacher_id": "T10", "teacher_name": "อ.บรรเจิด ช่างยนต์", "department": "ช่างยนต์", "max_hours_per_week": 20, "unavailable_slots": [{"day": 0, "period": 4}]},
            {"teacher_id": "T11", "teacher_name": "อ.สุเทพ ไฟฟ้ากำลัง", "department": "ช่างไฟฟ้า", "max_hours_per_week": 18, "unavailable_slots": []},
            {"teacher_id": "T12", "teacher_name": "อ.อัญชลี ศิลปวัฒนธรรม", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": []},
            {"teacher_id": "T13", "teacher_name": "อ.ณัฐพล ปัญญาประดิษฐ์", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 18, "unavailable_slots": [{"day": 2, "period": 6}]},
            {"teacher_id": "T14", "teacher_name": "อ.กมลวรรณ การเงินธุรกิจ", "department": "การบัญชี", "max_hours_per_week": 16, "unavailable_slots": []},
            {"teacher_id": "T15", "teacher_name": "อ.พงศ์ธร เขียนแบบวิศวกรรม", "department": "ช่างยนต์", "max_hours_per_week": 18, "unavailable_slots": []},
            {"teacher_id": "T16", "teacher_name": "อ.นภาพร กราฟิกดีไซน์", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": []}
        ]
        
        rooms = [
            {"room_id": "LAB-101", "room_name": "ห้องปฏิบัติการคอมพิวเตอร์ 1", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 40, "building": "อาคารวิทยบริการ"},
            {"room_id": "LAB-102", "room_name": "ห้องปฏิบัติการคอมพิวเตอร์ 2", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 40, "building": "อาคารวิทยบริการ"},
            {"room_id": "LAB-103", "room_name": "ห้องปฏิบัติการปัญญาประดิษฐ์", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 35, "building": "อาคารวิทยบริการ"},
            {"room_id": "REC-201", "room_name": "ห้องเรียนทฤษฎี 201", "room_type": "ห้องเรียนทฤษฎี", "capacity": 45, "building": "อาคารเฉลิมพระเกียรติ"},
            {"room_id": "REC-202", "room_name": "ห้องเรียนทฤษฎี 202", "room_type": "ห้องเรียนทฤษฎี", "capacity": 45, "building": "อาคารเฉลิมพระเกียรติ"},
            {"room_id": "REC-203", "room_name": "ห้องเรียนทฤษฎี 203", "room_type": "ห้องเรียนทฤษฎี", "capacity": 40, "building": "อาคารเฉลิมพระเกียรติ"},
            {"room_id": "REC-204", "room_name": "ห้องเรียนทฤษฎี 204", "room_type": "ห้องเรียนทฤษฎี", "capacity": 40, "building": "อาคารเฉลิมพระเกียรติ"},
            {"room_id": "WK-AUTO", "room_name": "โรงฝึกงานช่างยนต์ 1", "room_type": "โรงฝึกงานช่าง", "capacity": 35, "building": "อาคารปฏิบัติการช่าง"},
            {"room_id": "WK-ELEC", "room_name": "โรงฝึกงานช่างไฟฟ้า", "room_type": "โรงฝึกงานช่าง", "capacity": 35, "building": "อาคารปฏิบัติการช่าง"},
            {"room_id": "ACT-301", "room_name": "ห้องปฏิบัติการบัญชีจำลอง", "room_type": "ห้องเรียนทฤษฎี", "capacity": 40, "building": "อาคารพาณิชยการ"}
        ]
        
        classes = [
            {"class_id": "IT-101", "class_name": "ปวช.1 เทคโนโลยีสารสนเทศ 1", "student_count": 30, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "IT-201", "class_name": "ปวช.2 เทคโนโลยีสารสนเทศ 1", "student_count": 28, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "IT-301", "class_name": "ปวช.3 เทคโนโลยีสารสนเทศ 1", "student_count": 26, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "ACC-101", "class_name": "ปวช.1 การบัญชี 1", "student_count": 32, "department": "การบัญชี"},
            {"class_id": "ACC-201", "class_name": "ปวช.2 การบัญชี 1", "student_count": 29, "department": "การบัญชี"},
            {"class_id": "MKT-101", "class_name": "ปวช.1 การตลาด 1", "student_count": 27, "department": "การตลาด"},
            {"class_id": "AUTO-101", "class_name": "ปวช.1 ช่างยนต์ 1", "student_count": 30, "department": "ช่างยนต์"},
            {"class_id": "ELEC-101", "class_name": "ปวช.1 ช่างไฟฟ้ากำลัง 1", "student_count": 28, "department": "ช่างไฟฟ้า"}
        ]
        
        subjects = [
            # IT-101
            {"subject_id": "SUB-IT1-01", "subject_name": "ภาษาไทยพื้นฐาน", "teacher_id": "T03", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-IT1-02", "subject_name": "คณิตศาสตร์ประยุกต์ 1", "teacher_id": "T04", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-IT1-03", "subject_name": "การเขียนโปรแกรมเบื้องต้น", "teacher_id": "T01", "class_id": "IT-101", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-IT1-04", "subject_name": "วิทยาศาสตร์เพื่องานอาชีพ", "teacher_id": "T09", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-IT1-05", "subject_name": "กราฟิกดีไซน์พื้นฐาน", "teacher_id": "T16", "class_id": "IT-101", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 2, "block_size": 2, "credit": 2},
            # IT-201
            {"subject_id": "SUB-IT2-01", "subject_name": "ระบบฐานข้อมูลเชิงสัมพันธ์", "teacher_id": "T02", "class_id": "IT-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-IT2-02", "subject_name": "ระบบเครือข่ายเบื้องต้น", "teacher_id": "T05", "class_id": "IT-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-IT2-03", "subject_name": "ภาษาอังกฤษธุรกิจ", "teacher_id": "T03", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-IT2-04", "subject_name": "สถิติประยุกต์ธุรกิจ", "teacher_id": "T04", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            # IT-301
            {"subject_id": "SUB-IT3-01", "subject_name": "ปัญญาประดิษฐ์ประยุกต์", "teacher_id": "T13", "class_id": "IT-301", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-IT3-02", "subject_name": "การพัฒนาเว็บแอปพลิเคชัน", "teacher_id": "T02", "class_id": "IT-301", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-IT3-03", "subject_name": "โครงการวิชาชีพ IT", "teacher_id": "T01", "class_id": "IT-301", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 4, "block_size": 2, "credit": 3},
            # ACC-101
            {"subject_id": "SUB-AC1-01", "subject_name": "หลักการบัญชีเบื้องต้น 1", "teacher_id": "T06", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-AC1-02", "subject_name": "กฎหมายพาณิชย์", "teacher_id": "T07", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-AC1-03", "subject_name": "คณิตศาสตร์ประยุกต์ 1", "teacher_id": "T04", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-AC1-04", "subject_name": "ภาษาไทยพื้นฐาน", "teacher_id": "T03", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            # ACC-201
            {"subject_id": "SUB-AC2-01", "subject_name": "การบัญชีชั้นกลาง 1", "teacher_id": "T06", "class_id": "ACC-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-AC2-02", "subject_name": "ภาษีอากร 1", "teacher_id": "T07", "class_id": "ACC-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-AC2-03", "subject_name": "โปรแกรมสำเร็จรูปเพื่องานบัญชี", "teacher_id": "T14", "class_id": "ACC-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            # MKT-101
            {"subject_id": "SUB-MK1-01", "subject_name": "การตลาดเบื้องต้น", "teacher_id": "T08", "class_id": "MKT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "SUB-MK1-02", "subject_name": "การขายและการเจรจา", "teacher_id": "T08", "class_id": "MKT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-MK1-03", "subject_name": "ภาษาอังกฤษธุรกิจ", "teacher_id": "T03", "class_id": "MKT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            # AUTO-101
            {"subject_id": "SUB-AU1-01", "subject_name": "งานเครื่องยนต์แก๊สโซลีน", "teacher_id": "T10", "class_id": "AUTO-101", "room_type_required": "โรงฝึกงานช่าง", "periods_per_week": 4, "block_size": 4, "credit": 3},
            {"subject_id": "SUB-AU1-02", "subject_name": "เขียนแบบเทคนิคเบื้องต้น", "teacher_id": "T15", "class_id": "AUTO-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-AU1-03", "subject_name": "วิทยาศาสตร์เพื่องานอาชีพ", "teacher_id": "T09", "class_id": "AUTO-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            # ELEC-101
            {"subject_id": "SUB-EL1-01", "subject_name": "งานวงจรไฟฟ้ากระแสตรง", "teacher_id": "T11", "class_id": "ELEC-101", "room_type_required": "โรงฝึกงานช่าง", "periods_per_week": 4, "block_size": 4, "credit": 3},
            {"subject_id": "SUB-EL1-02", "subject_name": "เครื่องมือวัดและทดสอบไฟฟ้า", "teacher_id": "T11", "class_id": "ELEC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "SUB-EL1-03", "subject_name": "คณิตศาสตร์ประยุกต์ 1", "teacher_id": "T04", "class_id": "ELEC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2}
        ]

    else:
        # Default: 'medium' ขนาดกลาง (ครู 8 คน, ห้อง 6 ห้อง, กลุ่มเรียน 4 กลุ่ม, 16 วิชา - 37 คาบ)
        teachers = [
            {"teacher_id": "T01", "teacher_name": "ดร.สมศักดิ์ รักการสอน", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": [{"day": 0, "period": 0}, {"day": 0, "period": 1}]},
            {"teacher_id": "T02", "teacher_name": "อ.กัญญา โค้ดดิ้ง", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": [{"day": 4, "period": 6}, {"day": 4, "period": 7}]},
            {"teacher_id": "T03", "teacher_name": "อ.วิภา ภาษาพาที", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": [{"day": 2, "period": 0}]},
            {"teacher_id": "T04", "teacher_name": "อ.ธีรพล คณิตคิดเร็ว", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": []},
            {"teacher_id": "T05", "teacher_name": "อ.ประวิทย์ เน็ตเวิร์ก", "department": "เทคโนโลยีสารสนเทศ", "max_hours_per_week": 16, "unavailable_slots": [{"day": 1, "period": 2}]},
            {"teacher_id": "T06", "teacher_name": "อ.ดาริน การบัญชี", "department": "การบัญชี", "max_hours_per_week": 16, "unavailable_slots": []},
            {"teacher_id": "T07", "teacher_name": "อ.ชลิต ภาษีอากร", "department": "การบัญชี", "max_hours_per_week": 14, "unavailable_slots": [{"day": 3, "period": 5}]},
            {"teacher_id": "T08", "teacher_name": "อ.ศิริพร วิทยาศาสตร์", "department": "สามัญสัมพันธ์", "max_hours_per_week": 14, "unavailable_slots": []}
        ]
        
        rooms = [
            {"room_id": "LAB-101", "room_name": "ห้องปฏิบัติการคอมพิวเตอร์ 1", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 38, "building": "อาคารวิทยบริการ"},
            {"room_id": "LAB-102", "room_name": "ห้องปฏิบัติการคอมพิวเตอร์ 2", "room_type": "ห้องปฏิบัติการคอมพิวเตอร์", "capacity": 35, "building": "อาคารวิทยบริการ"},
            {"room_id": "REC-201", "room_name": "ห้องเรียนทฤษฎี 201", "room_type": "ห้องเรียนทฤษฎี", "capacity": 45, "building": "อาคาร 2 ชั้น 2"},
            {"room_id": "REC-202", "room_name": "ห้องเรียนทฤษฎี 202", "room_type": "ห้องเรียนทฤษฎี", "capacity": 40, "building": "อาคาร 2 ชั้น 2"},
            {"room_id": "REC-203", "room_name": "ห้องเรียนทฤษฎี 203", "room_type": "ห้องเรียนทฤษฎี", "capacity": 35, "building": "อาคาร 2 ชั้น 3"},
            {"room_id": "ACT-301", "room_name": "ห้องปฏิบัติการบัญชีจำลอง", "room_type": "ห้องเรียนทฤษฎี", "capacity": 35, "building": "อาคารพาณิชยการ"}
        ]
        
        classes = [
            {"class_id": "IT-101", "class_name": "ปวช.1 เทคโนโลยีสารสนเทศ 1", "student_count": 30, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "IT-201", "class_name": "ปวช.2 เทคโนโลยีสารสนเทศ 1", "student_count": 28, "department": "เทคโนโลยีสารสนเทศ"},
            {"class_id": "ACC-101", "class_name": "ปวช.1 การบัญชี 1", "student_count": 32, "department": "การบัญชี"},
            {"class_id": "ACC-201", "class_name": "ปวช.2 การบัญชี 1", "student_count": 27, "department": "การบัญชี"}
        ]
        
        subjects = [
            # IT-101 (รวม 10 คาบ)
            {"subject_id": "20001-1001", "subject_name": "ภาษาไทยพื้นฐาน", "teacher_id": "T03", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20001-2001", "subject_name": "คณิตศาสตร์พื้นฐานอาชีพ", "teacher_id": "T04", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20204-2001", "subject_name": "การเขียนโปรแกรมคอมพิวเตอร์", "teacher_id": "T01", "class_id": "IT-101", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-3001", "subject_name": "วิทยาศาสตร์เพื่องานอาชีพ", "teacher_id": "T08", "class_id": "IT-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            
            # IT-201 (รวม 10 คาบ)
            {"subject_id": "20001-1002", "subject_name": "ภาษาอังกฤษเพื่อการสื่อสาร", "teacher_id": "T03", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20204-2004", "subject_name": "ระบบฐานข้อมูลเชิงสัมพันธ์", "teacher_id": "T02", "class_id": "IT-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20204-2005", "subject_name": "ระบบเครือข่ายเบื้องต้น", "teacher_id": "T05", "class_id": "IT-201", "room_type_required": "ห้องปฏิบัติการคอมพิวเตอร์", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-2002", "subject_name": "สถิติและการประยุกต์", "teacher_id": "T04", "class_id": "IT-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            
            # ACC-101 (รวม 9 คาบ)
            {"subject_id": "20200-1001", "subject_name": "หลักการบัญชีเบื้องต้น 1", "teacher_id": "T06", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-1001b", "subject_name": "ภาษาไทยพื้นฐาน", "teacher_id": "T03", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20001-2001b", "subject_name": "คณิตศาสตร์พื้นฐานอาชีพ", "teacher_id": "T04", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            {"subject_id": "20200-1002", "subject_name": "กฎหมายพาณิชย์", "teacher_id": "T07", "class_id": "ACC-101", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2},
            
            # ACC-201 (รวม 8 คาบ)
            {"subject_id": "20200-2001", "subject_name": "การบัญชีชั้นกลาง 1", "teacher_id": "T06", "class_id": "ACC-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20200-2002", "subject_name": "ภาษีอากร 1", "teacher_id": "T07", "class_id": "ACC-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 3, "block_size": 3, "credit": 2},
            {"subject_id": "20001-1002b", "subject_name": "ภาษาอังกฤษเพื่อการสื่อสาร", "teacher_id": "T03", "class_id": "ACC-201", "room_type_required": "ห้องเรียนทฤษฎี", "periods_per_week": 2, "block_size": 2, "credit": 2}
        ]

    return {
        "teachers": teachers,
        "rooms": rooms,
        "classes": classes,
        "subjects": subjects
    }


# ---------------------------------------------------------------------------
# 2. ฟังก์ชันแปลงข้อมูล DataFrames / Dicts เป็น Object Models
# ---------------------------------------------------------------------------

def dataset_to_models(data: Dict[str, Any]) -> Tuple[List[Teacher], List[Room], List[StudentClass], List[SubjectAssignment]]:
    """แปลงข้อมูล dictionary เป็น Dataclass Object Models"""
    teachers = [Teacher(**item) for item in data.get("teachers", [])]
    rooms = [Room(**item) for item in data.get("rooms", [])]
    classes = [StudentClass(**item) for item in data.get("classes", [])]
    subjects = [SubjectAssignment(**item) for item in data.get("subjects", [])]
    return teachers, rooms, classes, subjects


# ---------------------------------------------------------------------------
# 3. ระบบ Validation ตรวจเช็คความถูกต้องของข้อมูล (เกณฑ์ 10 คะแนน)
# ---------------------------------------------------------------------------

def validate_timetable_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ระบบตรวจสอบความสมบูรณ์และความถูกต้องของข้อมูลนำเข้า
    ตรวจเช็คข้อกำหนดทั้งหมด:
      1) ตรวจหา ID ซ้ำ (Duplicate IDs)
      2) ตรวจหาค่าว่าง (Null / Missing / Empty Values)
      3) ตรวจสอบการอ้างอิงรหัส (Foreign Key References)
      4) ตรวจขนาดห้องไม่พอกับนักเรียน (Room Capacity vs Student Count)
      5) ตรวจครูสอนเกินคาบ (Teacher Overbooked)
      6) ตรวจสอบทรัพยากรห้องเรียนเทียบกับความต้องการ (Room Demand vs Supply)
    
    คืนค่า:
      - is_valid: bool (ผ่านเกณฑ์พร้อมคำนวณหรือไม่)
      - errors: List[str] (ข้อผิดพลาดร้ายแรงที่ต้องแก้ไขก่อนคำนวณ)
      - warnings: List[str] (ข้อสังเกตหรือคำเตือน)
      - stats: Dict[str, Any] (สรุปสถิติจำนวนและภาระงาน)
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    teachers_raw = data.get("teachers", [])
    rooms_raw = data.get("rooms", [])
    classes_raw = data.get("classes", [])
    subjects_raw = data.get("subjects", [])
    
    # 3.1 ตรวจสอบว่ามีข้อมูลครบทั้ง 4 ส่วนหรือไม่
    if not teachers_raw:
        errors.append("❌ ไม่พบข้อมูลครูผู้สอน (Teachers) ในระบบ")
    if not rooms_raw:
        errors.append("❌ ไม่พบข้อมูลห้องเรียน (Rooms) ในระบบ")
    if not classes_raw:
        errors.append("❌ ไม่พบข้อมูลกลุ่มเรียน/นักเรียน (Classes) ในระบบ")
    if not subjects_raw:
        errors.append("❌ ไม่พบข้อมูลรายวิชาที่ต้องจัดสอน (Subjects) ในระบบ")
        
    if errors:
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "stats": {}
        }
    
    # แปลงเป็น DataFrame เพื่อง่ายต่อการตรวจสอบ
    df_t = pd.DataFrame(teachers_raw)
    df_r = pd.DataFrame(rooms_raw)
    df_c = pd.DataFrame(classes_raw)
    df_s = pd.DataFrame(subjects_raw)
    
    # 3.2 ตรวจสอบค่าว่าง (Empty / Null / NaN) ในคอลัมน์สำคัญ
    req_t_cols = ["teacher_id", "teacher_name", "max_hours_per_week"]
    req_r_cols = ["room_id", "room_name", "room_type", "capacity"]
    req_c_cols = ["class_id", "class_name", "student_count"]
    req_s_cols = ["subject_id", "subject_name", "teacher_id", "class_id", "periods_per_week", "block_size"]
    
    for col in req_t_cols:
        if col in df_t.columns and df_t[col].isna().any():
            errors.append(f"❌ พบค่าว่างในข้อมูลครู คอลัมน์ '{col}' จำนวน {df_t[col].isna().sum()} แถว")
            
    for col in req_r_cols:
        if col in df_r.columns and df_r[col].isna().any():
            errors.append(f"❌ พบค่าว่างในข้อมูลห้องเรียน คอลัมน์ '{col}' จำนวน {df_r[col].isna().sum()} แถว")
            
    for col in req_c_cols:
        if col in df_c.columns and df_c[col].isna().any():
            errors.append(f"❌ พบค่าว่างในข้อมูลกลุ่มเรียน คอลัมน์ '{col}' จำนวน {df_c[col].isna().sum()} แถว")
            
    for col in req_s_cols:
        if col in df_s.columns and df_s[col].isna().any():
            errors.append(f"❌ พบค่าว่างในข้อมูลรายวิชา คอลัมน์ '{col}' จำนวน {df_s[col].isna().sum()} แถว")

    # 3.3 ตรวจสอบ ID ซ้ำ (Duplicate IDs)
    if "teacher_id" in df_t.columns:
        dup_t = df_t[df_t.duplicated(subset=["teacher_id"], keep=False)]["teacher_id"].tolist()
        if dup_t:
            errors.append(f"❌ พบรหัสครูผู้สอนซ้ำกัน: {list(set(dup_t))}")

    if "room_id" in df_r.columns:
        dup_r = df_r[df_r.duplicated(subset=["room_id"], keep=False)]["room_id"].tolist()
        if dup_r:
            errors.append(f"❌ พบรหัสห้องเรียนซ้ำกัน: {list(set(dup_r))}")

    if "class_id" in df_c.columns:
        dup_c = df_c[df_c.duplicated(subset=["class_id"], keep=False)]["class_id"].tolist()
        if dup_c:
            errors.append(f"❌ พบรหัสกลุ่มเรียนซ้ำกัน: {list(set(dup_c))}")

    if "subject_id" in df_s.columns:
        # รายวิชาต้องไม่ซ้ำกันในระดับ (subject_id, class_id)
        dup_s = df_s[df_s.duplicated(subset=["subject_id", "class_id"], keep=False)]
        if not dup_s.empty:
            errors.append(f"❌ พบรหัสวิชาซ้ำกันในกลุ่มเรียนเดียวกัน: {dup_s[['subject_id', 'class_id']].to_dict('records')}")

    teacher_ids_set = set(df_t["teacher_id"].dropna().astype(str)) if "teacher_id" in df_t.columns else set()
    room_ids_set = set(df_r["room_id"].dropna().astype(str)) if "room_id" in df_r.columns else set()
    class_ids_set = set(df_c["class_id"].dropna().astype(str)) if "class_id" in df_c.columns else set()
    
    # สร้าง Lookups
    teacher_name_map = dict(zip(df_t["teacher_id"].astype(str), df_t["teacher_name"])) if "teacher_name" in df_t.columns else {}
    teacher_max_map = dict(zip(df_t["teacher_id"].astype(str), pd.to_numeric(df_t["max_hours_per_week"], errors='coerce').fillna(20))) if "max_hours_per_week" in df_t.columns else {}
    class_student_count_map = dict(zip(df_c["class_id"].astype(str), pd.to_numeric(df_c["student_count"], errors='coerce').fillna(30))) if "student_count" in df_c.columns else {}
    
    # 3.4 ตรวจสอบการอ้างอิง Foreign Keys (Referential Integrity)
    for idx, s in df_s.iterrows():
        t_id = str(s.get("teacher_id", ""))
        c_id = str(s.get("class_id", ""))
        pref_r = s.get("preferred_room_id")
        
        if t_id not in teacher_ids_set:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' (ID: {s.get('subject_id')}) อ้างอิงรหัสครู '{t_id}' ที่ไม่มีในระบบ")
        if c_id not in class_ids_set:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' (ID: {s.get('subject_id')}) อ้างอิงรหัสกลุ่มเรียน '{c_id}' ที่ไม่มีในระบบ")
        if pref_r and pd.notna(pref_r) and str(pref_r) not in room_ids_set:
            warnings.append(f"⚠️ วิชา '{s.get('subject_name')}' ระบุห้องเจาะจง '{pref_r}' ที่ไม่มีในระบบ (จะใช้การจัดสรรอัตโนมัติตามประเภทห้อง)")

    # 3.5 ตรวจขนาดห้องไม่พอกับจำนวนนักเรียน (Room Capacity vs Student Count)
    room_capacities_by_type: Dict[str, List[int]] = {}
    for _, r in df_r.iterrows():
        rtype = str(r.get("room_type", "ห้องเรียนทฤษฎี"))
        cap = int(r.get("capacity", 0))
        room_capacities_by_type.setdefault(rtype, []).append(cap)
        
    for idx, s in df_s.iterrows():
        c_id = str(s.get("class_id", ""))
        rtype = str(s.get("room_type_required", "ห้องเรียนทฤษฎี"))
        st_count = class_student_count_map.get(c_id, 0)
        
        caps = room_capacities_by_type.get(rtype, [])
        if not caps:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' ต้องการห้องประเภท '{rtype}' แต่ไม่มีห้องประเภทนี้ในระบบ")
        elif max(caps) < st_count:
            errors.append(f"❌ กลุ่มเรียน '{c_id}' (มีนักเรียน {st_count} คน) ในวิชา '{s.get('subject_name')}' ต้องการห้องประเภท '{rtype}' แต่ห้องที่ใหญ่ที่สุดจุได้เพียง {max(caps)} คน")

    # 3.6 ตรวจสอบครูสอนเกินคาบ (Teacher Overbooked)
    teacher_assigned_hours: Dict[str, int] = {}
    for _, s in df_s.iterrows():
        t_id = str(s.get("teacher_id", ""))
        periods = int(s.get("periods_per_week", 0))
        teacher_assigned_hours[t_id] = teacher_assigned_hours.get(t_id, 0) + periods
        
    for t_id, assigned_h in teacher_assigned_hours.items():
        max_h = teacher_max_map.get(t_id, 18)
        t_name = teacher_name_map.get(t_id, t_id)
        if assigned_h > max_h:
            errors.append(f"❌ ครู {t_name} ({t_id}) ถูกมอบหมายงานสอน {assigned_h} คาบ ซึ่งเกินขีดจำกัดสูงสุด {max_h} คาบ/สัปดาห์")
        elif assigned_h > TOTAL_SLOTS_PER_WEEK:
            errors.append(f"❌ ครู {t_name} ({t_id}) มีคาบสอน {assigned_h} คาบ เกินจำนวนคาบทั้งหมดในสัปดาห์ ({TOTAL_SLOTS_PER_WEEK} คาบ)")

    # 3.7 ตรวจสอบความถูกต้องของ block_size และ periods_per_week
    for idx, s in df_s.iterrows():
        p = int(s.get("periods_per_week", 0))
        b = int(s.get("block_size", 0))
        if p <= 0:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' มีจำนวนคาบต่อสัปดาห์ (periods_per_week) เป็น 0 หรือติดลบ")
        if b <= 0 or b > 4:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' มีขนาดคาบติดต่อกัน (block_size: {b}) ไม่ถูกต้อง (ต้องอยู่ระหว่าง 1-4 คาบ)")
        if b > p:
            errors.append(f"❌ วิชา '{s.get('subject_name')}' กำหนดคาบติดกัน (block_size: {b}) มากกว่าจำนวนคาบต่อสัปดาห์ ({p})")

    # 3.8 ตรวจสอบทรัพยากรห้องเรียนโดยรวม (Total Capacity Feasibility)
    total_assigned_periods = sum(int(s.get("periods_per_week", 0)) for _, s in df_s.iterrows())
    total_room_slots = len(df_r) * TOTAL_SLOTS_PER_WEEK
    
    if total_assigned_periods > total_room_slots:
        errors.append(f"❌ จำนวนคาบเรียนที่ต้องจัดสอนทั้งหมด ({total_assigned_periods} คาบ) เกินขีดความจุรวมของห้องเรียนทุกห้อง ({total_room_slots} คาบ)")
    elif total_assigned_periods > total_room_slots * 0.9:
        warnings.append(f"⚠️ การใช้ห้องเรียนหนาแน่นสูงมาก ({total_assigned_periods}/{total_room_slots} คาบ คิดเป็น {round(total_assigned_periods/total_room_slots*100, 1)}%) อาจจัดตารางยาก")

    # รวบรวมสถิติ (Summary Stats)
    stats = {
        "teacher_count": len(df_t),
        "room_count": len(df_r),
        "class_count": len(df_c),
        "subject_count": len(df_s),
        "total_periods_required": total_assigned_periods,
        "total_available_room_slots": total_room_slots,
        "overall_room_utilization_estimate": round((total_assigned_periods / max(1, total_room_slots)) * 100, 1),
        "teacher_workload": [
            {
                "teacher_id": t_id,
                "teacher_name": teacher_name_map.get(t_id, t_id),
                "assigned_hours": teacher_assigned_hours.get(t_id, 0),
                "max_hours": teacher_max_map.get(t_id, 18),
                "utilization_pct": round((teacher_assigned_hours.get(t_id, 0) / max(1, teacher_max_map.get(t_id, 18))) * 100, 1)
            }
            for t_id in df_t["teacher_id"].astype(str)
        ]
    }
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": stats
    }


# ---------------------------------------------------------------------------
# 4. ฟังก์ชันอ่านและแยกไฟล์นำเข้า (JSON, Excel, CSV)
# ---------------------------------------------------------------------------

def parse_json_input(file_content: bytes) -> Dict[str, Any]:
    """อ่านและแปลงไฟล์ JSON เป็นโครงสร้างข้อมูลของระบบ"""
    text = file_content.decode("utf-8")
    return json.loads(text)


def parse_excel_input(file_content: bytes) -> Dict[str, Any]:
    """
    อ่านไฟล์ Excel (.xlsx)
    รองรับ 2 รูปแบบ:
      แบบ A: มี 4 Sheets แยกกัน ('Teachers', 'Rooms', 'Classes', 'Subjects')
      แบบ B: รวมในตาราง Unified Master Sheet แผ่นเดียว
    """
    excel_file = pd.ExcelFile(io.BytesIO(file_content))
    sheet_names = [s.strip() for s in excel_file.sheet_names]
    sheet_names_lower = {s.lower(): s for s in sheet_names}
    
    # ตรวจสอบว่ามี 4 sheets ครบหรือไม่
    has_teachers = "teachers" in sheet_names_lower or "ครู" in sheet_names_lower
    has_rooms = "rooms" in sheet_names_lower or "ห้อง" in sheet_names_lower
    has_classes = "classes" in sheet_names_lower or "กลุ่มเรียน" in sheet_names_lower
    has_subjects = "subjects" in sheet_names_lower or "วิชา" in sheet_names_lower
    
    if has_teachers and has_rooms and has_classes and has_subjects:
        t_sheet = sheet_names_lower.get("teachers", sheet_names_lower.get("ครู"))
        r_sheet = sheet_names_lower.get("rooms", sheet_names_lower.get("ห้อง"))
        c_sheet = sheet_names_lower.get("classes", sheet_names_lower.get("กลุ่มเรียน"))
        s_sheet = sheet_names_lower.get("subjects", sheet_names_lower.get("วิชา"))
        
        df_t = pd.read_excel(excel_file, sheet_name=t_sheet)
        df_r = pd.read_excel(excel_file, sheet_name=r_sheet)
        df_c = pd.read_excel(excel_file, sheet_name=c_sheet)
        df_s = pd.read_excel(excel_file, sheet_name=s_sheet)
        
        # จัดการ unavailable_slots ถ้าเก็บเป็น JSON string
        teachers_list = df_t.to_dict("records")
        for t in teachers_list:
            if "unavailable_slots" in t and pd.notna(t["unavailable_slots"]):
                if isinstance(t["unavailable_slots"], str):
                    try:
                        t["unavailable_slots"] = json.loads(t["unavailable_slots"])
                    except Exception:
                        t["unavailable_slots"] = []
            else:
                t["unavailable_slots"] = []
                
        return {
            "teachers": teachers_list,
            "rooms": df_r.to_dict("records"),
            "classes": df_c.to_dict("records"),
            "subjects": df_s.to_dict("records")
        }
    else:
        # กรณีเป็นตารางเดียว (Master Sheet)
        df_unified = pd.read_excel(excel_file, sheet_name=0)
        return parse_unified_dataframe(df_unified)


def parse_csv_input(file_content: bytes) -> Dict[str, Any]:
    """
    อ่านไฟล์ CSV แบบ Master Table (Unified Ingestion Table)
    โดยถอดแยกออกเป็น Teachers, Rooms, Classes, Subjects อัตโนมัติ
    """
    # รองรับการถอดรหัสทั้ง utf-8 และ utf-8-sig (BOM) หรือ cp874/tis-620
    for enc in ["utf-8-sig", "utf-8", "tis-620", "cp874"]:
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
            return parse_unified_dataframe(df)
        except UnicodeDecodeError:
            continue
            
    raise ValueError("ไม่สามารถถอดรหัสไฟล์ CSV ได้ กรุณาบันทึกเป็น UTF-8")


def parse_unified_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    แปลงตารางรวม (Unified Master DataFrame) ออกเป็น 4 Entity ตามหลัก Relational Normalization
    ทำให้ผู้ใช้สามารถจัดเตรียมไฟล์ในตาราง Excel/CSV เพียงแผ่นเดียวได้ สะดวกมาก
    """
    # 1. ครู
    t_cols = [c for c in ["teacher_id", "teacher_name", "department", "max_hours_per_week"] if c in df.columns]
    df_t = df[t_cols].drop_duplicates(subset=["teacher_id"]).copy()
    if "max_hours_per_week" not in df_t.columns:
        df_t["max_hours_per_week"] = 18
    df_t["unavailable_slots"] = [[] for _ in range(len(df_t))]
    
    # 2. ห้องเรียน
    r_cols = [c for c in ["room_id", "room_name", "room_type", "capacity", "building"] if c in df.columns]
    df_r = df[r_cols].drop_duplicates(subset=["room_id"]).copy()
    if "capacity" not in df_r.columns:
        df_r["capacity"] = 40
    if "room_type" not in df_r.columns:
        df_r["room_type"] = "ห้องเรียนทฤษฎี"
        
    # 3. กลุ่มเรียน
    c_cols = [c for c in ["class_id", "class_name", "student_count", "department"] if c in df.columns]
    df_c = df[c_cols].drop_duplicates(subset=["class_id"]).copy()
    if "student_count" not in df_c.columns:
        df_c["student_count"] = 30
        
    # 4. รายวิชา
    s_cols = [c for c in ["subject_id", "subject_name", "teacher_id", "class_id", "room_type_required", "periods_per_week", "block_size", "credit"] if c in df.columns]
    df_s = df[s_cols].drop_duplicates(subset=["subject_id", "class_id"]).copy()
    if "block_size" not in df_s.columns:
        df_s["block_size"] = df_s["periods_per_week"].apply(lambda p: min(p, 2))
    if "room_type_required" not in df_s.columns:
        df_s["room_type_required"] = "ห้องเรียนทฤษฎี"
        
    return {
        "teachers": df_t.to_dict("records"),
        "rooms": df_r.to_dict("records"),
        "classes": df_c.to_dict("records"),
        "subjects": df_s.to_dict("records")
    }


# ---------------------------------------------------------------------------
# 5. ฟังก์ชันสร้าง Template เปล่าสำหรับดาวน์โหลด
# ---------------------------------------------------------------------------

def generate_blank_template_excel() -> bytes:
    """สร้าง Template ไฟล์ Excel สำหรับนำเข้าข้อมูล"""
    sample = generate_sample_dataset("small")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(sample["teachers"]).to_excel(writer, sheet_name="Teachers", index=False)
        pd.DataFrame(sample["rooms"]).to_excel(writer, sheet_name="Rooms", index=False)
        pd.DataFrame(sample["classes"]).to_excel(writer, sheet_name="Classes", index=False)
        pd.DataFrame(sample["subjects"]).to_excel(writer, sheet_name="Subjects", index=False)
    return output.getvalue()


def generate_blank_template_csv() -> bytes:
    """สร้าง Template ไฟล์ CSV แบบ Unified Table สำหรับนำเข้าข้อมูล"""
    sample = generate_sample_dataset("small")
    # นำมา denormalize รวมเป็น 1 ตาราง
    t_map = {t["teacher_id"]: t for t in sample["teachers"]}
    r_map = {r["room_id"]: r for r in sample["rooms"]}
    c_map = {c["class_id"]: c for c in sample["classes"]}
    
    rows = []
    for s in sample["subjects"]:
        t = t_map.get(s["teacher_id"], {})
        c = c_map.get(s["class_id"], {})
        rows.append({
            "subject_id": s["subject_id"],
            "subject_name": s["subject_name"],
            "periods_per_week": s["periods_per_week"],
            "block_size": s["block_size"],
            "room_type_required": s["room_type_required"],
            "teacher_id": s["teacher_id"],
            "teacher_name": t.get("teacher_name", ""),
            "class_id": s["class_id"],
            "class_name": c.get("class_name", ""),
            "student_count": c.get("student_count", 30),
            "max_hours_per_week": t.get("max_hours_per_week", 18)
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def generate_blank_template_json() -> bytes:
    """สร้าง Template ไฟล์ JSON"""
    sample = generate_sample_dataset("small")
    return json.dumps(sample, ensure_ascii=False, indent=2).encode("utf-8")
