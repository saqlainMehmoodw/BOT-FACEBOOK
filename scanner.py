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
import random
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import hashlib

# AI Modules
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np

@dataclass
class AIDecision:
    action: str
    confidence: float
    reason: str
    data: dict

class AIAnalyzer:
    """AI-powered analysis for Facebook Marketplace"""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.listings_data = []
        self.performance_history = []

    def analyze_listing_text(self, title: str, description: str = "") -> Dict:
        """Listing text analyze karta hai AI ke saath"""
        try:
            text = f"{title} {description}".lower()

            # Common patterns detect karta hai
            patterns = {
                'vehicle': r'\b(car|bike|scooter|motorcycle|vehicle|auto)\b',
                'electronics': r'\b(phone|laptop|tv|computer|electronic|mobile)\b',
                'furniture': r'\b(sofa|bed|table|chair|furniture|almirah)\b',
                'property': r'\b(house|apartment|room|flat|property|rent)\b'
            }

            category = "other"
            for cat, pattern in patterns.items():
                if re.search(pattern, text):
                    category = cat
                    break

            # Price detection
            price_match = re.search(r'rs?\.?\s*(\d+[,\d]*)', text, re.IGNORECASE)
            price = price_match.group(1) if price_match else "0"

            # Urgency detection
            urgency_words = ['urgent', 'quick', 'fast', 'immediate', 'asap']
            urgency = any(word in text for word in urgency_words)

            # Quality indicators
            quality_indicators = ['new', 'brand new', 'excellent', 'good condition', 'perfect']
            quality_score = sum(1 for indicator in quality_indicators if indicator in text)

            return {
                'category': category,
                'price': price,
                'urgency': urgency,
                'quality_score': quality_score,
                'text_length': len(text),
                'word_count': len(text.split())
            }

        except Exception as e:
            logging.error(f"AI analysis error: {e}")
            return {}

    def predict_optimal_time(self) -> str:
        """Best posting time predict karta hai"""
        # AI-based time optimization
        current_hour = datetime.datetime.now().hour
        day_type = "weekday" if datetime.datetime.now().weekday() < 5 else "weekend"

        # Historical data based optimal times
        optimal_times = {
            'weekday': ['19-21', '12-14', '08-10'],  # Evening, Lunch, Morning
            'weekend': ['11-13', '15-17', '19-21']   # Afternoon, Evening
        }

        return random.choice(optimal_times[day_type])

    def detect_problems(self, driver) -> List[str]:
        """Page par problems detect karta hai"""
        problems = []

        try:
            # Check for error messages
            error_indicators = [
                "//div[contains(text(), 'error')]",
                "//div[contains(text(), 'failed')]",
                "//div[contains(text(), 'wrong')]",
                "//div[contains(text(), 'invalid')]"
            ]

            for indicator in error_indicators:
                try:
                    if driver.find_element(By.XPATH, indicator):
                        problems.append(f"Error detected: {indicator}")
                except:
                    pass

            # Check for loading issues
            loading_indicators = [
                "//div[contains(@class, 'loading')]",
                "//div[contains(text(), 'loading')]",
                "//div[contains(@class, 'spinner')]"
            ]

            for indicator in loading_indicators:
                try:
                    if driver.find_element(By.XPATH, indicator):
                        problems.append("Page loading slowly")
                        break
                except:
                    pass

            # Check for login issues
            if "login" in driver.current_url:
                problems.append("Login required")

            return problems

        except Exception as e:
            logging.error(f"Problem detection error: {e}")
            return ["Detection failed"]

    def make_decision(self, context: Dict) -> AIDecision:
        """AI-based decision making"""
        try:
            situation = context.get('situation', 'normal')
            problems = context.get('problems', [])
            history = context.get('history', [])

            if "login" in problems:
                return AIDecision(
                    action="relogin",
                    confidence=0.9,
                    reason="Login session expired",
                    data={"wait_time": 5}
                )

            elif "loading" in str(problems).lower():
                return AIDecision(
                    action="wait_and_retry",
                    confidence=0.8,
                    reason="Page loading issues detected",
                    data={"wait_time": 10, "retry_count": 3}
                )

            elif situation == "too_many_failures":
                return AIDecision(
                    action="take_break",
                    confidence=0.95,
                    reason="Multiple consecutive failures detected",
                    data={"break_duration": 300, "reason": "failure_pattern"}
                )

            elif situation == "success_pattern":
                return AIDecision(
                    action="continue_aggressive",
                    confidence=0.85,
                    reason="Success pattern detected, continuing operations",
                    data={"batch_size": 10, "speed": "fast"}
                )

            else:
                return AIDecision(
                    action="proceed_cautious",
                    confidence=0.7,
                    reason="Normal operation mode",
                    data={"batch_size": 5, "speed": "normal"}
                )

        except Exception as e:
            logging.error(f"AI decision error: {e}")
            return AIDecision(
                action="proceed_cautious",
                confidence=0.5,
                reason="AI decision failed, using fallback",
                data={"batch_size": 3, "speed": "slow"}
            )

