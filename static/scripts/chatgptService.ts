export async function fetchChatGPTResponse(prompt: string): Promise<string> {
    const res = await fetch("/api/chatgpt", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ prompt })
    });

    const text = await res.text();
    if (!res.ok) {
        console.error("[chatgptService] non-ok response:", res.status, text);
        throw new Error(text || "ChatGPT request failed");
    }

    let data: any;
    try {
        data = JSON.parse(text);
    } catch (err) {
        console.error("[chatgptService] invalid JSON:", text);
        throw new Error("Invalid JSON from server");
    }

    if (!("reply" in data)) {
        console.error("[chatgptService] missing reply field:", data);
        throw new Error("No `reply` field in response: " + JSON.stringify(data));
    }

    return data.reply;
}