VERSION="1.0.3"

import requests
import json
from TelegramTextApp.database import SQL_request
import TelegramTextApp
import os
from dotenv import load_dotenv
from parser import scrape_magtu_data

if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    DATABASE = os.getenv("DATABASE")
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
    TelegramTextApp.start(TOKEN, "bot.json", DATABASE, debug=DEBUG)

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


async def ranked(tta_data):
    load_dotenv()
    MY_SNILS = os.getenv("SNILS")
    ALINA = os.getenv("ALINA")

    rank_data = scrape_magtu_data()
    data = {}
    
    if rank_data:
        admitted_students = {snils: info for snils, info in rank_data.items() if info["Поступил"]}
        count_priority = sum(
            1 for info in rank_data.values() 
            if info.get("Приоритет") == 1
        )
        admitted_points = [int(info["Баллы"]) for info in admitted_students.values()]
        
        my_points = None
        alina_points = None
        
        if MY_SNILS in rank_data:
            my_points = int(rank_data[MY_SNILS]["Баллы"])
        if ALINA in rank_data:
            alina_points = int(rank_data[ALINA]["Баллы"])
        
        my_admitted_pos = None
        alina_admitted_pos = None
        
        if my_points is not None:
            my_admitted_pos = sum(1 for points in admitted_points if points > my_points) + 1
        
        if alina_points is not None:
            alina_admitted_pos = sum(1 for points in admitted_points if points > alina_points) + 1
        
        data.update({
            'total_students': len(rank_data),
            'admitted_students': len(admitted_points),
            'count_priority': count_priority,
            'my_admitted_position': my_admitted_pos,
            'alina_admitted_position': alina_admitted_pos,
            'count_eligible_users_200': await count_eligible_users(rank_data, 200),
            'get_min_score': await get_min_score_top_25_priority1(rank_data),
            'exams': await exams(rank_data, MY_SNILS),
            'exams_alina': await exams(rank_data, ALINA),
        })

    return data

async def create_tables():
    await SQL_request('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        snils TEXT,
        speciality JSON,
        FOREIGN KEY (telegram_id) REFERENCES TTA(telegram_id)
    )''')

async def speciality(tta_data):
    telegram_id = tta_data["telegram_id"]
    result = await SQL_request("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not result:
        await create_tables()

    user_data = await SQL_request("SELECT * FROM users WHERE telegram_id=?", (telegram_id,), 'one')
    if not user_data:
        return {"snils":"Укажите снилc"}

    if not user_data["snils"]:
        return {"snils":"Укажите снилс"}

    if not user_data["speciality"]:
        return {"snils":"Загрузка"}
        
    return {"snils":"Пппп"}

async def add_snils(tta_data):
    telegram_id = tta_data["telegram_id"]
    snils = tta_data.get("snils")
    if snils:
        token_data = await SQL_request("SELECT * FROM users WHERE telegram_id=?", (telegram_id,), 'one')
        if token_data:
            await SQL_request("UPDATE users SET snils = ? WHERE telegram_id = ?", (snils, telegram_id))
        else:
            await SQL_request('INSERT INTO users (telegram_id, snils) VALUES (?, ?)', (telegram_id, snils))
            return
    else:
        return {"error_text":"Не верный токен"}