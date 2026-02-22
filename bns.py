from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.keys import Keys

# Initialize the Chrome driver
service = Service(executable_path=r"C:\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(service=service, options=options)


def robust_click(driver, element, retries=6, pause=0.2):
    """Try multiple click strategies on a WebElement until success or retries exhausted.

    Returns True if a click was performed, False if the element became stale or click failed.
    """

    def highlight_click_target():
        try:
            driver.execute_script(
                """
                const el = arguments[0];
                const duration = arguments[1];
                if (!el) return;
                const previousOutline = el.style.outline;
                const previousOffset = el.style.outlineOffset;
                el.style.outline = '3px solid red';
                el.style.outlineOffset = '2px';
                setTimeout(() => {
                    el.style.outline = previousOutline;
                    el.style.outlineOffset = previousOffset;
                }, duration);
                """,
                element,
                500,
            )
        except Exception:
            pass

    for attempt in range(retries):
        try:
            highlight_click_target()
            ActionChains(driver).move_to_element(element).pause(0.05).click().perform()
            return True
        except (ElementClickInterceptedException, WebDriverException):
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center', inline:'center'});",
                    element,
                )
                highlight_click_target()
                driver.execute_script("arguments[0].click();", element)
                return True
            except StaleElementReferenceException:
                return False
            except Exception:
                time.sleep(pause)
        except StaleElementReferenceException:
            return False
        time.sleep(pause)
    return False
