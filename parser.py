from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os

def scrape_magtu_data():
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
        wait = WebDriverWait(driver, 20)  # Увеличиваем время ожидания до 20 секунд
        
        result_dict = {}
        
        try:
            # Открываем страницу
            driver.get("https://www.magtu.ru/abit/6013-spiski-podavshikh-dokumenty-byudzhetnye-mesta.html")
            time.sleep(3)  # Даем время для полной загрузки страницы
            
            # Ждем и выбираем институт
            institute_select = wait.until(EC.presence_of_element_located((By.ID, "dep")))
            Select(institute_select).select_by_value("08")
            time.sleep(2)  # Даем время для обновления данных
            
            # Ждем и выбираем специальность
            spec_select = wait.until(EC.presence_of_element_located((By.ID, "spec")))
            found_specialty = False
            for option in Select(spec_select).options:
                if "Web-приложений" in option.text:
                    option.click()
                    found_specialty = True
                    break
            
            if not found_specialty:
                print("Специальность 'Web-приложений' не найдена")
                return {}
            
            # Даем дополнительное время для загрузки таблицы
            time.sleep(3)
            
            # Парсим таблицу
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
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
            print(f"Произошла ошибка при работе с сайтом: {str(e)}")
            return {}
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Произошла ошибка при настройке драйвера: {str(e)}")
        return {}

# Пример использования
if __name__ == "__main__":
    data = scrape_magtu_data()
    print("Полученные данные:")
    for snils, info in data.items():
        print(f"\nСНИЛС/ID: {snils}")
        for key, value in info.items():
            print(f"{key}: {value}")