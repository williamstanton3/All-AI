var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
export function fetchChatGPTResponse(prompt) {
    return __awaiter(this, void 0, void 0, function* () {
        const res = yield fetch("/api/chatgpt", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt })
        });
        const text = yield res.text();
        if (!res.ok) {
            console.error("[chatgptService] non-ok response:", res.status, text);
            throw new Error(text || "ChatGPT request failed");
        }
        let data;
        try {
            data = JSON.parse(text);
        }
        catch (err) {
            console.error("[chatgptService] invalid JSON:", text);
            throw new Error("Invalid JSON from server");
        }
        if (!("reply" in data)) {
            console.error("[chatgptService] missing reply field:", data);
            throw new Error("No `reply` field in response: " + JSON.stringify(data));
        }
        return data.reply;
    });
}
//# sourceMappingURL=chatgptService.js.map