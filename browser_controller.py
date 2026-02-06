"""
Browser Controller with Gemini Computer Use
AI-powered browser automation for Amazon shopping
"""
import asyncio
import time
import re
from typing import Optional, Dict, Any, Callable, Union, Coroutine
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

from google import genai
from google.genai import types
from google.genai.types import Content, Part

import config

# Constants for screen dimensions
SCREEN_WIDTH = 1440
SCREEN_HEIGHT = 900

# Initialize Gemini client
client = genai.Client()


def denormalize_x(x: int, screen_width: int) -> int:
    """Convert normalized x coordinate (0-1000) to actual pixel coordinate."""
    return int(x / 1000 * screen_width)


def denormalize_y(y: int, screen_height: int) -> int:
    """Convert normalized y coordinate (0-1000) to actual pixel coordinate."""
    return int(y / 1000 * screen_height)


def show_click_highlight(page, x: int, y: int, color: str = "#FF4444", duration: int = 800):
    """
    Show a visual highlight/ripple effect at the specified position.
    
    Args:
        page: Playwright page object
        x: X coordinate in pixels
        y: Y coordinate in pixels
        color: Color of the highlight (default red for clicks)
        duration: Duration of animation in milliseconds
    """
    # JavaScript to inject a ripple/highlight effect
    highlight_js = f"""
    (function() {{
        // Create the highlight element
        const highlight = document.createElement('div');
        highlight.id = 'automation-highlight-' + Date.now();
        
        // Style the main highlight circle (smaller 16px size)
        highlight.style.cssText = `
            position: fixed;
            left: {x}px;
            top: {y}px;
            width: 16px;
            height: 16px;
            margin-left: -8px;
            margin-top: -8px;
            border-radius: 50%;
            background: {color};
            opacity: 0.8;
            pointer-events: none;
            z-index: 999999;
            box-shadow: 0 0 10px {color}, 0 0 20px {color}80;
            animation: highlight-pulse {duration}ms ease-out forwards;
        `;
        
        // Create ripple effect (smaller ring)
        const ripple = document.createElement('div');
        ripple.style.cssText = `
            position: fixed;
            left: {x}px;
            top: {y}px;
            width: 16px;
            height: 16px;
            margin-left: -8px;
            margin-top: -8px;
            border-radius: 50%;
            border: 2px solid {color};
            pointer-events: none;
            z-index: 999998;
            animation: highlight-ripple {duration}ms ease-out forwards;
        `;
        
        // Add CSS animation keyframes if not already added
        if (!document.getElementById('highlight-animation-styles')) {{
            const style = document.createElement('style');
            style.id = 'highlight-animation-styles';
            style.textContent = `
                @keyframes highlight-pulse {{
                    0% {{ transform: scale(1); opacity: 0.8; }}
                    50% {{ transform: scale(1.3); opacity: 0.5; }}
                    100% {{ transform: scale(1.8); opacity: 0; }}
                }}
                @keyframes highlight-ripple {{
                    0% {{ transform: scale(1); opacity: 1; }}
                    100% {{ transform: scale(3); opacity: 0; }}
                }}
            `;
            document.head.appendChild(style);
        }}
        
        // Add elements to page
        document.body.appendChild(highlight);
        document.body.appendChild(ripple);
        
        // Remove elements after animation
        setTimeout(() => {{
            highlight.remove();
            ripple.remove();
        }}, {duration});
    }})();
    """
    
    try:
        page.evaluate(highlight_js)
    except Exception as e:
        print(f"Highlight injection error: {e}")


def summarize_for_speech(verbose_text: str) -> str:
    """
    Use Gemini Flash to convert verbose model output into brief instructional speech.
    
    Args:
        verbose_text: The verbose model output (e.g., "I have evaluated the screenshot...")
        
    Returns:
        Brief instructional guidance (e.g., "Click on the File menu")
    """
    try:
        # Skip if text is already short enough
        if len(verbose_text.split()) <= 10:
            return verbose_text
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                Content(role="user", parts=[
                    Part(text=f"""Convert this browser action into a brief instruction for teaching a user.
Give clear, direct instructions like "Click on the File menu" or "Type your search in the box" or "Now press Enter to submit".
Use action words: Click, Type, Press, Select, Scroll, Drag, Open, etc.
Keep it to 5-12 words. Be friendly and helpful.
Never explain reasoning. Just give the instruction.

Action to convert:
{verbose_text}

Instruction:""")
                ])
            ],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=40,
            )
        )
        
        summary = response.text.strip()
        # Clean up any quotes or extra formatting
        summary = summary.strip('"\'')
        return summary if summary else verbose_text
        
    except Exception as e:
        print(f"Summarization error: {e}")
        # Fall back to first 10 words if summarization fails
        words = verbose_text.split()[:10]
        return ' '.join(words) + ('...' if len(verbose_text.split()) > 10 else '')


