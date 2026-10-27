# engine.py
import time
import json
import random
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from database import YandexDB


class YandexMapScraper:
    def __init__(self, keyword, scroll_count=10):
        self.keyword = keyword
        self.scroll_count = scroll_count
        encoded_keyword = urllib.parse.quote(keyword)
        self.target_url = f"https://yandex.com/maps/213/moscow/search/{encoded_keyword}/"
        self.db = YandexDB()

    def init_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--window-size=1400,900")
        options.add_argument("--lang=en-US")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=options
        )
        return driver

    def _extract_from_state_json(self, driver):
        """검색 결과 페이지의 <script class="state-view"> JSON 에서 구조화된 데이터 추출"""
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, "script.state-view")
            if not scripts:
                return []
            raw = scripts[-1].get_attribute("innerHTML")
            state = json.loads(raw)
        except Exception as e:
            print(f"[-] state-view 파싱 실패: {e}")
            return []

        results = []
        stack = state.get("stack", [])
        for frame in stack:
            if frame.get("mode") != "search":
                continue
            res = frame.get("results") or {}
            for item in res.get("items", []):
                if item.get("type") != "business":
                    continue
                title = item.get("title") or "N/A"
                address = item.get("fullAddress") or item.get("address") or "N/A"

                phones = item.get("phones") or []
                phone = phones[0].get("number") if phones else "N/A"

                urls = item.get("urls") or []
                website = urls[0] if urls else ""

                rating_data = item.get("ratingData") or {}
                rating = rating_data.get("ratingValue", "0.0")
                rating = str(rating)

                results.append({
                    "title": title,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "rating": rating,
                })
        return results

    def _enrich_from_org_page(self, driver, org_url):
        """상세 페이지에서 전화번호/웹사이트/평점 추출"""
        data = {"phone": "N/A", "website": "", "rating": "0.0"}
        try:
            driver.get(org_url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1.card-title-view__title, h1.orgpage-header-view__header")
                )
            )
            time.sleep(1.5)

            # 전화번호: "전화번호 표시" 버튼이 있으면 먼저 클릭
            try:
                more_btn = driver.find_element(By.CSS_SELECTOR, ".card-phones-view__more")
                driver.execute_script("arguments[0].click();", more_btn)
                time.sleep(1.0)
            except Exception:
                pass
            for sel in (".card-phones-view__phone-number", ".business-contacts-view__phone"):
                try:
                    data["phone"] = driver.find_element(By.CSS_SELECTOR, sel).text.strip() or "N/A"
                    if data["phone"] != "N/A":
                        break
                except Exception:
                    continue

            for sel in (".business-urls-view__link", "a[itemprop='url']"):
                try:
                    data["website"] = driver.find_element(By.CSS_SELECTOR, sel).get_attribute("href") or ""
                    if data["website"]:
                        break
                except Exception:
                    continue

            for sel in (".business-rating-badge-view__rating-text", ".business-header-rating-view__text"):
                try:
                    data["rating"] = driver.find_element(By.CSS_SELECTOR, sel).text.strip() or "0.0"
                    if data["rating"]:
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"[-] 상세 페이지 보완 실패 ({org_url}): {e}")
        return data

    def start_sync(self):
        # ✅ [핵심] 같은 키워드의 기존 데이터만 삭제 (다른 키워드는 보존)
        deleted = self.db.delete_by_keyword(self.keyword)
        if deleted:
            print(f"[+] '{self.keyword}' 기존 데이터 {deleted}건 삭제 후 재수집")

        driver = self.init_driver()
        print(f"[+] Accessing Yandex Maps: {self.target_url}")
        driver.get(self.target_url)

        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.search-list-view__list")))
            sidebar = driver.find_element(By.CSS_SELECTOR, "ul.search-list-view__list")

            print(f"[+] Starting infinite scroll ({self.scroll_count} iterations)...")
            for _ in range(self.scroll_count):
                driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);", sidebar
                )
                time.sleep(2.0)
        except Exception as e:
            print(f"[-] 목록 로딩 예외: {e}")

        items = self._extract_from_state_json(driver)
        print(f"[+] state-view JSON에서 {len(items)}건 추출")

        if not items:
            cards = driver.find_elements(By.CSS_SELECTOR, "li.search-snippet-view")
            print(f"[+] DOM에서 {len(cards)}건 카드 발견")
            for card in cards:
                try:
                    title = card.find_element(By.CSS_SELECTOR, ".search-business-snippet-view__title").text
                except Exception:
                    title = "N/A"
                try:
                    address = card.find_element(By.CSS_SELECTOR, ".search-business-snippet-view__address").text
                except Exception:
                    address = "N/A"
                if title != "N/A":
                    items.append({
                        "title": title, "address": address,
                        "phone": "N/A", "website": "", "rating": "0.0",
                        "org_url": None,
                    })

        for item in items:
            if item.get("phone") == "N/A" and not item.get("website"):
                org_url = item.get("org_url")
                if not org_url:
                    try:
                        link = driver.find_element(
                            By.XPATH,
                            f"//a[contains(@class,'link-overlay') and @aria-label='{item['title']}']"
                        )
                        href = link.get_attribute("href")
                        if href:
                            org_url = href if href.startswith("http") else "https://yandex.com" + href
                    except Exception:
                        pass
                if org_url:
                    extra = self._enrich_from_org_page(driver, org_url)
                    item.update(extra)
                    time.sleep(random.uniform(4, 9))

            self.db.insert_lead(
                self.keyword,
                item["title"], item["address"], item["phone"],
                item["website"], item["rating"],
            )

        print(f"[+] 처리 완료: {len(items)}건")
        driver.quit()