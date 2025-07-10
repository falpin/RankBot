from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
import time
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def scrape_magtu_data():
    options = Options()
    options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
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
                "Поступил": admitted  # Добавляем статус поступления
            }
        
        return result_dict
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return {}
    finally:
        driver.quit()

# Пример использования
if __name__ == "__main__":
    data = scrape_magtu_data()
    print("Полученные данные:")
    for snils, info in data.items():
        print(f"\nСНИЛС/ID: {snils}")
        for key, value in info.items():
            print(f"{key}: {value}")