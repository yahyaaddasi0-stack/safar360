import os
import re

ai_service_path = '/home/ubuntu/safar360/backend/app/services/ai_service.py'
with open(ai_service_path, 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Update SYSTEM_PROMPTS
code = code.replace(
    '"system_prompt": "أنت صلاح الدين الأيوبي، القائد المسلم التاريخي البطل. تتحدث بحكمة وعدل وشجاعة. لا تستخدم ألقاباً مصطنعة مثل (يضحك) أو (يبتسم).",',
    '"system_prompt": "أنت صلاح الدين الأيوبي، القائد المسلم التاريخي البطل. تتحدث بحكمة وعدل وشجاعة. لا تستخدم ألقاباً مصطنعة مثل (يضحك) أو (يبتسم). إذا طلب منك المستخدم رسم صورة أو إظهار خريطة، أضف العلامة [GENERATE_IMAGE: وصف الصورة بالإنجليزية] في نهاية ردك.",'
)
code = code.replace(
    '"system_prompt": "أنت الشاعر المتنبي. تتحدث بفخر واعتزاز وبلاغة عربية. لا تستخدم ألقاباً مصطنعة أو حركات مسرحية مثل (يتنهد) أو (يضحك).",',
    '"system_prompt": "أنت الشاعر المتنبي. تتحدث بفخر واعتزاز وبلاغة عربية. لا تستخدم ألقاباً مصطنعة أو حركات مسرحية مثل (يتنهد) أو (يضحك). إذا طلب منك المستخدم رسم صورة أو مشهد، أضف العلامة [GENERATE_IMAGE: وصف المشهد بالإنجليزية] في نهاية ردك.",'
)
code = code.replace(
    '"system_prompt": "أنت الملكة زنوبيا ملكة تدمر. تتحدثين بكبرياء وقوة ملكية. لا تستخدمي حركات أو انفعالات بين قوسين مثل (تبتسم).",',
    '"system_prompt": "أنت الملكة زنوبيا ملكة تدمر. تتحدثين بكبرياء وقوة ملكية. لا تستخدمي حركات أو انفعالات بين قوسين مثل (تبتسم). إذا طلب منك المستخدم رسم صورة أو معبد، أضفي العلامة [GENERATE_IMAGE: وصف الصورة بالإنجليزية] في نهاية ردك.",'
)

# 2. Modify stream_completion to extract image requests
stream_completion_regex = re.compile(r'async def stream_completion\([\s\S]*?yield f"data: \{json\.dumps\(stop_chunk, ensure_ascii=False\)\\n\\n"')

new_stream_completion = """async def stream_completion(self, request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
        stream_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        created_time = int(time.time())

        persona = CHARACTER_PERSONAS.get(request.character_id, CHARACTER_PERSONAS["salah-al-din"])
        sys_prompt = persona["system_prompt"]
        last_msg = request.messages[-1].content
        
        initial_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": settings.VERTEX_AI_MODEL,
            "character_id": request.character_id,
            "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
        }
        yield f"data: {json.dumps(initial_chunk, ensure_ascii=False)}\\n\\n"

        full_ai_response = ""

        if self.is_initialized and last_msg:
            try:
                chat = self.model.start_chat(history=self._get_history(request.messages))
                full_prompt = f"System: {sys_prompt}\\nUser: {last_msg}"
                responses = await chat.send_message_async(full_prompt, stream=True)
                
                async for chunk in responses:
                    filtered_text = filter_tts_text(chunk.text)
                    if filtered_text:
                        full_ai_response += filtered_text
                        data = {
                            "id": stream_id,
                            "object": "chat.completion.chunk",
                            "created": created_time,
                            "model": settings.VERTEX_AI_MODEL,
                            "character_id": request.character_id,
                            "choices": [{"index": 0, "delta": {"content": filtered_text}, "finish_reason": None}],
                        }
                        yield f"data: {json.dumps(data, ensure_ascii=False)}\\n\\n"
            except Exception as e:
                print(f"⚠️ [Vertex AI] Stream error: {e}")
                err_data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": "أعتذر، فقدنا الاتصال ببيت الحكمة."}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(err_data, ensure_ascii=False)}\\n\\n"
        else:
            # Fallback if no credentials
            fallback_msg = filter_tts_text(persona["greeting"])
            # Check user message for mock image request
            if "ارسم" in last_msg or "صورة" in last_msg:
                fallback_msg += " [GENERATE_IMAGE: majestic historical scene]"
                
            full_ai_response = fallback_msg
            words = fallback_msg.split(" ")
            for word in words:
                data = {
                    "id": stream_id,
                    "object": "chat.completion.chunk",
                    "created": created_time,
                    "model": settings.VERTEX_AI_MODEL,
                    "character_id": request.character_id,
                    "choices": [{"index": 0, "delta": {"content": word + " "}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(data, ensure_ascii=False)}\\n\\n"
                await asyncio.sleep(0.05)

        # Post-stream processing for images
        img_match = re.search(r'\\[GENERATE_IMAGE:\\s*(.*?)\\]', full_ai_response)
        if img_match:
            img_prompt = img_match.group(1)
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
                yield f"data: {json.dumps(data, ensure_ascii=False)}\\n\\n"

        stop_chunk = {
            "id": stream_id,
            "object": "chat.completion.chunk",
            "created": created_time,
            "model": settings.VERTEX_AI_MODEL,
            "character_id": request.character_id,
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }
        yield f"data: {json.dumps(stop_chunk, ensure_ascii=False)}\\n\\n" """

code = stream_completion_regex.sub(new_stream_completion, code)

# Remove the img_match block from generate_completion too
gen_img_regex = re.compile(r'# Check for Imagen 3 interceptor[\s\S]*?last_msg = last_msg\.replace\(img_match\.group\(0\), ""\)\.strip\(\)')
code = gen_img_regex.sub('', code)

with open(ai_service_path, 'w', encoding='utf-8') as f:
    f.write(code)
