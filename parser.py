from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import sys


driver_path = ChromeDriverManager().install()

def scrape_magtu_data():
    global driver_path
    # Проверяем и устанавливаем зависимости для Linux

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1920,1080")
    
    # Установка ChromeDriver
    
    # Проверяем существование драйвера
    # if not os.path.exists(driver_path):
    #     raise FileNotFoundError(f"ChromeDriver не найден по пути: {driver_path}")

    # Устанавливаем права
    # os.chmod(driver_path, 0o755)
    
    # Создаем сервис
    service = webdriver.ChromeService(driver_path)
    
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Ошибка при запуске Chrome: {str(e)}")
        print("Попытка установки дополнительных зависимостей...")
        if sys.platform == 'linux':
            os.system('apt-get install -y libgbm1')
        driver = webdriver.Chrome(service=service, options=options)
    
    result_dict = {}
    
    try:
        driver.get("https://www.magtu.ru/abit/6013-spiski-podavshikh-dokumenty-byudzhetnye-mesta.html")
        time.sleep(3)
        
        # Выбираем институт
        institute_select = Select(driver.find_element(By.ID, "dep"))
        institute_select.select_by_value("08")
        time.sleep(2)
        
        # Ждем загрузки и выбираем специальность
        time.sleep(3)
        spec_select = Select(driver.find_element(By.ID, "spec"))
        found_specialty = False
        for option in spec_select.options:
            if "Web-приложений" in option.text:
                option.click()
                found_specialty = True
                break
        
        if not found_specialty:
            print("Специальность 'Web-приложений' не найдена")
            return {}
        
        # Парсим таблицу
        time.sleep(3)
        table = driver.find_element(By.CSS_SELECTOR, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Пропускаем заголовок
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) < 8:
                continue
                
            snils_id = cells[0].text.strip()
            
            # Проверяем наличие класса 'yes' в строке
            admitted = "yes" in row.get_attribute("class").split()
            
            result_dict[snils_id] = {
                "Баллы": cells[1].text.strip(),
                "Доп": cells[2].text.strip(),
                "Оригинал": cells[4].text.strip(),
                "Основание приема": cells[5].text.strip(),
                "Приоритет": int(cells[7].text.strip()),
                "Поступил": admitted
            }
        
        return result_dict
        
    except Exception as e:
        print(f"Произошла ошибка при работе: {str(e)}")
        return {}
    finally:
        driver.quit()

if __name__ == "__main__":
    data = scrape_magtu_data()
    print("Полученные данные:")
    for snils, info in data.items():
        print(f"\nСНИЛС/ID: {snils}")
        for key, value in info.items():
            print(f"{key}: {value}")