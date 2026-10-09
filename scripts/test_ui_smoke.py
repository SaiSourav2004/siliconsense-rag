import os
import sys
from streamlit.testing.v1 import AppTest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

def test_streamlit_app_smoke():
    app_path = os.path.join(ROOT_DIR, "app.py")
    
    # 1. Initialize the app
    at = AppTest.from_file(app_path)
    
    # Run the app initially
    at.run(timeout=120)
    
    # 2. Check title
    assert not at.exception, "App crashed on startup"
    assert len(at.title) > 0
    assert "SiliconSense RAG" in at.title[0].value
    
    # 3. Simulate user input
    # Set text area
    query_input = at.text_area[0]
    query_input.set_value("STM32F401RE MCU with 512KB Flash")
    
    # 4. Click search button
    search_btn = at.button[0]
    assert search_btn.label == "Search Candidates"
    
    # 5. Run the app with the button click
    at.button[0].click().run(timeout=120)
    
    # 6. Verify results
    assert not at.exception, "App crashed during search execution"
    
    # Look for Candidate Rankings section
    rankings_header_found = any(h.value == "Candidate Rankings" for h in at.header)
    assert rankings_header_found, "Candidate Rankings header not found in the output"
    
    print("UI Smoke Test Passed!")

if __name__ == "__main__":
    test_streamlit_app_smoke()
