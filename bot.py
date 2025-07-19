VERSION="1.0.4.2"

import requests
import json
from TelegramTextApp.database import SQL_request
import TelegramTextApp
import os
from dotenv import load_dotenv
import parser
import json
from datetime import datetime, timedelta
from TelegramTextApp.utils import markdown

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    DATABASE = os.getenv("DATABASE")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    TelegramTextApp.start(TOKEN, "bot.json", DATABASE, debug=DEBUG)


async def create_tables():
    await create_users()
    await create_specialties()

async def create_users():
    await SQL_request('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        snils TEXT,
        speciality JSON,
        FOREIGN KEY (telegram_id) REFERENCES TTA(telegram_id)
    )''')

async def create_specialties():
    await SQL_request('''
    CREATE TABLE IF NOT EXISTS specialties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        time_add TIMESTAMP,
        data JSON
    )''')


async def count_eligible_users(data, select_points=200):
    count = 0
    for user_data in data.values():
        try:
            points = int(user_data["Баллы"].replace(' ', ''))
            priority = user_data["Приоритет"]
            admitted = user_data["Поступил"]
            
            if points > select_points and priority == 1:
                count += 1
        except (ValueError, KeyError):
            continue
    return count

async def get_min_score_top_25_priority1(data):
    priority1_users = []
    
    for user_data in data.values():
        try:
            if user_data["Приоритет"] == 1:
                points = int(user_data["Баллы"].replace(' ', ''))
                priority1_users.append(points)
        except (ValueError, KeyError):
            continue
    
    if len(priority1_users) < 25:
        return 100
    
    top25 = sorted(priority1_users, reverse=True)[:25]
    
    return top25[-1]

async def exams(data, snils):
    if snils not in data:
        return "Данные не найдены"
    
    student_data = data[snils]
    exams_str = student_data.get("Экзамены", "")
    
    # Определяем тип сдачи (егэ/вуз)
    exam_type = "егэ" if "егэ" in exams_str.lower() else "вуз"
    
    # Получаем баллы
    total_points = student_data.get("Баллы", "0")
    additional_points = student_data.get("Доп", "0")
    points = str(int(total_points) - int(additional_points)) if additional_points.isdigit() and total_points.isdigit() else total_points
    
    # Разбираем экзамены и сопоставляем с предметами
    exam_scores = []
    for exam in exams_str.split(','):
        exam = exam.strip()
        if '-' in exam:
            exam = exam.split('-')[1].strip()
        exam = exam.split('(')[0].strip()
        exam_scores.append(exam)
    
    # Предметы в нужном порядке
    subjects = ["Русский", "Математика", "Информатика"]
    
    # Формируем результат
    result = [
        f"*Всего баллов:* `{total_points}`",
        f"**>*Тип:* {exam_type}",
        f">*Дополнительные баллы:* {additional_points}",
        f">",
        ">*Баллы за экзамены:*"
    ]
    
    # Добавляем предметы с баллами
    for subject, score in zip(subjects, exam_scores):
        result.append(f">*{subject}:* {score}")
    
    text = "\n".join(result)
    text = (f"{text}\n>*Итого:* {points}")
    return text


async def get_speciality(tta_data):
    user_data = await SQL_request("SELECT * FROM users WHERE telegram_id=?", (tta_data["telegram_id"],), 'one')
    snils = user_data['snils']
    speciality = json.loads(user_data["speciality"])
    speciality = speciality[int(tta_data["spec_number"])]

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result = await SQL_request("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not result:
        await create_tables()



    speciality_data = await SQL_request("SELECT * FROM specialties WHERE name=?", (speciality["Направление"],), 'one')
    if not speciality_data:
        rank_data = parser.scrape_magtu_data(speciality["Направление"])
        await SQL_request('INSERT INTO specialties (name, time_add, data) VALUES (?, ?, ?)', (speciality["Направление"], current_time, json.dumps(rank_data)))

    if speciality_data:
        time_add_dt = datetime.strptime(speciality_data['time_add'], '%Y-%m-%d %H:%M:%S')
        current_time_dt = datetime.strptime(current_time, '%Y-%m-%d %H:%M:%S')
        if current_time_dt - time_add_dt > timedelta(hours=1):
            rank_data = parser.scrape_magtu_data(speciality["Направление"])
            await SQL_request("UPDATE specialties SET data = ?, time_add=? WHERE name = ?", (json.dumps(rank_data), current_time, speciality["Направление"]))
        else:
            rank_data = (speciality_data["data"])


    data = {}
    
    if rank_data:
        count_priority = sum(1 for info in rank_data.values() if info.get("Приоритет") == 1)
        admitted_students = {student_snils: info for student_snils, info in rank_data.items() if info.get("Поступил")}
        admitted_points = [int(info["Баллы"]) for info in admitted_students.values()]
        
        points = None
        
        if snils in rank_data:
            points = int(rank_data[snils]["Баллы"])
        
        admitted_pos = None
        
        if points is not None:
            admitted_pos = sum(1 for all_points in admitted_points if all_points > points) + 1
        

        data = {
            'speciality_name': markdown(speciality["Направление"], True),
            'total_students': len(rank_data),
            'admitted_students': len(admitted_points),
            'count_priority': count_priority,
            'admitted_position': admitted_pos,  # Исправлено
            'count_eligible_users_200': await count_eligible_users(rank_data, 200),
            'get_min_score': await get_min_score_top_25_priority1(rank_data),
            'exams': await exams(rank_data, snils),
        }

    return data

async def user_speciality(tta_data):
    result = await SQL_request("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not result:
        await create_tables()

    telegram_id = tta_data["telegram_id"]
    user_data = await SQL_request("SELECT * FROM users WHERE telegram_id=?", (telegram_id,), 'one')

    if not user_data:
        return {"snils":"Укажите снилc"}

    if not user_data["snils"]:
        return {"snils":"Укажите снилс"}

    if not user_data["speciality"]:
        data = parser.get_applicant_priorities(user_data['snils'])
        if data:
            await SQL_request("UPDATE users SET speciality = ? WHERE telegram_id = ?", (json.dumps(data), telegram_id))
            keyboard = {}
            i = 0
            for speciality in data:
                keyboard[f"speciality|{i}"] = f"\\{speciality['Направление']}"
                i += 1
            return keyboard
        else:
            return {"main":"Обновить"}

    if user_data["speciality"]:
        keyboard = {}
        i = 0
        for speciality in json.loads(user_data["speciality"]):
            keyboard[f"speciality|{i}"] = f"\\{speciality['Направление']}"
            i += 1
        return keyboard

async def add_snils(tta_data):  # добавление снилса в базу
    telegram_id = tta_data["telegram_id"]
    snils = tta_data.get("snils")
    token_data = await SQL_request("SELECT * FROM users WHERE telegram_id=?", (telegram_id,), 'one')
    if token_data:
        await SQL_request("UPDATE users SET snils = ? WHERE telegram_id = ?", (snils, telegram_id))
    else:
        await SQL_request('INSERT INTO users (telegram_id, snils) VALUES (?, ?)', (telegram_id, snils))