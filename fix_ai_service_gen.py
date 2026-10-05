import os
import re

ai_service_path = '/home/ubuntu/safar360/backend/app/services/ai_service.py'
with open(ai_service_path, 'r', encoding='utf-8') as f:
    code = f.read()

# The error happens in generate_completion because we removed the img_match code but left the `if img_response:`
code = code.replace("""        # Apply Regex Filters
        reply_content = filter_tts_text(reply_content)
        if img_response:
            reply_content += img_response""",
"""        # Apply Regex Filters
        reply_content = filter_tts_text(reply_content)""")

with open(ai_service_path, 'w', encoding='utf-8') as f:
    f.write(code)
