from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATA_FILE = os.getenv("DATA_FILE")
CACHE_EXPIRE_HOURS = 1

def is_cache_valid():
    if not os.path.exists(DATA_FILE):
        return False
    
    file_time = os.path.getmtime(DATA_FILE)
    cache_age = (time.time() - file_time) / 3600
    return cache_age < CACHE_EXPIRE_HOURS

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'data': data
        }, f, ensure_ascii=False, indent=2)

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = json.load(f)
            return content['data']
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def setup_driver():  # настройки драйвера
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # Увеличиваем время ожидания для WebDriverManager
    os.environ['WDM_LOCAL'] = '1'
    os.environ['WDM_LOG_LEVEL'] = '0'
    
    try:
        # Устанавливаем ChromeDriver с явным указанием версии
        driver_path = ChromeDriverManager().install()
        
        # Проверяем, что файл существует
        if not os.path.exists(driver_path):
            raise FileNotFoundError(f"ChromeDriver не найден по пути: {driver_path}")

        # Устанавливаем права
        os.chmod(driver_path, 0o755)
        
        # Создаем сервис с установленным драйвером
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 1)  # Увеличиваем время ожидания до 1 секунд
        
        return driver, wait
        
    except Exception as e:
        print(f"Произошла ошибка при настройке драйвера: {str(e)}")
        return None, None


def scrape_magtu_data(speciality):
    if is_cache_valid():
        cached_data = load_data()
        if cached_data:
            print("Используются кэшированные данные")
            return cached_data

    driver, wait = setup_driver()
    if not driver or not wait:
        return {}
    
    result_dict = {}
    
    try:
        print("Открываем страницу")
        driver.get("https://www.magtu.ru/abit/6013-spiski-podavshikh-dokumenty-byudzhetnye-mesta.html")
        
        institute_select = wait.until(EC.presence_of_element_located((By.ID, "dep")))
        Select(institute_select).select_by_value("16")
        
        spec_select = wait.until(EC.presence_of_element_located((By.ID, "spec")))
        found_specialty = False
        for option in Select(spec_select).options:
            if speciality in option.text:
                option.click()
                found_specialty = True
                break
        
        if not found_specialty:
            print(f"Специальность '{speciality}' не найдена")
            return {}
        
        time.sleep(0.3)  # дополнительное время для загрузки таблицы
        
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Пропускаем заголовок
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                continue
                
            snils_id = cells[0].text.strip()
            
            admitted = "yes" in row.get_attribute("class").split()
            
            result_dict[snils_id] = {
                "Баллы": cells[1].text.strip(),
                "Доп": cells[2].text.strip(),
                "Оригинал": cells[4].text.strip(),
                "Основание приема": cells[5].text.strip(),
                "Приоритет": int(cells[7].text.strip()),
                "Поступил": admitted,
                "Экзамены": cells[3].text.strip()
            }
        save_data(result_dict)
        return result_dict
        
    except Exception as e:
        print(f"Произошла ошибка при работе с сайтом: {str(e)}")
        return {}
    finally:
        driver.quit()


def get_applicant_priorities(snils):
    """
    Получает список приоритетов абитуриента по его СНИЛС
    Возвращает список словарей с информацией о приоритетах
    """
    driver, wait = setup_driver()
    if not driver or not wait:
        return []
    
    try:
        driver.get("https://www.magtu.ru/abit/rating.php")
        
        snils_input = wait.until(EC.presence_of_element_located((By.ID, "id_abitur")))
        snils_input.clear()
        snils_input.send_keys(snils)
        
        search_button = wait.until(EC.element_to_be_clickable((By.ID, "poisk_abitur")))
        search_button.click()
        
        time.sleep(0.1)
        
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_wrapper table.table_abit")))
        
        priorities = []
        table_wrapper = driver.find_element(By.CLASS_NAME, "table_wrapper")
        table = table_wrapper.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Пропускаем заголовок
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 5:
                continue
                
            priority = {
                "Приоритет": int(cells[0].text.strip()),
                "Направление": cells[1].text.strip(),
                "Форма обучения": cells[2].text.strip(),
                "Основание приема": cells[3].text.strip(),
                "Баллы": int(cells[4].text.strip()) if cells[4].text.strip().isdigit() else 0
            }
            priorities.append(priority)
            
        return priorities
        
    except Exception as e:
        print(f"Ошибка при получении приоритетов для СНИЛС {snils}: {str(e)}")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    data = scrape_magtu_data()
