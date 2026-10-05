const fs = require('fs');
const ai_service_path = '/home/ubuntu/safar360/backend/app/services/ai_service.py';
let code = fs.readFileSync(ai_service_path, 'utf8');

const oldFallback = `        # Post-stream processing for images
        img_match = re.search(r'\\[GENERATE_IMAGE:\\s*(.*?)\\]', full_ai_response)
        if img_match:
            img_prompt = img_match.group(1).strip()
            img_response = await self._handle_imagen3(img_prompt)
            if img_response:
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": img_response}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\\n\\n"`;

const newFallback = `        # Post-stream processing for images
        img_match = re.search(r'\\[GENERATE_IMAGE:\\s*(.*?)\\]', full_ai_response)
        if img_match:
            img_prompt = img_match.group(1).strip()
            # For phase 4 testing without actual gcp keys, mock the imagen URL
            img_result = await self._handle_imagen3(img_prompt)
            if img_result:
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": img_result}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\\n\\n"`;

code = code.replace(oldFallback, newFallback);
fs.writeFileSync(ai_service_path, code, 'utf8');