link = input("Enter the bushiroad order link: ")
tracking = input("Enter the tracking number: ")
bns_user = input("Enter your BNS email: ")
bns_pass = input("Enter your BNS password: ")
try:
    # Navigate to website
    driver.get(link)
    
    # If the button exists, press it repeatedly until it no longer exists
    button_xpath = "/html/body/div[1]/div[1]/div/div[1]/div/div/main/div/div/div/div/div[2]/div/div[2]/div/section/div/div/section/div[2]/div/div/div[1]/div[1]/div/div[3]/div/button"
    max_clicks = 50
    clicks = 0
    time.sleep(5)
    while True:
        buttons = driver.find_elements(By.XPATH, button_xpath)
        if not buttons:
            break
        btn = buttons[0]
        # Attempt robust click; if element becomes stale, re-find on next loop iteration
        success = robust_click(driver, btn)
        if not success:
            try:
                driver.execute_script("arguments[0].click();", btn)
            except Exception:
                break
        clicks += 1
        if clicks >= max_clicks:
            print(f"Reached max clicks ({max_clicks}), stopping.")
            break
        try:
            WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.XPATH, button_xpath)))
        except TimeoutException:
            # If it doesn't disappear quickly, continue and attempt again until max_clicks
            time.sleep(0.5)

    # Wait for items container to load (up to 10 seconds)
    items_xpath = "/html/body/div[1]/div[1]/div/div[1]/div/div/main/div/div/div/div/div[2]/div/div[2]/div/section/div/div/section/div[2]/div/div/div[1]"
    items = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, items_xpath))
    )

    # Print text for each element in items (e.g., descendant span elements)
    text_elements = items.find_elements(By.XPATH, ".//span")
    quantity_list = []
    item_list = []
    price_list = []
    rotate = 0
    for idx, text_element in enumerate(text_elements, start=1):
        text = text_element.text.strip()
        if text:
            # print(f"{idx}: {text}")
            if rotate == 0:
                parent = text_element.find_element(By.XPATH, "..")
                int_quantity = int(parent.text.strip().split("\n")[1])
                quantity_list.append(int_quantity)
                # print(parent.text.strip())
            if rotate == 1:
                # print(f"item: {text}")
                item_list.append(text)
            if rotate == 2:
                # print(f"price: {text}")
                # print(text.replace("￥", "").replace(",", ""))
                price_list.append(int(text.replace("￥", "").replace(",", "")))
            rotate += 1
            if rotate == 3:
                # print("-----")
                rotate = 0
    for quantity, item, price in zip(quantity_list, item_list, price_list):
        print(f"Quantity: {quantity}, Item: {item}, Price: ￥{int(price/quantity)}")
    driver.get("https://www.buyandship.today/")
    time.sleep(2)
    login_user_xpath = "/html/body/div[1]/div/div/section/div/section[1]/div/div[2]/div/div/div/div/div[2]/div[1]/div/input"
    login_user_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, login_user_xpath))
    )
    login_user_element.send_keys(bns_user)
    login_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/section/div/section[1]/div/div[2]/div/div/div/div/button"))
    )
    if not robust_click(driver, login_button):
        try:
            driver.execute_script("arguments[0].click();", login_button)
        except Exception:
            pass
    password_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/section/div/section[1]/div/div[2]/div/aside/div[2]/div[2]/div/div/div[1]/div/input"))
    )
    password_input.send_keys(bns_pass)
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/div/section/div/section[1]/div/div[2]/div/aside/div[2]/div[3]/button"))
    )
    submit_button.click()
    time.sleep(0.2)
    driver.get("https://www.buyandship.today/account/v2020/shipments/new/")
    time.sleep(0.2)
    el = driver.find_element(By.XPATH, "/html/body/div[3]/div[3]/div/div[1]/div[2]/div/div/p")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[3]/div/div[1]/div[2]/div/div/p"))
    )
    if not robust_click(driver, el):
        try:
            driver.execute_script("arguments[0].click();", el)
        except Exception:
            pass
    driver.get("https://www.buyandship.today/account/v2020/shipments/new/")
    time.sleep(0.2)
    el = driver.find_element(By.CLASS_NAME, "bs-select__content")
    if not robust_click(driver, el):
        try:
            driver.execute_script("arguments[0].click();", el)
        except Exception:
            pass
    time.sleep(0.2)
    places = driver.find_elements(By.CLASS_NAME, "shipment-warehouse-list__option")
    try:
        if not robust_click(driver, places[4]):
            driver.execute_script("arguments[0].click();", places[4])
    except Exception:
        pass
    time.sleep(0.2)
    tracking_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='請輸入貨件追蹤編號']"))
    )
    tracking_input.send_keys(tracking)
    time.sleep(0.2)
    
    
    item_num = 0
    for quantity, item, price in zip(quantity_list, item_list, price_list):
        if item_num == 0:
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='新增產品']/.."))
            )
            if not robust_click(driver, button):
                try:
                    driver.execute_script("arguments[0].click();", button)
                except Exception:
                    pass
        else:
            button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='新增']/.."))
            )
            if not robust_click(driver, button):
                try:
                    driver.execute_script("arguments[0].click();", button)
                except Exception:
                    pass
        item_num += 1
        time.sleep(0.2)
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='按此選擇產品類別']/.."))
        )
        if not robust_click(driver, button):
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                pass
        time.sleep(0.2)
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='遊戲及影音娛樂']/.."))
        )
        if not robust_click(driver, button):
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                pass
        time.sleep(0.2)
        button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//span[text()='娛樂收藏']/.."))
        )
        time.sleep(0.2)
        if not robust_click(driver, button):
            try:
                driver.execute_script("arguments[0].click();", button)
            except Exception:
                pass
        quant_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bs-icon--add"))
        )
        name_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='請輸入產品名稱']"))
        )
        name_input.send_keys(item)
        price_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='請輸入產品「單件」售價']"))
        )
        price_input.send_keys(str(price))
        for _ in range(quantity-1):
            if not robust_click(driver, quant_button):
                try:
                    driver.execute_script("arguments[0].click();", quant_button)
                except Exception:
                    pass
        # time.sleep(100)
        test_btn = driver.find_elements(By.XPATH, "/html/body/div[3]/div[3]/div/div[2]/div[5]/div/div/div[2]/div[2]/div/div[4]/div[2]/div/a/div")
        # print("found test btn", len(test_btn))
        add_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "bs-button-normal--round-edge"))
        )
        # print(len(add_buttons))
        add_button = add_buttons[2]
        time.sleep(0.2)
        driver.execute_script("arguments[0].scrollIntoView(true);", add_button)
        time.sleep(0.5)
        if not robust_click(driver, add_button):
            try:
                driver.execute_script("arguments[0].click();", add_button)
            except Exception:
                pass
        # print("pass")
        # break
        # time.sleep(100)
    check_box = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[3]/div[3]/div/main/div[3]/section/main/div/div/div[2]/div/div[2]/div[1]/div[2]/div/label/span"))
    )
    if not robust_click(driver, check_box):
        try:
            driver.execute_script("arguments[0].click();", check_box)
        except Exception:
            pass
    continue_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "bs-button-normal--round-edge"))
        )
    continue_button = continue_buttons[0]
    if not robust_click(driver, continue_button):
        try:
            driver.execute_script("arguments[0].click();", continue_button)
        except Exception:
            pass
    ins_button = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[3]/div[3]/div/main/div[3]/section/main/div/div/div[4]/div/div[3]/label[2]/div/div/div/div[1]/div[2]/label/span"))
        )[0]
    if not robust_click(driver, ins_button):
        try:
            driver.execute_script("arguments[0].click();", ins_button)
        except Exception:
            pass
    continue_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "/html/body/div[3]/div[3]/div/main/div[3]/section/main/div/div/div[4]/div/div[3]/div/button"))
        )
    continue_button = continue_buttons[0]
    if not robust_click(driver, continue_button):
        try:
            driver.execute_script("arguments[0].click();", continue_button)
        except Exception:
            pass
    continue_buttons = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "bs-button-normal--round-edge"))
        )
    continue_button = continue_buttons[1]
    if not robust_click(driver, continue_button):
        try:
            driver.execute_script("arguments[0].click();", continue_button)
        except Exception:
            pass
    time.sleep(10)
finally:
    # Close the browser
    driver.quit()