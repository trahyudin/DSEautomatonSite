import time
import random
import math
import numpy as np

try:
    import cv2
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

class HumanMouse:
    """Generates natural Bezier curve mouse movements to evade bot detection."""
    
    @staticmethod
    def bezier_curve(p0, p1, p2, p3, steps=25):
        """Generates 3rd order Bezier curve control points."""
        points = []
        for i in range(steps + 1):
            t = i / steps
            # Cubic bezier formula
            x = (1-t)**3 * p0[0] + 3*(1-t)**2 * t * p1[0] + 3*(1-t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2 * t * p1[1] + 3*(1-t) * t**2 * p2[1] + t**3 * p3[1]
            
            # Add subtle micro-jitter (human tremor)
            jitter_x = random.uniform(-1.5, 1.5)
            jitter_y = random.uniform(-1.5, 1.5)
            points.append((int(x + jitter_x), int(y + jitter_y)))
        return points

    @classmethod
    def move_to(cls, start_pos, target_pos, steps=30):
        """Calculates control points and returns trajectory path."""
        x1, y1 = start_pos
        x2, y2 = target_pos
        
        # Calculate random control points for natural curve arc
        ctrl_x1 = x1 + (x2 - x1) * random.uniform(0.2, 0.4) + random.randint(-50, 50)
        ctrl_y1 = y1 + (y2 - y1) * random.uniform(0.1, 0.3) + random.randint(-50, 50)
        
        ctrl_x2 = x1 + (x2 - x1) * random.uniform(0.6, 0.8) + random.randint(-50, 50)
        ctrl_y2 = y1 + (y2 - y1) * random.uniform(0.7, 0.9) + random.randint(-50, 50)
        
        return cls.bezier_curve((x1, y1), (ctrl_x1, ctrl_y1), (ctrl_x2, ctrl_y2), (x2, y2), steps=steps)

class HumanKeyboard:
    """Simulates realistic human typing rhythms, delays, and punctuation pauses."""
    
    @staticmethod
    def type_text(page_or_element, text, min_delay=0.04, max_delay=0.14):
        """
        Types text into a Playwright page or element with randomized delays.
        """
        for char in text:
            # Playwright element typing or string injection
            if hasattr(page_or_element, 'type'):
                delay_ms = int(random.uniform(min_delay, max_delay) * 1000)
                page_or_element.type(char, delay=delay_ms)
            elif hasattr(page_or_element, 'press'):
                page_or_element.press(char)
                time.sleep(random.uniform(min_delay, max_delay))
            else:
                time.sleep(random.uniform(min_delay, max_delay))
                
            # Extra pause on punctuation/space
            if char in ['.', ',', '!', '?', '\n']:
                time.sleep(random.uniform(0.2, 0.5))

class VisionEngine:
    """Computer Vision Helper using OpenCV for screen matching."""
    
    @staticmethod
    def find_template(screenshot_path, template_path, threshold=0.8):
        """
        Locates a sub-image template within a full screen capture.
        Returns (found: bool, center_x, center_y, confidence)
        """
        if not CV2_AVAILABLE:
            return False, 0, 0, 0.0
            
        try:
            img = cv2.imread(screenshot_path, cv2.IMREAD_COLOR)
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            
            if img is None or template is None:
                return False, 0, 0, 0.0
                
            h, w, _ = template.shape
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= threshold:
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return True, center_x, center_y, max_val
            return False, 0, 0, max_val
        except Exception:
            return False, 0, 0, 0.0
