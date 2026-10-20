"""
=============================================================================
ระบบจัดตารางสอนอัตโนมัติด้วย AI (Automated Timetable Scheduling System)
โมดูล: scheduler_engine.py - สมองกลคำนวณตารางสอนด้วย Google OR-Tools (CP-SAT)
=============================================================================
"""

import time
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from ortools.sat.python import cp_model

from models import (
    DAYS, PERIODS, DAY_NAMES_TH, MORNING_PERIODS, AFTERNOON_PERIODS,
    TOTAL_PERIODS_PER_DAY, TOTAL_DAYS, TOTAL_SLOTS_PER_WEEK,
    Teacher, Room, StudentClass, SubjectAssignment, TimetableEntry
)


class TimetableSession:
    """หน่วยย่อยของการจัดคาบสอน (Schedulable Session Chunk)"""
    def __init__(
        self,
        session_id: str,
        subject: SubjectAssignment,
        duration: int,
        candidate_rooms: List[str]
    ):
        self.session_id = session_id
        self.subject = subject
        self.duration = duration
        self.candidate_rooms = candidate_rooms


class TimetableEngine:
    """
    สมองกล AI จัดตารางสอนอัตโนมัติ (Automated Timetable AI Engine)
    ขับเคลื่อนด้วย Google OR-Tools Constraint Programming (CP-SAT) Solver
    รองรับทั้ง Hard Constraints (กฎเหล็ก 100%) และ Soft Constraints (การกระจายและปรับแต่ง)
    """

    def __init__(
        self,
        teachers: List[Teacher],
        rooms: List[Room],
        classes: List[StudentClass],
        subjects: List[SubjectAssignment],
        seed: int = 42,
        time_limit_sec: float = 20.0,
        deterministic: bool = True,
        num_workers: int = 4,
        strict_unavailability: bool = True,
        penalty_consecutive: int = 50,
        penalty_unavailability: int = 500,
        penalty_same_day_subject: int = 200
    ):
        self.teachers = teachers
        self.rooms = rooms
        self.classes = classes
        self.subjects = subjects
        
        # Lookups
        self.teacher_map = {t.teacher_id: t for t in teachers}
        self.room_map = {r.room_id: r for r in rooms}
        self.class_map = {c.class_id: c for c in classes}
        
        # Solver Configuration
        self.seed = seed
        self.time_limit_sec = time_limit_sec
        self.deterministic = deterministic
        self.num_workers = 1 if deterministic else max(1, num_workers)
        
        # Constraint parameters
        self.strict_unavailability = strict_unavailability
        self.penalty_consecutive = penalty_consecutive
        self.penalty_unavailability = penalty_unavailability
        self.penalty_same_day_subject = penalty_same_day_subject
        
        # Internal state
        self.sessions: List[TimetableSession] = []
        self._prepare_sessions()

    def _prepare_sessions(self):
        """
        แตกรายวิชา (Subjects) ออกเป็นคาบเรียนย่อย (Sessions) ตาม periods_per_week และ block_size
        ตัวอย่าง: 3 คาบ/สัปดาห์ (block_size=3) -> 1 session (3 คาบ)
                 4 คาบ/สัปดาห์ (block_size=2) -> 2 sessions (2 คาบ + 2 คาบ)
                 3 คาบ/สัปดาห์ (block_size=2) -> 2 sessions (2 คาบ + 1 คาบ)
        """
        self.sessions.clear()
        session_counter = 0

        for subj in self.subjects:
            c = self.class_map.get(subj.class_id)
            student_count = c.student_count if c else 30
            
            # ค้นหาห้องที่เหมาะสม (ประเภทห้องตรง และ ความจุเพียงพอ)
            candidate_room_ids = []
            for r in self.rooms:
                if r.room_type == subj.room_type_required and r.capacity >= student_count:
                    candidate_room_ids.append(r.room_id)
                    
            # กรณีระบุห้องเจาะจง (preferred_room_id)
            if subj.preferred_room_id and subj.preferred_room_id in self.room_map:
                if subj.preferred_room_id not in candidate_room_ids:
                    # ถ้าห้องเจาะจงมีความจุพอ ให้เพิ่มเข้าไป
                    pref_r = self.room_map[subj.preferred_room_id]
                    if pref_r.capacity >= student_count:
                        candidate_room_ids.append(subj.preferred_room_id)

            # ถ้ายังไม่มีห้องใดเข้าเกณฑ์เลย ให้ใช้ห้องที่มีความจุมากที่สุดเป็น Fallback
            if not candidate_room_ids:
                candidate_room_ids = [r.room_id for r in self.rooms if r.capacity >= student_count]
                if not candidate_room_ids:
                    # ถ้าไม่มีเลยให้ใช้ห้องทั้งหมด
                    candidate_room_ids = [r.room_id for r in self.rooms]

            # แตกเป็น sessions ย่อย
            remaining_periods = subj.periods_per_week
            while remaining_periods > 0:
                duration = min(remaining_periods, subj.block_size)
                # ป้องกัน session ยาวเกิน 4 คาบ (ครึ่งวัน)
                duration = min(duration, 4)
                
                session_counter += 1
                sess_id = f"SESS_{subj.subject_id}_{subj.class_id}_{session_counter}"
                self.sessions.append(TimetableSession(
                    session_id=sess_id,
                    subject=subj,
                    duration=duration,
                    candidate_rooms=candidate_room_ids
                ))
                remaining_periods -= duration

    def _get_valid_starts(self, duration: int) -> List[int]:
        """
        หาคาบเริ่มต้น (Start Periods) ที่ถูกต้อง เพื่อไม่ให้คาบเรียนกินข้ามเวลาพักกลางวัน
        ช่วงเช้า: คาบ 0..3 (08:30-11:50)
        ช่วงบ่าย: คาบ 4..7 (12:40-16:00)
        """
        valid_starts = []
        for p in MORNING_PERIODS:
            if p + duration - 1 <= MORNING_PERIODS[-1]:
                valid_starts.append(p)
        for p in AFTERNOON_PERIODS:
            if p + duration - 1 <= AFTERNOON_PERIODS[-1]:
                valid_starts.append(p)
        return valid_starts

    def solve(self, progress_callback=None) -> Dict[str, Any]:
        """
        ประมวลผลจัดตารางสอนด้วย CP-SAT Model
        ส่งกลับผลลัพธ์พร้อมสถิติทางวิศวกรรม
        """
        start_time = time.time()
        model = cp_model.CpModel()
        
        if progress_callback:
            progress_callback(10, "กำลังสร้างตัวแปรการตัดสินใจและข้อจำกัด (Decision Variables & Constraints)...")

        days = list(range(TOTAL_DAYS))
        periods = list(range(TOTAL_PERIODS_PER_DAY))
        
        # -------------------------------------------------------------------
        # 1. การสร้างตัวแปรการตัดสินใจ (Decision Variables)
        # x[(sess_id, day, start_p, room)] = 1 หากจัด session นี้ในวันและคาบดังกล่าว
        # -------------------------------------------------------------------
        x: Dict[Tuple[str, int, int, str], cp_model.IntVar] = {}
        for s in self.sessions:
            dur = s.duration
            valid_starts = self._get_valid_starts(dur)
            for d in days:
                for p in valid_starts:
                    for r in s.candidate_rooms:
                        var_name = f"x_{s.session_id}_{d}_{p}_{r}"
                        x[(s.session_id, d, p, r)] = model.NewBoolVar(var_name)

        # -------------------------------------------------------------------
        # 2. Hard Constraint 1: แต่ละ Session ต้องได้รับการจัด 1 ครั้งพอดี
        # -------------------------------------------------------------------
        for s in self.sessions:
            dur = s.duration
            valid_starts = self._get_valid_starts(dur)
            sess_vars = [
                x[(s.session_id, d, p, r)]
                for d in days
                for p in valid_starts
                for r in s.candidate_rooms
                if (s.session_id, d, p, r) in x
            ]
            if sess_vars:
                model.Add(sum(sess_vars) == 1)
            else:
                return {
                    "status": "INFEASIBLE",
                    "status_text": "ไม่สามารถจัดตารางได้: รายวิชาบางวิชาไม่มีห้องที่เหมาะสม",
                    "timetable": [],
                    "wall_time": time.time() - start_time,
                    "metrics": {}
                }

        # Helper สำหรับดึงตัวแปรที่ครอบครองช่วงเวลา (day, t)
        def get_occupying_vars(session: TimetableSession, day: int, t: int, target_room: Optional[str] = None):
            dur = session.duration
            valid_starts = self._get_valid_starts(dur)
            res = []
            for p in valid_starts:
                if p <= t < p + dur:
                    if target_room is not None:
                        if (session.session_id, day, p, target_room) in x:
                            res.append(x[(session.session_id, day, p, target_room)])
                    else:
                        for rm in session.candidate_rooms:
                            if (session.session_id, day, p, rm) in x:
                                res.append(x[(session.session_id, day, p, rm)])
            return res

        if progress_callback:
            progress_callback(30, "กำลังบังคับกฎเหล็ก No-Overlap (ครู, ห้อง, กลุ่มเรียน ห้ามซ้อนทับ 100%)...")

        # -------------------------------------------------------------------
        # 3. Hard Constraint 2: ครู 1 คน สอนได้ไม่เกิน 1 ห้องในเวลาเดียวกัน (No Teacher Overlap)
        # -------------------------------------------------------------------
        for teacher in self.teachers:
            t_sessions = [s for s in self.sessions if s.subject.teacher_id == teacher.teacher_id]
            if not t_sessions:
                continue
            for d in days:
                for t in periods:
                    occ = []
                    for s in t_sessions:
                        occ.extend(get_occupying_vars(s, d, t))
                    if len(occ) > 1:
                        model.Add(sum(occ) <= 1)

        # -------------------------------------------------------------------
        # 4. Hard Constraint 3: กลุ่มเรียน 1 กลุ่ม เรียนได้ไม่เกิน 1 วิชาในเวลาเดียวกัน (No Class Overlap)
        # -------------------------------------------------------------------
        for c in self.classes:
            c_sessions = [s for s in self.sessions if s.subject.class_id == c.class_id]
            if not c_sessions:
                continue
            for d in days:
                for t in periods:
                    occ = []
                    for s in c_sessions:
                        occ.extend(get_occupying_vars(s, d, t))
                    if len(occ) > 1:
                        model.Add(sum(occ) <= 1)

        # -------------------------------------------------------------------
        # 5. Hard Constraint 4: ห้อง 1 ห้อง มีการเรียนการสอนได้ไม่เกิน 1 วิชาในเวลาเดียวกัน (No Room Overlap)
        # -------------------------------------------------------------------
        for r in self.rooms:
            r_id = r.room_id
            for d in days:
                for t in periods:
                    occ = []
                    for s in self.sessions:
                        if r_id in s.candidate_rooms:
                            occ.extend(get_occupying_vars(s, d, t, target_room=r_id))
                    if len(occ) > 1:
                        model.Add(sum(occ) <= 1)

        # -------------------------------------------------------------------
        # 6. Constraint 5: ป้องกันวิชาเดียวกันของกลุ่มเดียวกัน จัดซ้ำในวันเดียวกัน (Different Days Distribution)
        # -------------------------------------------------------------------
        subject_grouping: Dict[Tuple[str, str], List[TimetableSession]] = {}
        for s in self.sessions:
            key = (s.subject.subject_id, s.subject.class_id)
            subject_grouping.setdefault(key, []).append(s)

        penalty_terms = []

        for (s_id, c_id), sess_list in subject_grouping.items():
            if len(sess_list) > 1:
                for d in days:
                    day_vars = []
                    for s in sess_list:
                        dur = s.duration
                        for p in self._get_valid_starts(dur):
                            for rm in s.candidate_rooms:
                                if (s.session_id, d, p, rm) in x:
                                    day_vars.append(x[(s.session_id, d, p, rm)])
                    if day_vars:
                        # พยายามหลีกเลี่ยงการจัดวิชาเดียวกันในวันเดียวกัน
                        # ถ้าจัดเกิน 1 ครั้งในวันเดียวกันจะมีค่าปรับ
                        overlap_day = model.NewBoolVar(f"same_day_{s_id}_{c_id}_{d}")
                        model.Add(sum(day_vars) <= 1 + overlap_day * len(sess_list))
                        penalty_terms.append(overlap_day * self.penalty_same_day_subject)

        if progress_callback:
            progress_callback(50, "กำลังประมวลผลเงื่อนไขพิเศษ (Soft Constraints & Workload Smoothing)...")

        # -------------------------------------------------------------------
        # 7. Soft/Hard Constraint 6: ช่วงเวลาห้ามสอนของครู (Teacher Unavailable Slots)
        # -------------------------------------------------------------------
        for teacher in self.teachers:
            unavail_slots = teacher.unavailable_slots or []
            t_sessions = [s for s in self.sessions if s.subject.teacher_id == teacher.teacher_id]
            for slot in unavail_slots:
                d = slot.get("day", 0)
                t = slot.get("period", 0)
                occ = []
                for s in t_sessions:
                    occ.extend(get_occupying_vars(s, d, t))
                if occ:
                    if self.strict_unavailability:
                        # ห้ามสอนเด็ดขาด (Hard Constraint)
                        model.Add(sum(occ) == 0)
                    else:
                        # ห้ามสอนแบบยืดหยุ่น (Soft Penalty)
                        penalty_terms.extend([v * self.penalty_unavailability for v in occ])

        # -------------------------------------------------------------------
        # 8. Soft Constraint 7: กระจายคาบเรียนไม่ให้ครูสอนติดกันเกินกำหนด (Avoid Excessive Consecutive Periods)
        # เช่น หากครูสอนติดกัน 4 คาบในครึ่งวัน (เช่น เช้าคาบ 0,1,2,3 ทั้งหมด) จะมีค่าปรับ
        # -------------------------------------------------------------------
        for teacher in self.teachers:
            t_sessions = [s for s in self.sessions if s.subject.teacher_id == teacher.teacher_id]
            if not t_sessions:
                continue
            for d in days:
                # ตรวจช่วงเช้า 4 คาบ
                morning_occ_sum = []
                for t in MORNING_PERIODS:
                    occ = []
                    for s in t_sessions:
                        occ.extend(get_occupying_vars(s, d, t))
                    if occ:
                        # สร้าง indicator ว่าคาบ t ครูมีสอนหรือไม่
                        is_active = model.NewBoolVar(f"t_active_{teacher.teacher_id}_{d}_{t}")
                        model.Add(sum(occ) >= is_active)
                        morning_occ_sum.append(is_active)
                if len(morning_occ_sum) == len(MORNING_PERIODS):
                    # ถ้าสอนครบทั้ง 4 คาบเช้าติดกัน
                    all_morning = model.NewBoolVar(f"all_morning_{teacher.teacher_id}_{d}")
                    model.Add(sum(morning_occ_sum) <= 3 + all_morning)
                    penalty_terms.append(all_morning * self.penalty_consecutive)

                # ตรวจช่วงบ่าย 4 คาบ
                afternoon_occ_sum = []
                for t in AFTERNOON_PERIODS:
                    occ = []
                    for s in t_sessions:
                        occ.extend(get_occupying_vars(s, d, t))
                    if occ:
                        is_active = model.NewBoolVar(f"t_active_{teacher.teacher_id}_{d}_{t}")
                        model.Add(sum(occ) >= is_active)
                        afternoon_occ_sum.append(is_active)
                if len(afternoon_occ_sum) == len(AFTERNOON_PERIODS):
                    all_afternoon = model.NewBoolVar(f"all_afternoon_{teacher.teacher_id}_{d}")
                    model.Add(sum(afternoon_occ_sum) <= 3 + all_afternoon)
                    penalty_terms.append(all_afternoon * self.penalty_consecutive)

        # -------------------------------------------------------------------
        # 9. การตั้งค่าฟังก์ชันเป้าหมาย (Objective Function: Minimize Total Penalties)
        # -------------------------------------------------------------------
        if penalty_terms:
            model.Minimize(sum(penalty_terms))

        if progress_callback:
            progress_callback(70, f"ส่งโจทย์ให้ CP-SAT Solver ประมวลผล (Seed: {self.seed}, Workers: {self.num_workers})...")

        # -------------------------------------------------------------------
        # 10. การกำหนดค่าและสั่ง Solver ทำงาน (Deterministic & Reproducibility)
        # -------------------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.random_seed = self.seed
        solver.parameters.max_time_in_seconds = self.time_limit_sec
        solver.parameters.num_search_workers = self.num_workers
        solver.parameters.log_search_progress = False

        status = solver.Solve(model)
        elapsed_sec = time.time() - start_time

        status_name = solver.StatusName(status)
        is_success = status in (cp_model.OPTIMAL, cp_model.FEASIBLE)

        if progress_callback:
            progress_callback(100, f"การคำนวณเสร็จสิ้น (สถานะ: {status_name}, เวลา: {round(elapsed_sec, 2)} วินาที)")

        if not is_success:
            return {
                "status": status_name,
                "status_text": f"ไม่พบผลลัพธ์ที่เป็นไปได้ (Status: {status_name}) กรุณาลดชั่วโมงสอนหรือเพิ่มห้องเรียน",
                "is_success": False,
                "wall_time": round(elapsed_sec, 3),
                "timetable": [],
                "metrics": {}
            }

        # -------------------------------------------------------------------
        # 11. แปลงผลลัพธ์เป็น TimetableEntry และโครงสร้างตาราง
        # -------------------------------------------------------------------
        scheduled_entries: List[TimetableEntry] = []
        for s in self.sessions:
            dur = s.duration
            for d in days:
                for p in self._get_valid_starts(dur):
                    for r in s.candidate_rooms:
                        if (s.session_id, d, p, r) in x and solver.Value(x[(s.session_id, d, p, r)]) == 1:
                            occupied = list(range(p, p + dur))
                            time_start = PERIODS[p]["time_range"].split(" - ")[0]
                            time_end = PERIODS[p + dur - 1]["time_range"].split(" - ")[1]
                            time_str = f"{time_start} - {time_end}"
                            
                            t_info = self.teacher_map.get(s.subject.teacher_id)
                            r_info = self.room_map.get(r)
                            c_info = self.class_map.get(s.subject.class_id)
                            
                            scheduled_entries.append(TimetableEntry(
                                session_id=s.session_id,
                                subject_id=s.subject.subject_id,
                                subject_name=s.subject.subject_name,
                                teacher_id=s.subject.teacher_id,
                                teacher_name=t_info.teacher_name if t_info else s.subject.teacher_id,
                                class_id=s.subject.class_id,
                                class_name=c_info.class_name if c_info else s.subject.class_id,
                                room_id=r,
                                room_name=r_info.room_name if r_info else r,
                                day_index=d,
                                day_name=DAY_NAMES_TH[d],
                                start_period=p,
                                duration=dur,
                                occupied_periods=occupied,
                                time_range=time_str
                            ))

        # -------------------------------------------------------------------
        # 12. สรุปผลตัวชี้วัด (Analytics & Decision Metrics)
        # -------------------------------------------------------------------
        metrics = self._calculate_metrics(scheduled_entries, elapsed_sec, solver)

        return {
            "status": status_name,
            "status_text": "จัดตารางสอนสำเร็จสมบูรณ์ (Optimal Solution)" if status == cp_model.OPTIMAL else "จัดตารางสอนสำเร็จ (Feasible Solution)",
            "is_success": True,
            "wall_time": round(elapsed_sec, 3),
            "objective_value": solver.ObjectiveValue() if penalty_terms else 0,
            "timetable": scheduled_entries,
            "metrics": metrics
        }

    def _calculate_metrics(
        self,
        entries: List[TimetableEntry],
        elapsed_sec: float,
        solver: cp_model.CpSolver
    ) -> Dict[str, Any]:
        """คำนวณตัวชี้วัดประสิทธิภาพ (KPIs & Metrics) สำหรับ Dashboard"""
        total_slots_per_room = TOTAL_SLOTS_PER_WEEK  # 40 คาบ
        
        # 1. การใช้งานห้องเรียน (Room Utilization)
        room_usage = {r.room_id: 0 for r in self.rooms}
        for entry in entries:
            room_usage[entry.room_id] += entry.duration
            
        room_stats = []
        for r in self.rooms:
            used = room_usage.get(r.room_id, 0)
            rate = round((used / total_slots_per_room) * 100, 1)
            room_stats.append({
                "room_id": r.room_id,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "capacity": r.capacity,
                "used_periods": used,
                "free_periods": total_slots_per_room - used,
                "utilization_pct": rate
            })
            
        overall_used_room_periods = sum(room_usage.values())
        total_room_capacity_periods = len(self.rooms) * total_slots_per_room
        overall_room_utilization = round((overall_used_room_periods / max(1, total_room_capacity_periods)) * 100, 1)

        # 2. ภาระงานครู (Teacher Workload)
        teacher_workload_dict = {t.teacher_id: 0 for t in self.teachers}
        teacher_days_dict = {t.teacher_id: set() for t in self.teachers}
        for entry in entries:
            teacher_workload_dict[entry.teacher_id] += entry.duration
            teacher_days_dict[entry.teacher_id].add(entry.day_index)
            
        teacher_stats = []
        for t in self.teachers:
            actual_h = teacher_workload_dict.get(t.teacher_id, 0)
            max_h = t.max_hours_per_week
            active_days = len(teacher_days_dict.get(t.teacher_id, set()))
            teacher_stats.append({
                "teacher_id": t.teacher_id,
                "teacher_name": t.teacher_name,
                "department": t.department,
                "actual_hours": actual_h,
                "max_hours": max_h,
                "remaining_capacity": max(0, max_h - actual_h),
                "teaching_days_count": active_days,
                "workload_pct": round((actual_h / max(1, max_h)) * 100, 1)
            })

        # 3. ภาระการเรียนของกลุ่มเรียน (Class Workload)
        class_usage = {c.class_id: 0 for c in self.classes}
        for entry in entries:
            class_usage[entry.class_id] += entry.duration
            
        class_stats = []
        for c in self.classes:
            used = class_usage.get(c.class_id, 0)
            class_stats.append({
                "class_id": c.class_id,
                "class_name": c.class_name,
                "department": c.department,
                "total_periods": used,
                "free_periods": total_slots_per_room - used
            })

        # 4. สรุปคาบว่างรวม (Total Free Slots)
        total_free_periods = total_room_capacity_periods - overall_used_room_periods

        return {
            "wall_time_sec": round(elapsed_sec, 3),
            "deterministic_seed": self.seed,
            "overall_room_utilization_pct": overall_room_utilization,
            "total_room_slots": total_room_capacity_periods,
            "used_room_slots": overall_used_room_periods,
            "total_free_slots": total_free_periods,
            "room_stats": room_stats,
            "teacher_stats": teacher_stats,
            "class_stats": class_stats,
            "total_sessions_scheduled": len(entries),
            "conflicts_count": 0  # รับประกัน 0 ข้อขัดแย้ง 100% ตามหลัก Hard Constraints ของ CP-SAT
        }
