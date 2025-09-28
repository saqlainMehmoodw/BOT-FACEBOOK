from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import sqlite3
import datetime
import json
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class FacebookBotWithPHP:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.php_url = "http://localhost/facebook_bot"  # Change to your PHP server URL
        self.setup_database()

    def setup_database(self):
        """SQLite database setup"""
        conn = sqlite3.connect('facebook_bot.db')
        cursor = conn.cursor()

        # Listings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                url TEXT,
                title TEXT,
                price TEXT,
                status TEXT DEFAULT 'pending',
                is_public BOOLEAN DEFAULT 0,
                is_visible BOOLEAN DEFAULT 0,
                views INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Bot logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bot_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER,
                action TEXT,
                status TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings (id)
            )
        ''')

        # Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                password TEXT,
                auto_restart BOOLEAN DEFAULT 1,
                check_interval INTEGER DEFAULT 300,
                is_running BOOLEAN DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("✅ Database setup completed")

    def send_to_php(self, data):
        """Data PHP server ko send karta hai"""
        try:
            response = requests.post(f"{self.php_url}/api.php", json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logging.error(f"PHP connection error: {e}")
            return False

    def update_php_dashboard(self, listing_data):
        """PHP dashboard ko update karta hai"""
        php_data = {
            'action': 'update_listing',
            'data': listing_data
        }
        return self.send_to_php(php_data)

    def log_to_php(self, action, status, message=""):
        """PHP mein log bhejta hai"""
        log_data = {
            'action': 'add_log',
            'data': {
                'action': action,
                'status': status,
                'message': message,
                'timestamp': datetime.datetime.now().isoformat()
            }
        }
        return self.send_to_php(log_data)

    def initialize_driver(self):
        """Driver initialize karta hai"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)

            self.log_to_php("driver_init", "success", "WebDriver initialized successfully")
            return True
        except Exception as e:
            self.log_to_php("driver_init", "error", f"Driver initialization failed: {e}")
            return False

    def login(self, email, password):
        """Facebook login"""
        try:
            self.log_to_php("login", "started", "Attempting Facebook login")

            self.driver.get("https://www.facebook.com")
            time.sleep(5)

            # Email field
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(email)

            # Password field
            password_input = self.driver.find_element(By.NAME, "pass")
            password_input.send_keys(password)

            # Login button
            login_button = self.driver.find_element(By.NAME, "login")
            login_button.click()

            time.sleep(8)

            # Login verification
            if "login" not in self.driver.current_url.lower():
                self.log_to_php("login", "success", "Login successful")
                return True
            else:
                self.log_to_php("login", "error", "Login failed")
                return False

        except Exception as e:
            self.log_to_php("login", "error", f"Login error: {e}")
            return False

    def get_listings_from_db(self):
        """Database se pending listings get karta hai"""
        try:
            conn = sqlite3.connect('facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, item_id, url, title, status
                FROM listings
                WHERE status = 'pending' OR is_public = 0
                ORDER BY created_at DESC
            ''')

            listings = cursor.fetchall()
            conn.close()

            return listings
        except Exception as e:
            logging.error(f"Database error: {e}")
            return []

    def update_listing_in_db(self, item_id, updates):
        """Database mein listing update karta hai"""
        try:
            conn = sqlite3.connect('facebook_bot.db')
            cursor = conn.cursor()

            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values())
            values.append(item_id)

            cursor.execute(f'''
                UPDATE listings
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
            ''', values)

            conn.commit()
            conn.close()

            # PHP ko bhi update bhejo
            php_data = {
                'item_id': item_id,
                **updates
            }
            self.update_php_dashboard(php_data)

            return True
        except Exception as e:
            logging.error(f"Update error: {e}")
            return False

    def add_listing_to_db(self, listing_data):
        """Database mein nayi listing add karta hai"""
        try:
            conn = sqlite3.connect('facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO listings
                (item_id, url, title, price, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                listing_data['item_id'],
                listing_data['url'],
                listing_data['title'],
                listing_data.get('price', ''),
                'pending'
            ))

            conn.commit()
            listing_id = cursor.lastrowid
            conn.close()

            # PHP ko notify karo
            self.update_php_dashboard({
                'item_id': listing_data['item_id'],
                'action': 'new_listing'
            })

            return listing_id
        except Exception as e:
            logging.error(f"Add listing error: {e}")
            return None

    def get_marketplace_listings(self):
        """Marketplace se listings collect karta hai"""
        try:
            self.driver.get("https://www.facebook.com/marketplace/you/selling")
            time.sleep(8)

            # Scroll to load listings
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Find listings
            listings = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")

            collected_listings = []
            for listing in listings:
                try:
                    url = listing.get_attribute('href')
                    if '/marketplace/item/' in url:
                        item_id = url.split('/item/')[1].split('/')[0] if '/item/' in url else None

                        # Extract title
                        title = "Unknown Title"
                        try:
                            title_elements = listing.find_elements(By.XPATH, ".//span[@dir='auto']")
                            if title_elements:
                                title = title_elements[0].text
                        except:
                            pass

                        listing_data = {
                            'item_id': item_id,
                            'url': url,
                            'title': title,
                            'price': ''  # You can add price extraction logic
                        }

                        collected_listings.append(listing_data)

                        # Database mein add karo
                        self.add_listing_to_db(listing_data)

                except Exception as e:
                    continue

            self.log_to_php("get_listings", "success", f"Found {len(collected_listings)} listings")
            return collected_listings

        except Exception as e:
            self.log_to_php("get_listings", "error", f"Error getting listings: {e}")
            return []

    def process_listings(self):
        """Saari listings process karta hai"""
        try:
            self.log_to_php("processing", "started", "Starting listings processing")

            # Database se listings lo
            db_listings = self.get_listings_from_db()

            # Agar database mein nahi hai to marketplace se collect karo
            if not db_listings:
                marketplace_listings = self.get_marketplace_listings()
                if not marketplace_listings:
                    self.log_to_php("processing", "warning", "No listings found")
                    return

            # Process each listing
            success_count = 0
            total_count = len(db_listings)

            for listing in db_listings:
                listing_id, item_id, url, title, status = listing

                self.log_to_php("process_listing", "started", f"Processing: {title}")

                # Make listing public (simplified logic)
                success = self.make_listing_public(url, item_id)

                if success:
                    self.update_listing_in_db(item_id, {
                        'status': 'processed',
                        'is_public': 1,
                        'is_visible': 1
                    })
                    success_count += 1
                    self.log_to_php("process_listing", "success", f"Made public: {title}")
                else:
                    self.update_listing_in_db(item_id, {
                        'status': 'failed',
                        'is_public': 0,
                        'is_visible': 0
                    })
                    self.log_to_php("process_listing", "error", f"Failed: {title}")

                time.sleep(3)

            # Final report
            self.log_to_php("processing", "completed",
                          f"Processed {success_count}/{total_count} listings successfully")

            return success_count, total_count

        except Exception as e:
            self.log_to_php("processing", "error", f"Processing error: {e}")
            return 0, 0

    def make_listing_public(self, url, item_id):
        """Listing ko public banata hai (simplified version)"""
        try:
            # Listing par jao
            self.driver.get(url)
            time.sleep(5)

            # Edit button dhundho
            edit_found = False
            edit_selectors = [
                "//span[contains(text(), 'Edit')]",
                "//button[contains(text(), 'Edit')]"
            ]

            for selector in edit_selectors:
                try:
                    edit_btn = self.driver.find_element(By.XPATH, selector)
                    self.driver.execute_script("arguments[0].click();", edit_btn)
                    edit_found = True
                    time.sleep(3)
                    break
                except:
                    continue

            if edit_found:
                # Save directly (simplified)
                save_selectors = [
                    "//span[contains(text(), 'Save')]",
                    "//button[contains(text(), 'Save')]"
                ]

                for selector in save_selectors:
                    try:
                        save_btn = self.driver.find_element(By.XPATH, selector)
                        self.driver.execute_script("arguments[0].click();", save_btn)
                        time.sleep(5)
                        return True
                    except:
                        continue

            return False

        except Exception as e:
            logging.error(f"Make public error: {e}")
            return False

    def get_stats(self):
        """Statistics get karta hai"""
        try:
            conn = sqlite3.connect('facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM listings")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_public = 1")
            public = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE is_visible = 1")
            visible = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'pending'")
            pending = cursor.fetchone()[0]

            conn.close()

            stats = {
                'total_listings': total,
                'public_listings': public,
                'visible_listings': visible,
                'pending_listings': pending,
                'success_rate': (public / total * 100) if total > 0 else 0
            }

            # PHP ko stats bhejo
            self.send_to_php({
                'action': 'update_stats',
                'data': stats
            })

            return stats

        except Exception as e:
            logging.error(f"Stats error: {e}")
            return {}

    def run_bot(self, email, password):
        """Main bot function"""
        self.log_to_php("bot", "started", "Bot started running")

        if not self.initialize_driver():
            return

        try:
            # Login
            if not self.login(email, password):
                return

            # Process listings
            success_count, total_count = self.process_listings()

            # Get final stats
            stats = self.get_stats()

            # PHP ko final report bhejo
            self.log_to_php("bot", "completed",
                          f"Bot completed. Success: {success_count}/{total_count}")

        except Exception as e:
            self.log_to_php("bot", "error", f"Bot error: {e}")
        finally:
            self.close()

    def close(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()
        self.log_to_php("bot", "stopped", "Bot stopped")

# PHP Server ke liye API functions
def start_bot_from_php():
    """PHP se call karne ke liye function"""
    bot = FacebookBotWithPHP()

    # Database se settings lo
    conn = sqlite3.connect('facebook_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT email, password FROM settings ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()

    if result:
        email, password = result
        bot.run_bot(email, password)
        return True
    return False

if __name__ == "__main__":
    # Direct run karne ke liye
    EMAIL = "xofedi9676@rabitex.com"
    PASSWORD = "ASD@123"

    bot = FacebookBotWithPHP()
    bot.run_bot(EMAIL, PASSWORD)
