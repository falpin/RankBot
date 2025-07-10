from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
import sys

# Глобальные переменные для кэширования драйвера и сервиса
_DRIVER_INSTALLED = False
_SERVICE = None

def install_dependencies():
    """Устанавливает зависимости только один раз при первом запуске"""
    global _DRIVER_INSTALLED, _SERVICE
    
    if _DRIVER_INSTALLED:
        return _SERVICE
    
    # Проверяем и устанавливаем ChromeDriver
    driver_path = ChromeDriverManager().install()
    
    if not os.path.exists(driver_path):
        raise FileNotFoundError(f"ChromeDriver не найден по пути: {driver_path}")

    os.chmod(driver_path, 0o755)
    
    # Создаем сервис
    _SERVICE = Service(driver_path)
    _DRIVER_INSTALLED = True
    
    return _SERVICE

def scrape_magtu_data():
    global _SERVICE
    
    # Проверяем и устанавливаем зависимости (только при первом вызове)
    if not _DRIVER_INSTALLED:
        _SERVICE = install_dependencies()
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        driver = webdriver.Chrome(service=_SERVICE, options=options)
    except Exception as e:
        print(f"Ошибка при запуске Chrome: {str(e)}")
        return {}
    
    result_dict = {}
    
    try:
        driver.get("https://www.magtu.ru/abit/6013-spiski-podavshikh-dokumenty-byudzhetnye-mesta.html")
        time.sleep(2)
        
        # Выбираем институт
        institute_select = Select(driver.find_element(By.ID, "dep"))
        institute_select.select_by_value("08")
        time.sleep(1)
        
        # Ждем загрузки и выбираем специальность
        time.sleep(2)
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
        time.sleep(2)
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
    # Первый вызов - будет установка драйвера
    data1 = scrape_magtu_data()
    print(f"Найдено {len(data1)} записей")
    
    # Последующие вызовы - используют уже установленный драйвер
    data2 = scrape_magtu_data()
    print(f"Найдено {len(data2)} записей")