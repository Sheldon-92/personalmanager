#!/usr/bin/env python3
"""
添加课程时间表到Google Calendar

将用户的四门课程信息同步到Google Calendar中
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pm.integrations.google_auth import GoogleAuthManager
from pm.core.config import PMConfig
import structlog

logger = structlog.get_logger()


class CourseScheduleManager:
    """课程时间表管理器"""

    def __init__(self):
        self.config = PMConfig()
        self.auth_manager = GoogleAuthManager(self.config)

        # 2025年秋季课程信息
        self.courses = [
            {
                "name": "Ethical Leadership for Design Professionals",
                "code": "PGDM 5250",
                "crn": "16024",
                "instructor": "Matthew Robb",
                "day": "Monday",
                "start_time": "09:00",
                "end_time": "11:40",
                "location": "63 Fifth Ave, Room 502",
                "semester_start": "2025-08-27",
                "semester_end": "2025-12-15",
                "color": "blue"
            },
            {
                "name": "Graduate Writing and Research Studio 3",
                "code": "NELP 5899",
                "crn": "2633",
                "instructor": "Fiore Sireci",
                "day": "Tuesday",
                "start_time": "09:00",
                "end_time": "11:40",
                "location": "63 Fifth Ave, Room 622",
                "semester_start": "2025-08-27",
                "semester_end": "2025-12-15",
                "color": "green"
            },
            {
                "name": "Design Research Capstone Studio",
                "code": "PGDM 5275",
                "crn": "16029",
                "instructor": "Sareeta Amrute",
                "day": "Wednesday",
                "start_time": "12:10",
                "end_time": "14:50",
                "location": "63 Fifth Ave, Room 502",
                "semester_start": "2025-08-27",
                "semester_end": "2025-12-15",
                "color": "orange"
            },
            {
                "name": "Collab: Multispecies Design",
                "code": "PSAM 5550",
                "crn": "11934",
                "instructor": "Jane Pirone",
                "day": "Friday",
                "start_time": "12:10",
                "end_time": "14:50",
                "location": "6 East 16th Street, Room 1204A",
                "semester_start": "2025-08-27",
                "semester_end": "2025-12-15",
                "color": "red",
                "special_notes": "Approximately 4 field trips during semester, Material Fee: $200"
            }
        ]

        # 星期映射
        self.day_mapping = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6
        }

    def get_all_course_dates(self, course: Dict[str, Any]) -> List[datetime]:
        """获取某门课程的所有上课日期"""
        start_date = datetime.strptime(course["semester_start"], "%Y-%m-%d")
        end_date = datetime.strptime(course["semester_end"], "%Y-%m-%d")

        # 找到学期开始后的第一个上课日
        target_weekday = self.day_mapping[course["day"]]
        current_date = start_date

        # 移动到第一个目标星期几
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead <= 0:  # 目标日在今天或之前
            days_ahead += 7
        first_class = current_date + timedelta(days=days_ahead)

        # 如果开始日期正好是目标星期几
        if current_date.weekday() == target_weekday:
            first_class = current_date

        # 生成所有上课日期
        class_dates = []
        current_class = first_class

        while current_class <= end_date:
            class_dates.append(current_class)
            current_class += timedelta(weeks=1)  # 每周一次

        return class_dates

    def create_calendar_event(self, course: Dict[str, Any], date: datetime) -> Dict[str, Any]:
        """创建日历事件"""
        start_time_str = course["start_time"]
        end_time_str = course["end_time"]

        # 解析时间
        start_hour, start_minute = map(int, start_time_str.split(":"))
        end_hour, end_minute = map(int, end_time_str.split(":"))

        # 创建完整的开始和结束时间
        start_datetime = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_datetime = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

        # 格式化为Google Calendar API需要的格式
        start_time_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")

        event = {
            "summary": f"{course['code']}: {course['name']}",
            "description": f"教师: {course['instructor']}\\n课程代码: {course['code']} (CRN: {course['crn']})\\n" +
                          (f"\\n特殊说明: {course['special_notes']}" if course.get('special_notes') else ""),
            "location": course["location"],
            "start": {
                "dateTime": start_time_iso,
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": end_time_iso,
                "timeZone": "America/New_York"
            },
            "recurrence": [],  # 我们会为每个日期创建单独的事件
            "reminders": {
                "useDefault": True
            }
        }

        return event

    def add_courses_to_calendar(self) -> Dict[str, Any]:
        """将所有课程添加到Google Calendar"""
        try:
            logger.info("开始添加课程到Google Calendar")

            # 检查认证
            if not self.auth_manager.is_google_authenticated():
                return {"success": False, "error": "Google认证已过期，请重新认证"}

            token = self.auth_manager.get_google_token()
            if not token or token.is_expired:
                return {"success": False, "error": "Google认证令牌无效"}

            import requests

            total_events = 0
            added_events = 0
            errors = []
            course_summary = {}

            for course in self.courses:
                try:
                    course_name = f"{course['code']}: {course['name']}"
                    logger.info(f"处理课程: {course_name}")

                    # 获取所有上课日期
                    class_dates = self.get_all_course_dates(course)
                    logger.info(f"课程 {course['code']} 共有 {len(class_dates)} 次课")

                    course_events = 0

                    for date in class_dates:
                        try:
                            event = self.create_calendar_event(course, date)

                            # 发送到Google Calendar API
                            api_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
                            headers = {
                                'Authorization': token.authorization_header,
                                'Content-Type': 'application/json'
                            }

                            response = requests.post(api_url, headers=headers, json=event)

                            if response.status_code == 200:
                                course_events += 1
                                added_events += 1
                                logger.info(f"成功添加: {course['code']} - {date.strftime('%Y-%m-%d')}")
                            else:
                                error_msg = f"添加事件失败 {course['code']} {date.strftime('%Y-%m-%d')}: {response.status_code}"
                                errors.append(error_msg)
                                logger.error(error_msg)

                            total_events += 1

                        except Exception as e:
                            error_msg = f"处理日期 {date.strftime('%Y-%m-%d')} 时出错: {str(e)}"
                            errors.append(error_msg)
                            logger.error(error_msg)

                    course_summary[course['code']] = {
                        "name": course['name'],
                        "total_classes": len(class_dates),
                        "added_events": course_events,
                        "day": course['day'],
                        "time": f"{course['start_time']}-{course['end_time']}",
                        "location": course['location']
                    }

                except Exception as e:
                    error_msg = f"处理课程 {course.get('code', 'Unknown')} 时出错: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)

            result = {
                "success": True,
                "total_events": total_events,
                "added_events": added_events,
                "course_summary": course_summary
            }

            if errors:
                result["errors"] = errors

            logger.info(f"完成课程添加: {added_events}/{total_events} 个事件成功添加")
            return result

        except Exception as e:
            logger.error(f"添加课程到日历失败: {e}")
            return {"success": False, "error": str(e)}

    def print_course_schedule(self):
        """打印课程时间表"""
        print("\\n📚 2025年秋季学期课程安排\\n")
        print("=" * 80)

        for course in self.courses:
            print(f"\\n📖 {course['name']}")
            print(f"   课程代码: {course['code']} (CRN: {course['crn']})")
            print(f"   教师: {course['instructor']}")
            print(f"   时间: 每周{course['day']} {course['start_time']}-{course['end_time']}")
            print(f"   地点: {course['location']}")
            print(f"   学期: {course['semester_start']} 至 {course['semester_end']}")

            if course.get('special_notes'):
                print(f"   特殊说明: {course['special_notes']}")

            # 计算总课时
            class_dates = self.get_all_course_dates(course)
            print(f"   总课时: {len(class_dates)} 次课")


def main():
    """主函数"""
    try:
        manager = CourseScheduleManager()

        # 首先显示课程安排
        manager.print_course_schedule()

        print("\\n" + "=" * 80)
        print("正在将课程添加到Google Calendar...")

        # 添加到日历
        result = manager.add_courses_to_calendar()

        if result["success"]:
            print("\\n✅ 课程添加完成!")
            print(f"   成功添加事件: {result['added_events']}/{result['total_events']}")

            print("\\n📅 课程概要:")
            for code, info in result['course_summary'].items():
                print(f"   • {code}: {info['name']}")
                print(f"     时间: 每周{info['day']} {info['time']}")
                print(f"     地点: {info['location']}")
                print(f"     课时: {info['added_events']}/{info['total_classes']} 次课已添加")

            if result.get('errors'):
                print("\\n⚠️ 部分错误:")
                for error in result['errors']:
                    print(f"   - {error}")

            return 0
        else:
            print(f"\\n❌ 添加失败: {result.get('error', '未知错误')}")
            return 1

    except Exception as e:
        print(f"\\n❌ 程序执行出错: {e}")
        return 1


if __name__ == "__main__":
    exit(main())