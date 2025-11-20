from __future__ import annotations
from flask import request, session, jsonify, current_app, Response
import flask
from modules import dbms
from modules.dbms import ChatThread, ChatHistory
from flask_login import current_user
from xai_sdk.chat import user, system
import modules.extensions as extensions
import os
import asyncio

from modules.llm_client import LLMClient

db = extensions.db
debug_ai_messages = False

#
#
#
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

#
#
#
def _save_history(thread_id: int, prompt: str, model_name: str, reply: str) -> None:
    """
    Saves a prompt and response to the history
    """
    new_message = ChatHistory(
        thread_id=thread_id,
        user_input=prompt,
        model_name=model_name,
        model_response=reply
    )
    db.session.add(new_message)
    db.session.commit()

#
#
#
def _get_history_context(max_messages: int) -> list[(str, str)]:
    """
    returns the parts of chat history to be included in the prompt.
    """
    thread_id = flask.session.get("current_thread_id")
    if thread_id is None:
        return []
    else:
        messages = []
        for entry in dbms.get_history_entries(thread_id):
            if len(messages) >= max_messages:
                return messages
            messages.append((entry.user_input, entry.model_response))
        return messages

#
#
#
def single_llm_endpoint(client: LLMClient) -> Response:
    """
    Endpoint that returns a response from a specific LLM.
    """
    if client is None:
        return jsonify({"error", "Unknown LLM"}), 400

    prompt = request.get_json(force=True).get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    current_app.logger.info("%s endpoint called; model=%s prompt_len=%d", client.name, client.model, len(prompt))
    current_thread = _get_or_create_thread(prompt)

    if debug_ai_messages:
        reply = f"This is a {client.name} response from debug mode."
        _save_history(current_thread.id, prompt, f"{client.model}-debug", reply)
        return jsonify({"reply": reply}), 200

    else:
        reply = ""
        try:
            reply = asyncio.run(client.get_reply(
                system_prompt=client.system_prompt(),
                user_prompt=prompt,
                history=_get_history_context(2)
            ))
            _save_history(current_thread.id, prompt, client.model, reply)
            return jsonify({"reply": reply})
        except Exception as e:
            current_app.logger.exception(f"{client.name} request failed")
            return jsonify({"error": str(e)}), 500


#TODO: Add an endpoint allowing multiple LLMS to be queried in parallel using async
def multi_llm_endpoint(client: list[LLMClient]) -> Response:
    pass


def gpt()      -> Response: return single_llm_endpoint(extensions.gpt_client)
def gemini()   -> Response: return single_llm_endpoint(extensions.gemini_client)
def claude()   -> Response: return single_llm_endpoint(extensions.claude_client)
def grok()     -> Response: return single_llm_endpoint(extensions.grok_client)
def deepseek() -> Response: return single_llm_endpoint(extensions.deepseek_client)
def falcon()   -> Response: return jsonify({"reply": "This is a Falcon response."}), 200
def mistral()  -> Response: return jsonify({"reply": "This is a Mistral response."}), 200
def bert()     -> Response: return jsonify({"reply": "This is a BERT response."}), 200