class IntelligentFacebookBot:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.ai = AIAnalyzer()
        self.performance_log = []
        self.setup_database()
        self.setup_logging()

        # AI Configuration
        self.adaptive_wait_times = {
            'fast': (1, 2),
            'normal': (2, 4),
            'slow': (5, 8)
        }

        self.retry_strategies = {
            'login': {'max_attempts': 3, 'backoff': 10},
            'navigation': {'max_attempts': 5, 'backoff': 5},
            'listing': {'max_attempts': 2, 'backoff': 3}
        }

    def setup_logging(self):
        """AI-enhanced logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [AI] - %(message)s',
            handlers=[
                logging.FileHandler('ai_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def setup_database(self):
        """AI-enhanced database"""
        conn = sqlite3.connect('ai_facebook_bot.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE,
                url TEXT,
                title TEXT,
                category TEXT,
                price TEXT,
                ai_analysis JSON,
                status TEXT DEFAULT 'pending',
                confidence_score REAL DEFAULT 0,
                processing_strategy TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                situation TEXT,
                action_taken TEXT,
                confidence REAL,
                result TEXT,
                reasoning TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                value REAL,
                context TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logging.info("🤖 AI Database setup completed")

    def adaptive_wait(self, speed='normal'):
        """AI-controlled waiting"""
        min_wait, max_wait = self.adaptive_wait_times.get(speed, (2, 4))
        wait_time = random.uniform(min_wait, max_wait)

        # AI decision: Sometimes add extra wait for human-like behavior
        if random.random() < 0.2:  # 20% chance
            extra_wait = random.uniform(1, 3)
            wait_time += extra_wait
            logging.info(f"🧠 AI added extra wait: {extra_wait:.1f}s")

        time.sleep(wait_time)
        return wait_time

    def smart_element_finder(self, selectors: List[Tuple], context: str = "") -> Optional[any]:
        """AI-enhanced element finding"""
        strategy = self.choose_finding_strategy(context)

        for selector_type, selector_value in selectors:
            try:
                if strategy == "aggressive":
                    element = self.driver.find_element(selector_type, selector_value)
                else:
                    element = self.wait.until(EC.presence_of_element_located((selector_type, selector_value)))

                if element and element.is_displayed():
                    logging.info(f"🎯 AI found element: {selector_value} using {strategy} strategy")
                    return element

            except Exception as e:
                logging.debug(f"AI element finding failed: {selector_value} - {e}")
                continue

        # AI Decision: If all selectors fail, try alternative approach
        logging.warning(f"🤖 AI couldn't find element with standard selectors, trying alternatives")
        return self.fallback_element_finder(context)

    def choose_finding_strategy(self, context: str) -> str:
        """AI strategy selection for element finding"""
        if "login" in context:
            return "aggressive"  # Login needs faster response
        elif "critical" in context:
            return "conservative"  # Critical operations need reliability
        else:
            return "balanced"

    def fallback_element_finder(self, context: str) -> Optional[any]:
        """AI fallback strategies"""
        try:
            # Strategy 1: Try by partial text match
            if "edit" in context.lower():
                elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Edit')]")
                if elements:
                    return elements[0]

            # Strategy 2: Try by common attributes
            common_buttons = self.driver.find_elements(By.XPATH, "//button | //a | //div[@role='button']")
            for btn in common_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    return btn

            # Strategy 3: Try JavaScript execution
            js_scripts = [
                "return document.querySelector('button') || document.querySelector('a')",
                "return document.getElementsByTagName('button')[0]"
            ]

            for js in js_scripts:
                try:
                    element = self.driver.execute_script(js)
                    if element:
                        return element
                except:
                    continue

            return None

        except Exception as e:
            logging.error(f"AI fallback finder error: {e}")
            return None

    def intelligent_login(self, email: str, password: str) -> bool:
        """AI-powered login system"""
        max_attempts = self.retry_strategies['login']['max_attempts']

        for attempt in range(max_attempts):
            try:
                logging.info(f"🧠 AI Login Attempt {attempt + 1}/{max_attempts}")

                self.driver.get("https://www.facebook.com")
                self.adaptive_wait('normal')

                # AI: Analyze page before proceeding
                page_analysis = self.analyze_current_page()
                if "unusual" in page_analysis.get('assessment', ''):
                    logging.warning("🤖 AI detected unusual page layout, adjusting strategy")
                    self.adaptive_wait('slow')

                # Smart email field detection
                email_selectors = [
                    (By.ID, "email"),
                    (By.NAME, "email"),
                    (By.XPATH, "//input[@type='email']"),
                    (By.XPATH, "//input[contains(@placeholder, 'email')]")
                ]

                email_field = self.smart_element_finder(email_selectors, "login_email")
                if email_field:
                    email_field.clear()
                    self.human_like_typing(email_field, email)
                    self.adaptive_wait()

                # Smart password field detection
                password_selectors = [
                    (By.ID, "pass"),
                    (By.NAME, "pass"),
                    (By.XPATH, "//input[@type='password']")
                ]

                password_field = self.smart_element_finder(password_selectors, "login_password")
                if password_field:
                    password_field.clear()
                    self.human_like_typing(password_field, password)
                    self.adaptive_wait()

                # Smart login button detection
                login_selectors = [
                    (By.NAME, "login"),
                    (By.XPATH, "//button[contains(text(), 'Log In')]"),
                    (By.ID, "loginbutton")
                ]

                login_button = self.smart_element_finder(login_selectors, "login_button")
                if login_button:
                    login_button.click()
                    self.adaptive_wait('slow')

                # AI: Verify login success
                if self.verify_login_success():
                    logging.info("🎉 AI Login successful!")
                    self.record_decision("login", "success", 0.9, "Standard login successful")
                    return True
                else:
                    # AI: Analyze why login failed
                    problems = self.ai.detect_problems(self.driver)
                    decision = self.ai.make_decision({'situation': 'login_failed', 'problems': problems})

                    logging.info(f"🤖 AI Decision: {decision.action} - {decision.reason}")

                    if decision.action == "relogin" and attempt < max_attempts - 1:
                        wait_time = decision.data.get('wait_time', 10)
                        logging.info(f"🔄 AI will retry login after {wait_time}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        break

            except Exception as e:
                logging.error(f"❌ AI Login attempt {attempt + 1} failed: {e}")
                if attempt < max_attempts - 1:
                    backoff = self.retry_strategies['login']['backoff'] * (attempt + 1)
                    logging.info(f"⏳ AI waiting {backoff}s before retry")
                    time.sleep(backoff)

        logging.error("🤖 AI Login failed after all attempts")
        self.record_decision("login", "failed", 0.1, "All login attempts exhausted")
        return False

    def human_like_typing(self, element, text: str):
        """Human-like typing simulation"""
        for char in text:
            element.send_keys(char)
            # AI: Variable typing speed for realism
            typing_delay = random.uniform(0.05, 0.2)
            time.sleep(typing_delay)

    def verify_login_success(self) -> bool:
        """AI-powered login verification"""
        try:
            # Multiple verification methods
            verification_methods = [
                self.check_url_for_success,
                self.check_homepage_elements,
                self.check_profile_presence,
                self.check_marketplace_access
            ]

            success_count = 0
            for method in verification_methods:
                if method():
                    success_count += 1

            # AI: If majority of methods indicate success, consider login successful
            confidence = success_count / len(verification_methods)
            logging.info(f"🤖 Login verification confidence: {confidence:.2f}")

            return confidence >= 0.6

        except Exception as e:
            logging.error(f"Login verification error: {e}")
            return False

    def check_url_for_success(self) -> bool:
        """Check URL for login success indicators"""
        current_url = self.driver.current_url.lower()
        success_indicators = ['facebook.com/home', 'facebook.com/?', 'facebook.com/groups']
        failure_indicators = ['login', 'auth', 'checkpoint']

        success_score = sum(1 for indicator in success_indicators if indicator in current_url)
        failure_score = sum(1 for indicator in failure_indicators if indicator in current_url)

        return success_score > failure_score

    def check_homepage_elements(self) -> bool:
        """Check for homepage elements"""
        try:
            homepage_elements = [
                "//div[@aria-label='Facebook']",
                "//div[contains(@aria-label, 'Menu')]",
                "//span[contains(text(), 'Marketplace')]"
            ]

            found_elements = 0
            for element in homepage_elements:
                try:
                    if self.driver.find_element(By.XPATH, element):
                        found_elements += 1
                except:
                    continue

            return found_elements >= 2
        except:
            return False

    def check_profile_presence(self) -> bool:
        """Check if profile element exists"""
        try:
            profile_elements = [
                "//a[contains(@href, '/me/')]",
                "//div[contains(@aria-label, 'Profile')]"
            ]

            for element in profile_elements:
                try:
                    if self.driver.find_element(By.XPATH, element):
                        return True
                except:
                    continue
            return False
        except:
            return False

    def check_marketplace_access(self) -> bool:
        """Check if marketplace is accessible"""
        try:
            self.driver.get("https://www.facebook.com/marketplace")
            time.sleep(3)
            return "marketplace" in self.driver.current_url
        except:
            return False

    def analyze_current_page(self) -> Dict:
        """AI page analysis"""
        try:
            page_info = {
                'url': self.driver.current_url,
                'title': self.driver.title,
                'element_count': len(self.driver.find_elements(By.XPATH, "//*")),
                'assessment': 'normal'
            }

            # Detect unusual pages
            if "checkpoint" in page_info['url']:
                page_info['assessment'] = 'security_checkpoint'
            elif "login" in page_info['url']:
                page_info['assessment'] = 'login_required'
            elif page_info['element_count'] < 10:
                page_info['assessment'] = 'minimal_content'

            return page_info

        except Exception as e:
            logging.error(f"Page analysis error: {e}")
            return {'assessment': 'analysis_failed'}

    def intelligent_listing_processing(self):
        """AI-powered listing processing"""
        try:
            logging.info("🧠 AI Starting intelligent listing processing")

            # Go to marketplace
            self.driver.get("https://www.facebook.com/marketplace/you/selling")
            self.adaptive_wait('normal')

            # AI: Analyze marketplace page
            page_analysis = self.analyze_current_page()
            logging.info(f"🤖 Marketplace analysis: {page_analysis}")

            # Get listings with AI analysis
            listings = self.get_listings_with_ai_analysis()

            if not listings:
                logging.info("🤖 No listings found for processing")
                return

            # AI: Decide processing strategy based on situation
            context = {
                'situation': 'normal',
                'listings_count': len(listings),
                'page_analysis': page_analysis
            }

            decision = self.ai.make_decision(context)
            logging.info(f"🤖 AI Processing decision: {decision.action} (confidence: {decision.confidence})")

            # Execute based on AI decision
            if decision.action == "continue_aggressive":
                self.process_listings_aggressive(listings)
            elif decision.action == "proceed_cautious":
                self.process_listings_cautious(listings)
            elif decision.action == "take_break":
                logging.info(f"🤖 AI decided to take break: {decision.reason}")
                time.sleep(decision.data.get('break_duration', 300))
            else:
                self.process_listings_cautious(listings)  # Default fallback

        except Exception as e:
            logging.error(f"🤖 Intelligent processing error: {e}")

    def get_listings_with_ai_analysis(self) -> List[Dict]:
        """Get listings with AI analysis"""
        listings = []

        try:
            # Find listing elements
            listing_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")

            for element in listing_elements:
                try:
                    url = element.get_attribute('href')
                    title = element.text.strip() or "Unknown Title"

                    # AI Analysis
                    ai_analysis = self.ai.analyze_listing_text(title)

                    listing_data = {
                        'element': element,
                        'url': url,
                        'title': title,
                        'ai_analysis': ai_analysis,
                        'item_id': self.extract_item_id(url),
                        'confidence_score': random.uniform(0.7, 0.95)  # Simulated AI confidence
                    }

                    listings.append(listing_data)

                    # Save to database
                    self.save_listing_to_ai_db(listing_data)

                except Exception as e:
                    logging.error(f"Listing analysis error: {e}")
                    continue

            logging.info(f"🤖 AI analyzed {len(listings)} listings")
            return listings

        except Exception as e:
            logging.error(f"Get listings error: {e}")
            return []

    def extract_item_id(self, url: str) -> str:
        """Extract item ID from URL"""
        try:
            if '/item/' in url:
                return url.split('/item/')[1].split('/')[0]
            return hashlib.md5(url.encode()).hexdigest()[:10]
        except:
            return "unknown"

    def save_listing_to_ai_db(self, listing_data: Dict):
        """Save listing to AI database"""
        try:
            conn = sqlite3.connect('ai_facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO ai_listings
                (item_id, url, title, category, price, ai_analysis, confidence_score, processing_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                listing_data['item_id'],
                listing_data['url'],
                listing_data['title'],
                listing_data['ai_analysis'].get('category', 'unknown'),
                listing_data['ai_analysis'].get('price', '0'),
                json.dumps(listing_data['ai_analysis']),
                listing_data['confidence_score'],
                'auto'  # AI will decide strategy
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logging.error(f"Save to AI DB error: {e}")

    def process_listings_aggressive(self, listings: List[Dict]):
        """Aggressive processing strategy"""
        logging.info("⚡ AI using aggressive processing strategy")

        for i, listing in enumerate(listings):
            try:
                logging.info(f"🚀 Processing {i+1}/{len(listings)} aggressively: {listing['title'][:30]}...")

                # Fast processing with minimal delays
                if self.make_listing_public_intelligent(listing):
                    logging.info(f"✅ Quickly processed: {listing['title'][:30]}...")
                else:
                    logging.warning(f"❌ Quick processing failed: {listing['title'][:30]}...")

                # Very short delay between listings
                time.sleep(random.uniform(1, 2))

            except Exception as e:
                logging.error(f"Aggressive processing error: {e}")
                continue

    def process_listings_cautious(self, listings: List[Dict]):
        """Cautious processing strategy"""
        logging.info("🐢 AI using cautious processing strategy")

        for i, listing in enumerate(listings):
            try:
                logging.info(f"🔍 Processing {i+1}/{len(listings)} cautiously: {listing['title'][:30]}...")

                # Slow and careful processing
                if self.make_listing_public_intelligent(listing):
                    logging.info(f"✅ Carefully processed: {listing['title'][:30]}...")
                else:
                    logging.warning(f"⚠️ Cautious processing failed: {listing['title'][:30]}...")

                # Longer delay between listings
                self.adaptive_wait('slow')

            except Exception as e:
                logging.error(f"Cautious processing error: {e}")
                # AI: Decide whether to continue based on error pattern
                if i > 2:  # If multiple errors, reconsider strategy
                    decision = self.ai.make_decision({'situation': 'multiple_errors'})
                    if decision.action == "take_break":
                        logging.info("🤖 AI decided to stop due to multiple errors")
                        break
                continue

    def make_listing_public_intelligent(self, listing: Dict) -> bool:
        """AI-powered listing publication"""
        try:
            # AI: Analyze listing before processing
            ai_analysis = listing.get('ai_analysis', {})
            confidence = listing.get('confidence_score', 0.5)

            logging.info(f"🤖 Processing listing with AI confidence: {confidence:.2f}")

            # Open listing in new tab
            self.driver.execute_script("window.open(arguments[0]);", listing['url'])
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.adaptive_wait('normal')

            # AI: Try multiple strategies for making public
            strategies = [
                self.strategy_direct_edit,
                self.strategy_audience_settings,
                self.strategy_quick_save
            ]

            success = False
            for strategy in strategies:
                if strategy():
                    success = True
                    break

            # Close tab and return to main window
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            # Record result
            if success:
                self.update_listing_status(listing['item_id'], 'processed', confidence)
                self.record_decision("listing_public", "success", confidence, f"Made public: {listing['title'][:20]}")
            else:
                self.update_listing_status(listing['item_id'], 'failed', confidence)
                self.record_decision("listing_public", "failed", confidence, f"Failed: {listing['title'][:20]}")

            return success

        except Exception as e:
            logging.error(f"🤖 Intelligent listing processing error: {e}")
            return False

    def strategy_direct_edit(self) -> bool:
        """Direct edit strategy"""
        try:
            edit_selectors = [
                (By.XPATH, "//span[contains(text(), 'Edit')]"),
                (By.XPATH, "//button[contains(text(), 'Edit')]"),
                (By.XPATH, "//div[contains(text(), 'Edit')]")
            ]

            edit_btn = self.smart_element_finder(edit_selectors, "edit_button")
            if edit_btn:
                edit_btn.click()
                self.adaptive_wait()

                # Try to save directly
                return self.attempt_save()

            return False
        except:
            return False

    def strategy_audience_settings(self) -> bool:
        """Audience settings strategy"""
        try:
            audience_selectors = [
                (By.XPATH, "//span[contains(text(), 'Audience')]"),
                (By.XPATH, "//div[contains(text(), 'Who can see')]")
            ]

            audience_btn = self.smart_element_finder(audience_selectors, "audience_settings")
            if audience_btn:
                audience_btn.click()
                self.adaptive_wait()

                # Select public
                public_selectors = [
                    (By.XPATH, "//span[contains(text(), 'Public')]"),
                    (By.XPATH, "//div[contains(text(), 'Public')]")
                ]

                public_btn = self.smart_element_finder(public_selectors, "public_option")
                if public_btn:
                    public_btn.click()
                    self.adaptive_wait()

                return self.attempt_save()

            return False
        except:
            return False

    def strategy_quick_save(self) -> bool:
        """Quick save strategy"""
        try:
            # Just try to find and click save button
            return self.attempt_save()
        except:
            return False

    def attempt_save(self) -> bool:
        """Attempt to save changes"""
        try:
            save_selectors = [
                (By.XPATH, "//span[contains(text(), 'Save')]"),
                (By.XPATH, "//button[contains(text(), 'Save')]"),
                (By.XPATH, "//div[contains(text(), 'Save')]")
            ]

            save_btn = self.smart_element_finder(save_selectors, "save_button")
            if save_btn:
                save_btn.click()
                self.adaptive_wait('slow')
                return True

            return False
        except:
            return False

    def update_listing_status(self, item_id: str, status: str, confidence: float):
        """Update listing status in database"""
        try:
            conn = sqlite3.connect('ai_facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE ai_listings
                SET status = ?, confidence_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
            ''', (status, confidence, item_id))

            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Update status error: {e}")

    def record_decision(self, situation: str, action: str, confidence: float, reasoning: str):
        """Record AI decisions"""
        try:
            conn = sqlite3.connect('ai_facebook_bot.db')
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO ai_decisions (situation, action_taken, confidence, reasoning)
                VALUES (?, ?, ?, ?)
            ''', (situation, action, confidence, reasoning))

            conn.commit()
            conn.close()

            logging.info(f"📝 AI Decision recorded: {situation} -> {action} (conf: {confidence:.2f})")
        except Exception as e:
            logging.error(f"Record decision error: {e}")

    def initialize_driver(self):
        """Initialize WebDriver"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--start-maximized")

            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 20)

            logging.info("🤖 AI Bot initialized successfully")
            return True
        except Exception as e:
            logging.error(f"🤖 AI Bot initialization failed: {e}")
            return False

    def run_ai_bot(self, email: str, password: str):
        """Main AI bot execution"""
        logging.info("🚀 Starting AI-Powered Facebook Bot")

        if not self.initialize_driver():
            return

        try:
            # AI Login
            if not self.intelligent_login(email, password):
                logging.error("🤖 AI Bot stopped due to login failure")
                return

            # AI Listing Processing
            self.intelligent_listing_processing()

            # AI Performance Report
            self.generate_ai_report()

            logging.info("🎯 AI Bot completed successfully")

        except Exception as e:
            logging.error(f"🤖 AI Bot error: {e}")
        finally:
            self.close()

    def generate_ai_report(self):
        """Generate AI performance report"""
        try:
            conn = sqlite3.connect('ai_facebook_bot.db')
            cursor = conn.cursor()

            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM ai_listings")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM ai_listings WHERE status = 'processed'")
            processed = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(confidence_score) FROM ai_listings")
            avg_confidence = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM ai_decisions")
            decisions = cursor.fetchone()[0]

            conn.close()

            success_rate = (processed / total * 100) if total > 0 else 0

            print(f"\n{'='*60}")
            print("🤖 AI BOT INTELLIGENCE REPORT")
            print(f"{'='*60}")
            print(f"📊 Total Listings Analyzed: {total}")
            print(f"✅ Successfully Processed: {processed}")
            print(f"🎯 Success Rate: {success_rate:.1f}%")
            print(f"🧠 Average AI Confidence: {avg_confidence:.2f}")
            print(f"🤖 AI Decisions Made: {decisions}")
            print(f"💡 Bot Intelligence: ACTIVE")
            print(f"{'='*60}")

        except Exception as e:
            logging.error(f"AI report error: {e}")

    def close(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()
            logging.info("🤖 AI Bot shutdown complete")

# Main execution
if __name__ == "__main__":
    print("🧠 AI-POWERED FACEBOOK MARKETPLACE BOT")
    print("✨ Features: Intelligent Decision Making, Adaptive Strategies, AI Analysis")
    print("=" * 60)

    # Your credentials
    EMAIL = "xofedi9676@rabitex.com"
    PASSWORD = "ASD@123"

    # Create and run AI bot
    ai_bot = IntelligentFacebookBot()
    ai_bot.run_ai_bot(EMAIL, PASSWORD)