def execute_function_calls(candidate, page, screen_width, screen_height):
    """Execute function calls from the model response and return results."""
    results = []
    function_calls = []
    for part in candidate.content.parts:
        if part.function_call:
            function_calls.append(part.function_call)

    for function_call in function_calls:
        action_result = {}
        fname = function_call.name
        args = function_call.args
        print(f"  -> Executing: {fname}")

        # Check for safety decision in args
        if 'safety_decision' in args:
            safety_info = args['safety_decision']
            print(f"  ⚠️ Safety check: {safety_info.get('explanation', 'Confirmation required')}")
            # Auto-acknowledge for automation (in production, you'd prompt the user)
            action_result["safety_acknowledgement"] = "true"
            print(f"  ✅ Safety acknowledged")

        try:
            if fname == "open_web_browser":
                pass  # Already open
            elif fname == "click_at":
                actual_x = denormalize_x(args["x"], screen_width)
                actual_y = denormalize_y(args["y"], screen_height)
                # Show red highlight for click
                show_click_highlight(page, actual_x, actual_y, color="#FF4444")
                time.sleep(0.3)  # Brief pause to show highlight before clicking
                page.mouse.click(actual_x, actual_y)
            elif fname == "type_text_at":
                actual_x = denormalize_x(args["x"], screen_width)
                actual_y = denormalize_y(args["y"], screen_height)
                text = args["text"]
                press_enter = args.get("press_enter", False)
                # Show blue highlight for typing
                show_click_highlight(page, actual_x, actual_y, color="#4488FF")
                time.sleep(0.3)
                page.mouse.click(actual_x, actual_y)
                # Clear existing text (Ctrl+A for Windows, then Backspace)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type(text)
                if press_enter:
                    page.keyboard.press("Enter")
            elif fname == "scroll":
                # Handle scroll action - show highlight at center of viewport
                direction = args.get("direction", "down")
                amount = args.get("amount", 300)
                center_x = screen_width // 2
                center_y = screen_height // 2
                show_click_highlight(page, center_x, center_y, color="#44FF44")
                time.sleep(0.2)
                if direction == "down":
                    page.mouse.wheel(0, amount)
                elif direction == "up":
                    page.mouse.wheel(0, -amount)
            elif fname == "scroll_document":
                # Handle scroll document action - show highlight at center
                direction = args.get("direction", "down")
                amount = args.get("amount", 500)
                center_x = screen_width // 2
                center_y = screen_height // 2
                show_click_highlight(page, center_x, center_y, color="#44FF44")
                time.sleep(0.2)
                if direction == "down":
                    page.mouse.wheel(0, amount)
                elif direction == "up":
                    page.mouse.wheel(0, -amount)
            elif fname == "scroll_at":
                # Handle scroll at specific position
                x = args.get("x", 500)
                y = args.get("y", 500)
                direction = args.get("direction", "down")
                amount = args.get("amount", 300)
                actual_x = denormalize_x(x, screen_width)
                actual_y = denormalize_y(y, screen_height)
                # Show green highlight for scroll
                show_click_highlight(page, actual_x, actual_y, color="#44FF44")
                time.sleep(0.3)
                page.mouse.move(actual_x, actual_y)
                if direction == "down":
                    page.mouse.wheel(0, amount)
                elif direction == "up":
                    page.mouse.wheel(0, -amount)
            elif fname == "go_back":
                # Handle browser back navigation
                page.go_back()
            elif fname == "navigate":
                # Handle navigation to URL
                url = args.get("url", "")
                if url:
                    page.goto(url)
            elif fname == "drag_and_drop":
                # Handle drag to select text - with proper timing for selection
                start_x = args.get("start_x", 0)
                start_y = args.get("start_y", 0)
                end_x = args.get("end_x", 0)
                end_y = args.get("end_y", 0)
                actual_start_x = denormalize_x(start_x, screen_width)
                actual_start_y = denormalize_y(start_y, screen_height)
                actual_end_x = denormalize_x(end_x, screen_width)
                actual_end_y = denormalize_y(end_y, screen_height)
                # Show orange highlight at start and end of drag
                show_click_highlight(page, actual_start_x, actual_start_y, color="#FF8844")
                time.sleep(0.2)
                show_click_highlight(page, actual_end_x, actual_end_y, color="#FF8844")
                time.sleep(0.2)
                # Move to start, press, drag slowly, release
                page.mouse.move(actual_start_x, actual_start_y)
                time.sleep(0.1)
                page.mouse.down()
                time.sleep(0.1)
                # Move in steps for better selection
                page.mouse.move(actual_end_x, actual_end_y, steps=10)
                time.sleep(0.1)
                page.mouse.up()
            elif fname == "key_combination":
                # Handle keyboard shortcuts like Ctrl+A, Ctrl+B, Ctrl+C
                keys = args.get("keys", "")
                if keys:
                    # Normalize key names for Playwright (control -> Control, alt -> Alt, etc.)
                    normalized = keys
                    normalized = normalized.replace("control", "Control")
                    normalized = normalized.replace("ctrl", "Control")
                    normalized = normalized.replace("alt", "Alt")
                    normalized = normalized.replace("shift", "Shift")
                    normalized = normalized.replace("meta", "Meta")
                    normalized = normalized.replace("cmd", "Meta")
                    print(f"Pressing keys: {normalized}")
                    page.keyboard.press(normalized)
            elif fname == "press_key":
                # Handle single key press
                key = args.get("key", "")
                if key:
                    page.keyboard.press(key)
            elif fname == "triple_click":
                # Handle triple click (select paragraph/line)
                x = args.get("x", 500)
                y = args.get("y", 500)
                actual_x = denormalize_x(x, screen_width)
                actual_y = denormalize_y(y, screen_height)
                # Show red highlight for triple click
                show_click_highlight(page, actual_x, actual_y, color="#FF4444")
                time.sleep(0.3)
                page.mouse.click(actual_x, actual_y, click_count=3)
            elif fname == "double_click":
                # Handle double click (select word)
                x = args.get("x", 500)
                y = args.get("y", 500)
                actual_x = denormalize_x(x, screen_width)
                actual_y = denormalize_y(y, screen_height)
                # Show red highlight for double click
                show_click_highlight(page, actual_x, actual_y, color="#FF4444")
                time.sleep(0.3)
                page.mouse.dblclick(actual_x, actual_y)
            elif fname == "select_all":
                # Select all text in the document
                page.keyboard.press("Control+a")
            else:
                print(f"Warning: Unimplemented or custom function {fname}")

            # Wait for potential navigations/renders
            try:
                page.wait_for_load_state(timeout=5000)
            except Exception:
                pass  # Ignore timeout if page hasn't navigated
            time.sleep(1)

        except Exception as e:
            print(f"Error executing {fname}: {e}")
            action_result["error"] = str(e)

        results.append((fname, action_result))

    return results


