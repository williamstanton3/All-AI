from __future__ import annotations
import os
from flask import request, session, jsonify, current_app
import modules.extensions as extensions
from modules.database_classes import ChatThread, ChatHistory
from flask_login import current_user

db = extensions.db
debug_ai_messages = True

def gpt():
    # Parse input early so we can use the prompt for thread/title even in debug mode
    data = request.get_json(force=True)
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    current_app.logger.info("Chat endpoint called; model=%s prompt_len=%d", model, len(prompt))

    # Ensure we have or create a thread (preserve DB behavior)
    thread_id = session.get('current_thread_id')
    current_thread = None

    if thread_id is not None:
        current_thread = db.session.get(ChatThread, thread_id)
    else:
        thread_title = prompt[:10] + ("..." if len(prompt) > 50 else "")
        current_thread = ChatThread(
            user_id=current_user.id,
            thread_name=thread_title
        )
        db.session.add(current_thread)
        db.session.commit()
        session['current_thread_id'] = current_thread.id

    # Debug branch: do not call external API, but still save history and return JSON
    if debug_ai_messages:
        reply = "This is a ChatGPT response from debug mode."
        # Optionally include an echo of the prompt (commented out)
        # reply = f"This is a ChatGPT response from debug mode. Echo: {prompt}"

        new_message = ChatHistory(
            thread_id=current_thread.id,
            user_input=prompt,
            model_name=f"{model}-debug",
            model_response=reply
        )
        db.session.add(new_message)
        db.session.commit()

        return jsonify({"reply": reply}), 200

    # Normal runtime: build messages and call OpenAI client
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

        if extensions.client is None:
            raise RuntimeError("OpenAI client not initialized. Call init_extensions(...) before using the chat endpoint.")

        completion = extensions.client.chat.completions.create(
            model=model,
            messages=messages,  # type: ignore
            temperature=0.2,
            max_tokens=120,
            top_p=1.0
        )

        reply = completion.choices[0].message.content

        new_message = ChatHistory(
            thread_id=current_thread.id,
            user_input=prompt,
            model_name=model,
            model_response=reply
        )
        db.session.add(new_message)
        db.session.commit()

        return jsonify({"reply": reply})

    except Exception as e:
        current_app.logger.exception("OpenAI request failed")
        return jsonify({"error": str(e)}), 500

def gemini():
    return jsonify({"reply": "This is a Gemini response."}), 200

def claude():
    return jsonify({"reply": "This is a Claude response."}), 200

def bard():
    return jsonify({"reply": "This is a Bard response."}), 200

def llama():
    return jsonify({"reply": "This is a LLaMA response."}), 200

def grok():
    return jsonify({"reply": "This is a Grok response."}), 200

def deepseek():
    return jsonify({"reply": "This is a DeepSeek response."}), 200