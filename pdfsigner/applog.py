import os
import time
from pdfsigner import LOG_DIR, LOG_FILE


def _sanitize(value: str) -> str:
    if not value:
        return value
    result = value
    lower = result.lower()
    for kw in ("pin", "password", "пароль", "код", "secret", "key"):
        idx = lower.find(kw)
        if idx >= 0:
            eq = -1
            for ch in result[idx:]:
                if ch in ":=":
                    eq = result.index(ch, idx)
                    break
            if eq > 0:
                start = eq + 1
                while start < len(result) and result[start] in " \t":
                    start += 1
                end = len(result)
                for sep in " \t\n,;":
                    pos = result.find(sep, start)
                    if pos > 0 and pos < end:
                        end = pos
                result = result[:start] + "<redacted>" + result[end:]
                lower = result.lower()
    if "-----BEGIN" in result:
        s = result.index("-----BEGIN")
        e = result.find("-----END", s)
        if e > 0:
            after = result.find("-----", e + 8)
            if after > 0:
                result = result[:s] + "<redacted-certificate>" + result[after + 5:]
    return result


def log_info(message: str):
    _write("INFO", message, None)


def log_error(message: str, error: Exception = None):
    _write("ERROR", message, error)


def _write(level: str, message: str, error: Exception = None):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {_sanitize(message)}\n"
        if error:
            line += f"  error: {_sanitize(str(error))}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
