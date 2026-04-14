module.exports = [
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}),
"[project]/src/lib/api.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getChatHistory",
    ()=>getChatHistory,
    "getEngines",
    ()=>getEngines,
    "getSessions",
    ()=>getSessions,
    "healthcheck",
    ()=>healthcheck,
    "initStreamingQuery",
    ()=>initStreamingQuery,
    "login",
    ()=>login,
    "sendFeedback",
    ()=>sendFeedback,
    "sendQuery",
    ()=>sendQuery,
    "streamQuery",
    ()=>streamQuery,
    "streamQueryGenerator",
    ()=>streamQueryGenerator
]);
const API_BASE = ("TURBOPACK compile-time value", "http://main-app:8000") || "http://localhost:8000";
async function login(params) {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(params)
    });
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}
async function sendQuery(params) {
    const response = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(params)
    });
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}
async function initStreamingQuery(params) {
    const response = await fetch(`${API_BASE}/api/query_init`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(params)
    });
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}
async function streamQuery(messageId, userId, sessionId, callbacks) {
    const params = new URLSearchParams({
        id: messageId,
        user_id: userId,
        session_id: sessionId
    });
    const response = await fetch(`${API_BASE}/api/query_stream?${params}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const reader = response.body?.getReader();
    if (!reader) {
        throw new Error("No response body");
    }
    const decoder = new TextDecoder();
    let buffer = "";
    try {
        while(true){
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, {
                stream: true
            });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";
            for (const line of lines){
                if (line.startsWith("event: ")) {
                    const eventType = line.slice(7).trim();
                    continue;
                }
                if (line.startsWith("data: ")) {
                    const data = line.slice(6);
                    // Parse based on most recent event type
                    // For simplicity, we handle common patterns
                    if (data === "[DONE]") {
                        continue;
                    }
                // The SSE format sends event: then data: on next line
                // We need to track the event type
                }
            }
        }
    } finally{
        reader.releaseLock();
    }
}
async function* streamQueryGenerator(messageId, userId, sessionId) {
    const params = new URLSearchParams({
        id: messageId,
        user_id: userId,
        session_id: sessionId
    });
    const response = await fetch(`${API_BASE}/api/query_stream?${params}`);
    if (!response.ok) {
        yield {
            type: "error",
            data: `HTTP ${response.status}`
        };
        return;
    }
    const reader = response.body?.getReader();
    if (!reader) {
        yield {
            type: "error",
            data: "No response body"
        };
        return;
    }
    const decoder = new TextDecoder();
    let buffer = "";
    let currentEventType = "chunk";
    try {
        while(true){
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, {
                stream: true
            });
            // Process line by line
            const lines = buffer.split("\n");
            // Keep the last incomplete line in the buffer
            buffer = lines.pop() || "";
            for (const line of lines){
                if (line.startsWith("event: ")) {
                    currentEventType = line.slice(7).trim();
                } else if (line.startsWith("data: ")) {
                    const data = line.slice(6);
                    switch(currentEventType){
                        case "chunk":
                            yield {
                                type: "chunk",
                                data
                            };
                            break;
                        case "alert":
                            yield {
                                type: "alert",
                                data
                            };
                            break;
                        case "remapped_response":
                            yield {
                                type: "remapped",
                                data
                            };
                            break;
                        case "done":
                            try {
                                const parsed = JSON.parse(data);
                                yield {
                                    type: "done",
                                    data: parsed
                                };
                            } catch  {
                                yield {
                                    type: "error",
                                    data: "Failed to parse response"
                                };
                            }
                            break;
                        case "error":
                            yield {
                                type: "error",
                                data
                            };
                            break;
                    }
                }
            // Empty lines are ignored (they separate events in SSE)
            }
        }
    } finally{
        reader.releaseLock();
    }
}
async function sendFeedback(params) {
    const response = await fetch(`${API_BASE}/api/feedback`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(params)
    });
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
}
async function getEngines(userId, sessionId) {
    const params = new URLSearchParams({
        user_id: userId
    });
    if (sessionId) {
        params.append("session_id", sessionId);
    }
    const response = await fetch(`${API_BASE}/api/engines?${params}`);
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}
async function healthcheck() {
    try {
        const response = await fetch(`${API_BASE}/api/healthcheck`);
        return response.ok;
    } catch  {
        return false;
    }
}
async function getSessions(userId) {
    const params = new URLSearchParams({
        user_id: userId
    });
    const response = await fetch(`${API_BASE}/api/sessions?${params}`);
    if (!response.ok) {
        const error = await response.json().catch(()=>({
                detail: "Unknown error"
            }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}
async function getChatHistory(userId, sessionId) {
    const params = new URLSearchParams({
        user_id: userId,
        session_id: sessionId
    });
    try {
        const response = await fetch(`${API_BASE}/api/chat_history?${params}`);
        if (response.status === 404) {
            // Session not found - this is expected for new sessions
            return null;
        }
        if (!response.ok) {
            const error = await response.json().catch(()=>({
                    detail: "Unknown error"
                }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        return response.json();
    } catch (err) {
        console.error("Failed to load chat history:", err);
        return null;
    }
}
}),
"[project]/src/hooks/useAuth.ts [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AuthContext",
    ()=>AuthContext,
    "useAuth",
    ()=>useAuth,
    "useAuthState",
    ()=>useAuthState
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/lib/api.ts [app-ssr] (ecmascript)");
"use client";
;
;
const AUTH_STORAGE_KEY = "auth-user";
const AuthContext = /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["createContext"])(null);
function useAuth() {
    const context = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useContext"])(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
function useAuthState() {
    const [authState, setAuthState] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useState"])({
        isAuthenticated: false,
        userId: null,
        isLoading: true
    });
    // Load auth state from localStorage on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useEffect"])(()=>{
        try {
            const stored = localStorage.getItem(AUTH_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                setAuthState({
                    isAuthenticated: true,
                    userId: parsed.userId,
                    isLoading: false
                });
            } else {
                setAuthState((prev)=>({
                        ...prev,
                        isLoading: false
                    }));
            }
        } catch (err) {
            console.error("Failed to load auth state:", err);
            setAuthState((prev)=>({
                    ...prev,
                    isLoading: false
                }));
        }
    }, []);
    const login = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])(async (username, password)=>{
        try {
            const response = await (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$lib$2f$api$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["login"])({
                username,
                password
            });
            if (response.success && response.user_id) {
                const authData = {
                    userId: response.user_id
                };
                localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
                setAuthState({
                    isAuthenticated: true,
                    userId: response.user_id,
                    isLoading: false
                });
                return true;
            }
            return false;
        } catch (err) {
            console.error("Login failed:", err);
            return false;
        }
    }, []);
    const logout = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useCallback"])(()=>{
        localStorage.removeItem(AUTH_STORAGE_KEY);
        setAuthState({
            isAuthenticated: false,
            userId: null,
            isLoading: false
        });
    }, []);
    return {
        ...authState,
        login,
        logout
    };
}
;
}),
"[project]/src/components/auth/AuthProvider.tsx [app-ssr] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "AuthProvider",
    ()=>AuthProvider
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$hooks$2f$useAuth$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/hooks/useAuth.ts [app-ssr] (ecmascript)");
"use client";
;
;
function AuthProvider({ children }) {
    const authState = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$hooks$2f$useAuth$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["useAuthState"])();
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$ssr$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$hooks$2f$useAuth$2e$ts__$5b$app$2d$ssr$5d$__$28$ecmascript$29$__["AuthContext"].Provider, {
        value: authState,
        children: children
    }, void 0, false, {
        fileName: "[project]/src/components/auth/AuthProvider.tsx",
        lineNumber: 14,
        columnNumber: 5
    }, this);
}
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
;
else {
    if ("TURBOPACK compile-time falsy", 0) //TURBOPACK unreachable
    ;
    else {
        if ("TURBOPACK compile-time truthy", 1) {
            if ("TURBOPACK compile-time truthy", 1) {
                module.exports = __turbopack_context__.r("[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)");
            } else //TURBOPACK unreachable
            ;
        } else //TURBOPACK unreachable
        ;
    }
} //# sourceMappingURL=module.compiled.js.map
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react-jsx-dev-runtime.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].ReactJsxDevRuntime; //# sourceMappingURL=react-jsx-dev-runtime.js.map
}),
"[project]/node_modules/next/dist/server/route-modules/app-page/vendored/ssr/react.js [app-ssr] (ecmascript)", ((__turbopack_context__, module, exports) => {
"use strict";

module.exports = __turbopack_context__.r("[project]/node_modules/next/dist/server/route-modules/app-page/module.compiled.js [app-ssr] (ecmascript)").vendored['react-ssr'].React; //# sourceMappingURL=react.js.map
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__3d6c87f4._.js.map