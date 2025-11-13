from __future__ import annotations
import os
from flask import request, session, jsonify, current_app
import modules.extensions as extensions
from modules.database_classes import ChatThread, ChatHistory
from flask_login import current_user
from xai_sdk.chat import user, system

db = extensions.db
debug_ai_messages = True

def _get_or_create_thread(prompt: str) -> ChatThread:
    thread_id = session.get('current_thread_id')
    if thread_id is not None:
        thread = db.session.get(ChatThread, thread_id)
        if thread:
            return thread

    thread_title = prompt[:10] + ("..." if len(prompt) > 50 else "")
    thread = ChatThread(user_id=current_user.id, thread_name=thread_title)
    db.session.add(thread)
    db.session.commit()
    session['current_thread_id'] = thread.id
    return thread

def _save_history(thread_id: int, prompt: str, model_name: str, reply: str) -> None:
    new_message = ChatHistory(
        thread_id=thread_id,
        user_input=prompt,
        model_name=model_name,
        model_response=reply
    )
    db.session.add(new_message)
    db.session.commit()

def gpt():
    # existing GPT implementation (unchanged)...
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    current_app.logger.info("Chat endpoint called; model=%s prompt_len=%d", model, len(prompt))

    current_thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a ChatGPT response from debug mode."
        _save_history(current_thread.id, prompt, f"{model}-debug", reply)
        return jsonify({"reply": reply}), 200

    try:
        thread_id = session.get('current_thread_id')
        messages = [{"role": "system", "content": "asdfasdf"}]

        if thread_id is not None:
            history_entries = ChatHistory.query.filter_by(thread_id=thread_id).order_by(ChatHistory.id.desc()).limit(2).all()
            history_entries.reverse()
            for entry in history_entries:
                messages.append({"role": "user", "content": entry.user_input})
                messages.append({"role": "assistant", "content": entry.model_response})

        messages.append({"role": "user", "content": prompt})

        if extensions.gpt_client is None:
            raise RuntimeError("OpenAI client not initialized. Call init_extensions(...) before using the chat endpoint.")

        completion = extensions.gpt_client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            temperature=0.2,
            max_tokens=120,
            top_p=1.0
        )

        reply = completion.choices[0].message.content

        _save_history(current_thread.id, prompt, model, reply)
        return jsonify({"reply": reply})

    except Exception as e:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": str(e)}), 500

