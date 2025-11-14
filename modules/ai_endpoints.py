from __future__ import annotations
import os
from flask import request, session, jsonify, current_app
import modules.extensions as extensions
from modules.database_classes import ChatThread, ChatHistory
from flask_login import current_user
from xai_sdk.chat import user, system

db = extensions.db
debug_ai_messages = False

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
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    gpt_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    model = "GPT"
    current_thread = _get_or_create_thread(prompt)
    client = extensions.gpt_client

    if debug_ai_messages:
        reply = "This is a ChatGPT response from debug mode."
        _save_history(current_thread.id, prompt, model, reply)
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

        completion = client.chat.completions.create(
            model=gpt_model,
            messages=messages,
            temperature=0.2,
            max_tokens=100,
            top_p=1.0
        )
        reply = completion.choices[0].message.content
        _save_history(current_thread.id, prompt, model, reply)
        return jsonify({"reply": reply})

    except Exception as e:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": str(e)}), 500

def gemini():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = "GEMINI"
    current_thread = _get_or_create_thread(prompt)
    client = extensions.gemini_client

    if debug_ai_messages:
        reply = "This is a Gemini response from debug mode."
        _save_history(current_thread.id, prompt, "gemini-debug", reply)
        return jsonify({"reply": reply}), 200

    try:
        resp = client.models.generate_content(model=gemini_model, contents=prompt)
        reply = resp.text
        _save_history(current_thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200
    except Exception as e:
        current_app.logger.exception("Gemini SDK request failed")
        return jsonify({"error": str(e)}), 502

def claude():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    claude_model = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")
    model = "CLAUDE"
    client = extensions.claude_client
    current_thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a Claude response from debug mode."
        _save_history(current_thread.id, prompt, "claude-debug", reply)
        return jsonify({"reply": reply}), 200

    try:
        messages = [{"role": "user", "content": prompt}]
        resp = client.messages.create(model=claude_model, max_tokens=100, messages=messages)
        reply = resp.content[0].text

        _save_history(current_thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200

    except Exception as e:
        current_app.logger.exception("Claude SDK request failed")
        return jsonify({"error": str(e)}), 502

def grok():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = "GROK"
    grok_model = os.getenv("GROK_MODEL", "grok-3-mini")
    client = extensions.grok_client
    current_thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a Grok response from debug mode."
        _save_history(current_thread.id, prompt, "grok-debug", reply)
        return jsonify({"reply": reply}), 200

    if client is None:
        current_app.logger.error("Grok SDK client not initialized")
        return jsonify({"error": "Grok client not configured"}), 500

    try:
        chat = client.chat.create(model=grok_model, max_tokens=100)
        chat.append(system("You are Grok, a highly intelligent, helpful AI assistant."))
        chat.append(user(prompt))
        reply = chat.sample()
        _save_history(current_thread.id, prompt, model, reply)
        return jsonify({"reply": reply}), 200

    except Exception as e:
        current_app.logger.exception("Grok SDK request failed")
        return jsonify({"error": str(e)}), 502

def deepseek():
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = "This is a DeepSeek response from debug mode."
        _save_history(current_thread.id, prompt, "deepseek-debug", reply)
        return jsonify({"reply": reply}), 200

    client = extensions.deepseek_client

    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    try:
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
            max_tokens=100,
            stream=False
        )
        reply = resp.choices[0].message.content
        _save_history(current_thread.id, prompt, model, reply)
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