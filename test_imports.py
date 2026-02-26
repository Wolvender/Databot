#!/usr/bin/env python
"""Quick test to verify all modules can be imported"""

import sys

try:
    print("Testing imports...")
    print("  → config.py", end=" ... ")
    import config
    print("✓")
    
    print("  → auth.py", end=" ... ")
    import auth
    print("✓")
    
    print("  → file_handler.py", end=" ... ")
    import file_handler
    print("✓")
    
    print("  → data_processor.py", end=" ... ")
    import data_processor
    print("✓")
    
    print("  → ui_components.py", end=" ... ")
    import ui_components
    print("✓")
    
    print("\n✅ All modules imported successfully!")
    print(f"\nModule summary:")
    print(f"  - config: LLM_MODEL={config.LLM_MODEL}, LLM_TEMPERATURE={config.LLM_TEMPERATURE}")
    print(f"  - auth: check_password(), login_user(), logout_user()")
    print(f"  - file_handler: extract_text(), is_supported_file()")
    print(f"  - data_processor: DataProcessor class initialized")
    print(f"  - ui_components: {sum(1 for name in dir(ui_components) if name.startswith('render_'))} render_* functions")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