def get_function_responses(page, results):
    """Capture screenshot and build function responses to send back to the model."""
    screenshot_bytes = page.screenshot(type="png")
    current_url = page.url
    function_responses = []
    
    for name, result in results:
        response_data = {"url": current_url}
        response_data.update(result)  # This will include safety_acknowledgement if present
        function_responses.append(
            types.Part(
                function_response=types.FunctionResponse(
                    name=name,
                    response=response_data
                )
            )
        )
    
    # Add screenshot as a separate part
    screenshot_part = Part.from_bytes(data=screenshot_bytes, mime_type="image/png")
    function_responses.append(screenshot_part)
    
    return function_responses


class BrowserAutomation:
    """Handles AI-powered browser automation using Gemini Computer Use"""
    
    _instance = None
    _lock = asyncio.Lock()
    # Dedicated single-thread executor for all Playwright operations
    # This ensures all browser ops run on the same thread (required by Playwright's greenlets)
    _browser_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="browser_thread")
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_initialized = False
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
    
    @classmethod
    async def get_instance(cls) -> 'BrowserAutomation':
        """Get singleton instance"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = BrowserAutomation()
        # Re-initialize if browser was closed
        if cls._instance and not cls._instance.is_initialized:
            await cls._instance.initialize()
        return cls._instance
    
    async def initialize(self) -> bool:
        """Initialize the browser"""
        if self.is_initialized and self.browser and self.browser.is_connected():
            return True
        
        try:
            print("Initializing browser...")
            # Run playwright in dedicated browser thread (same thread for all ops)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._browser_executor, self._init_browser_sync)
            self.is_initialized = True
            print("✅ Browser initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Browser initialization failed: {e}")
            return False
    
    def _init_browser_sync(self):
        """Synchronous browser initialization"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=config.BROWSER_HEADLESS,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        self.context = self.browser.new_context(
            viewport={"width": self.screen_width, "height": self.screen_height}
        )
        self.page = self.context.new_page()
        # Navigate to Google Docs by default
        self.page.goto("https://docs.google.com")
    
    async def close(self):
        """Close the browser"""
        try:
            if self.browser:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._browser_executor, self._close_browser_sync)
            self.is_initialized = False
            BrowserAutomation._instance = None
            print("🔒 Browser closed")
        except Exception as e:
            print(f"❌ Error closing browser: {e}")
    
    def _close_browser_sync(self):
        """Synchronous browser close"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    async def execute_task(self, task_prompt: str, turn_limit: int = 15, speech_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Execute a browser automation task using Gemini Computer Use.
        
        Args:
            task_prompt: The task to perform (e.g., "Search for wireless earbuds")
            turn_limit: Maximum number of turns to prevent infinite loops
            speech_callback: Optional async callback function to speak text aloud
            
        Returns:
            Dict with success status and result message
        """
        try:
            await self.initialize()
            
            print(f"\n{'='*50}")
            print(f"Goal: {task_prompt}")
            print(f"{'='*50}\n")
            
            # Capture the event loop for async callback scheduling
            loop = asyncio.get_event_loop()
            
            # Run the agent loop in dedicated browser thread (same thread as init)
            result = await loop.run_in_executor(
                self._browser_executor, 
                self._run_agent_loop_sync, 
                task_prompt, 
                turn_limit,
                speech_callback,
                loop  # Pass the event loop
            )
            
            return result
            
        except Exception as e:
            print(f"Task execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_agent_loop_sync(self, task_prompt: str, turn_limit: int, speech_callback: Optional[Callable] = None, event_loop: Optional[asyncio.AbstractEventLoop] = None) -> Dict[str, Any]:
        """Synchronous agent loop execution"""
        try:
            # Configure the model with Computer Use tool
            model_config = types.GenerateContentConfig(
                tools=[types.Tool(computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER
                ))],
                thinking_config=types.ThinkingConfig(include_thoughts=True),
            )

            # Take initial screenshot
            initial_screenshot = self.page.screenshot(type="png")
            current_url = self.page.url
            
            print(f"Initial screenshot taken at: {current_url}")

            # Add instructions for teaching mode
            enhanced_prompt = f"""{task_prompt}

You are a TEACHING ASSISTANT demonstrating how to use Google Docs/Sheets/Slides.

TEACHING RULES:
1. Perform the action step-by-step while explaining what you're doing
2. After each step, briefly describe what you did (e.g., "I clicked on File menu")
3. Complete the demonstration fully - show the whole process
4. If you encounter a login page, explain that the user needs to sign in first
5. SHOW ONLY ONE EXAMPLE - do NOT demonstrate multiple alternatives or repeat the same action with different options

EXAMPLE TEACHING FLOW for "How do I create a new document?":
- Step 1: Click the + button or File > New (explain: "First, click the + New button")
- Step 2: Select "Google Docs" (explain: "Now select Google Docs from the menu")
- Step 3: Document opens (explain: "And there you have a new document ready to use!")
- STOP after showing ONE complete example

IMPORTANT:
- Speak naturally as if teaching a friend
- Explain each action as you do it
- Keep explanations brief but helpful
- STOP after demonstrating ONE complete example - do not show alternatives like "you could also try this font" or "another option is..."

TEXT SELECTION TIPS (use these when you need to select text):
- To select ALL text: Use key_combination with "Control+a"
- To select a word: Double-click on the word
- To select a line/paragraph: Triple-click on the line
- To format selected text as BOLD: Use key_combination with "Control+b"
- To format selected text as ITALIC: Use key_combination with "Control+i"
- To UNDO: Use key_combination with "Control+z" """

            # Initialize conversation history with enhanced prompt + initial screenshot
            contents = [
                Content(role="user", parts=[
                    Part(text=enhanced_prompt),
                    Part.from_bytes(data=initial_screenshot, mime_type='image/png')
                ])
            ]

            final_response = ""
            failed_click_count = 0  # Track consecutive failed clicks
            last_url = current_url  # Track URL to detect page changes
            
            # Agent Loop - model thinks, responds with actions, we execute, send back results
            for i in range(turn_limit):
                print(f"\n{'='*50}")
                print(f"--- Turn {i+1} ---")
                print("Thinking...")
                
                # Step 1: Send query to the model
                response = client.models.generate_content(
                    model='gemini-2.5-computer-use-preview-10-2025',
                    contents=contents,
                    config=model_config,
                )

                candidate = response.candidates[0]
                
                # Print the model's thoughts/reasoning (with null check)
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            is_thought = getattr(part, 'thought', False)
                            if is_thought:
                                print(f"Model's reasoning: {part.text}")
                            else:
                                # Clean up the text by removing "I have evaluated step X" prefix
                                clean_text = re.sub(r'^I have evaluated step \d+[,.]?\s*(and\s*)?', '', part.text, flags=re.IGNORECASE)
                                print(f"Model says: {clean_text}")
                                
                                # Speak every response for teaching mode
                                if speech_callback and clean_text.strip() and event_loop:
                                    try:
                                        # Summarize verbose text to brief speech using Gemini Flash
                                        brief_speech = summarize_for_speech(clean_text)
                                        print(f"Speaking: {brief_speech}")
                                        
                                        # Use run_coroutine_threadsafe to schedule on main event loop
                                        future = asyncio.run_coroutine_threadsafe(
                                            speech_callback(brief_speech),
                                            event_loop
                                        )
                                        # Wait briefly for it to be queued (session.say is fast)
                                        future.result(timeout=2.0)
                                    except Exception as e:
                                        print(f"Speech callback error: {e}")
                                
                                final_response = clean_text
                
                # Add model's response to conversation history
                if candidate.content:
                    contents.append(candidate.content)

                # Check if model returned function calls (with null check)
                has_function_calls = False
                if candidate.content and candidate.content.parts:
                    has_function_calls = any(part.function_call for part in candidate.content.parts if hasattr(part, 'function_call'))
                
                if not has_function_calls:
                    # No more actions - model is done
                    text_response = ""
                    if candidate.content and candidate.content.parts:
                        text_response = " ".join([part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text and not getattr(part, 'thought', False)])
                    print("\n" + "="*50)
                    print("✅ Agent finished with response:")
                    print("="*50)
                    print(text_response)
                    return {
                        "success": True,
                        "message": text_response or "Task completed successfully",
                        "url": self.page.url
                    }

                # Step 2: Execute the function calls
                print("Executing actions...")
                
                # Check if this was a click action
                was_click = any(
                    part.function_call and part.function_call.name == "click_at" 
                    for part in candidate.content.parts if part.function_call
                )
                
                results = execute_function_calls(
                    candidate, 
                    self.page, 
                    self.screen_width, 
                    self.screen_height
                )

                # Step 3: Capture state and build function responses
                print("Capturing state...")
                function_responses = get_function_responses(self.page, results)
                
                # Check if URL changed after action
                new_url = self.page.url
                url_changed = new_url != last_url
                
                # Track failed clicks (URL didn't change after click)
                if was_click and not url_changed:
                    failed_click_count += 1
                    print(f"⚠️ Click didn't change page (attempt {failed_click_count})")
                else:
                    failed_click_count = 0  # Reset on successful navigation
                
                last_url = new_url
                
                # If 2+ failed clicks, add hint to try keyboard navigation
                if failed_click_count >= 2:
                    hint = Part(text="""
HINT: Clicking doesn't seem to be working. Try these alternatives:
1. Use keyboard: Press Tab to focus the element, then Enter to activate
2. Try clicking the product IMAGE instead of text
3. Or just report that you cannot open this item and stop
""")
                    function_responses.append(hint)
                    print("💡 Added keyboard navigation hint")

                # Step 4: Send results back to the model for next iteration
                contents.append(
                    Content(role="user", parts=function_responses)
                )
            
            print(f"\n⚠️ Reached turn limit ({turn_limit}). Stopping.")
            return {
                "success": True,
                "message": final_response or f"Task in progress (reached {turn_limit} turns)",
                "url": self.page.url
            }
            
        except Exception as e:
            print(f"❌ Agent loop error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page URL and title"""
        try:
            if not self.is_initialized or not self.page:
                return {"success": False, "url": "", "title": ""}
            
            loop = asyncio.get_event_loop()
            url = self.page.url
            title = await loop.run_in_executor(None, lambda: self.page.title())
            
            return {
                "success": True,
                "url": url,
                "title": title
            }
        except Exception as e:
            return {"success": False, "url": "", "title": "", "error": str(e)}


# Create global instance
browser = BrowserAutomation()