# python
def gemini():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_app.logger.info("Gemini endpoint called; prompt_len=%d", len(prompt))
    thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a Gemini response from debug mode."
        _save_history(thread.id, prompt, "gemini-debug", reply)
        return jsonify({"reply": reply}), 200

    client = getattr(extensions, "gemini_client", None)
    if client is None:
        current_app.logger.error("Gemini SDK client not initialized")
        return jsonify({"error": "Gemini client not configured"}), 500

    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    try:
        resp = client.models.generate_content(model=model, contents=prompt)
        # normalize response shapes (SDK may expose .text, .output or return a dict)
        reply = getattr(resp, "text", None) or getattr(resp, "output", None)
        if reply is None:
            try:
                body = resp if isinstance(resp, dict) else resp.__dict__
                candidates = body.get("candidates") if isinstance(body, dict) else None
            except Exception:
                candidates = None
            if candidates:
                reply = candidates[0].get("content") or candidates[0].get("text") or candidates[0].get("output")
            else:
                reply = str(resp)
        _save_history(thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200
    except Exception as e:
        current_app.logger.exception("Gemini SDK request failed")
        return jsonify({"error": str(e)}), 502

def claude():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_app.logger.info("Claude endpoint called; prompt_len=%d", len(prompt))
    thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a Claude response from debug mode."
        _save_history(thread.id, prompt, "claude-debug", reply)
        return jsonify({"reply": reply}), 200

    client = getattr(extensions, "claude_client", None)
    if client is None:
        current_app.logger.error("Claude SDK client not initialized")
        return jsonify({"error": "Claude client not configured"}), 500

    model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    try:
        max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "1000"))
    except Exception:
        max_tokens = 1000

    try:
        messages = [{"role": "user", "content": prompt}]
        resp = client.messages.create(model=model, max_tokens=max_tokens, messages=messages)

        # Helper to extract text from various shapes
        def _text_of(item):
            if item is None:
                return ""
            if isinstance(item, str):
                return item
            text = getattr(item, "text", None) or getattr(item, "content", None)
            if text is None and isinstance(item, dict):
                text = item.get("text") or item.get("content")
            return str(text) if text is not None else str(item)

        # Prefer direct attributes, fall back to dict keys
        reply_candidate = getattr(resp, "content", None) or getattr(resp, "text", None)
        if reply_candidate is None and isinstance(resp, dict):
            reply_candidate = resp.get("content") or resp.get("text")
        if reply_candidate is None:
            reply_candidate = resp

        # Normalize lists and objects to a single string
        if isinstance(reply_candidate, list):
            parts = [_text_of(it) for it in reply_candidate]
            reply = "\n".join([p for p in parts if p]).strip()
        else:
            reply = _text_of(reply_candidate).strip()

        if not reply:
            reply = str(resp)

        _save_history(thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200

    except Exception as e:
        current_app.logger.exception("Claude SDK request failed")
        return jsonify({"error": str(e)}), 502

def grok():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_app.logger.info("Grok endpoint called; prompt_len=%d", len(prompt))
    thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a Grok response from debug mode."
        _save_history(thread.id, prompt, "grok-debug", reply)
        return jsonify({"reply": reply}), 200

    client = getattr(extensions, "grok_client", None)
    if client is None:
        current_app.logger.error("Grok SDK client not initialized")
        return jsonify({"error": "Grok client not configured"}), 500

    model = os.getenv("GROK_MODEL", "grok-3-mini")
    try:
        chat = client.chat.create(model=model)
        chat.append(system("You are Grok, a highly intelligent, helpful AI assistant."))
        chat.append(user(prompt))

        response = chat.sample()

        reply = getattr(response, "content", None) or getattr(response, "text", None) or getattr(response, "output", None) or str(response)

        _save_history(thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200

    except Exception as e:
        current_app.logger.exception("Grok SDK request failed")
        return jsonify({"error": str(e)}), 502

def deepseek():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_app.logger.info("DeepSeek endpoint called; prompt_len=%d", len(prompt))
    thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a DeepSeek response from debug mode."
        _save_history(thread.id, prompt, "deepseek-debug", reply)
        return jsonify({"reply": reply}), 200

    client = getattr(extensions, "deepseek_client", None)
    if client is None:
        current_app.logger.error("DeepSeek SDK client not initialized")
        return jsonify({"error": "DeepSeek client not configured"}), 500

    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    try:
        # Build messages with a small system prompt and recent history (last 2 entries)
        messages = [{"role": "system", "content": "You are a helpful assistant"}]
        thread_id = session.get('current_thread_id')
        if thread_id is not None:
            history_entries = ChatHistory.query.filter_by(thread_id=thread_id).order_by(ChatHistory.id.desc()).limit(2).all()
            history_entries.reverse()
            for entry in history_entries:
                messages.append({"role": "user", "content": entry.user_input})
                messages.append({"role": "assistant", "content": entry.model_response})

        messages.append({"role": "user", "content": prompt})

        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False
        )

        reply = None
        try:
            choices = getattr(resp, "choices", None)
            if choices and len(choices) > 0:
                msg = getattr(choices[0], "message", None)
                reply = getattr(msg, "content", None) if msg is not None else None
        except Exception:
            reply = None

        if reply is None:
            reply = getattr(resp, "content", None) or getattr(resp, "text", None)
        if reply is None:
            try:
                # attempt dict access if SDK returned a dict-like response
                if isinstance(resp, dict):
                    if "choices" in resp and resp["choices"]:
                        c = resp["choices"][0]
                        reply = (c.get("message") or {}).get("content") or c.get("text")
            except Exception:
                pass
        if reply is None:
            reply = str(resp)

        _save_history(thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200

    except Exception as e:
        current_app.logger.exception("DeepSeek SDK request failed")
        return jsonify({"error": str(e)}), 502

def falcon():
    return jsonify({"reply": "This is a Falcon response."}), 200

def mistral():
    return jsonify({"reply": "This is a Mistral response."}), 200

def bert():
    return jsonify({"reply": "This is a BERT response."}), 200