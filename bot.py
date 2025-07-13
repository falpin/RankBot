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
            'my_points': my_points,
            'alina_points': alina_points
        })
    
    return data