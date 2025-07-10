from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import sys

def install_chrome_linux():
    """Устанавливает Chrome и необходимые зависимости в Linux"""
    if sys.platform != 'linux':
        return
    
    print("Установка Chrome и зависимостей...")
    os.system('apt-get update -y')
    os.system('apt-get install -y wget gnupg')
    os.system('wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -')
    os.system('sh -c \'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list\'')
    os.system('apt-get update -y')
    os.system('apt-get install -y google-chrome-stable')
    os.system('apt-get install -y libxss1 libappindicator1 libindicator7')
    os.system('apt-get install -y fonts-liberation libasound2 libatk-bridge2.0-0 libgtk-3-0 libnspr4 libnss3 xdg-utils')

def scrape_magtu_data():
    # Проверяем и устанавливаем зависимости для Linux
    if sys.platform == 'linux':
        install_chrome_linux()

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")
    
    # Установка ChromeDriver
    driver_path = ChromeDriverManager().install()
    
    # Проверяем существование драйвера
    if not os.path.exists(driver_path):
        raise FileNotFoundError(f"ChromeDriver не найден по пути: {driver_path}")

    # Устанавливаем права
    os.chmod(driver_path, 0o755)
    
    # Создаем сервис
    service = Service(driver_path)
    
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