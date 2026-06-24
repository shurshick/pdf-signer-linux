import locale


_translations = {
    "ru": {
        "app_title": "PDF Signer Linux",
        "files": "PDF-файлы",
        "add_files": "Добавить PDF",
        "remove_file": "Убрать",
        "clear": "Очистить",
        "certificate": "Сертификаты",
        "cn": "Владелец",
        "store": "Хранилище",
        "valid_to": "Действителен до",
        "thumbprint": "Отпечаток",
        "refresh": "Обновить",
        "options": "Параметры",
        "output_folder": "Папка результата",
        "browse": "Выбрать",
        "save_next_to": "Сохранять рядом с исходным PDF",
        "verify_after": "Проверять после подписания",
        "signing_reason": "Назначение подписи",
        "default_reason": "Подписано в PDF Signer Linux",
        "stamp_profile": "Профиль штампа",
        "position": "Позиция штампа",
        "pages": "Страницы",
        "sign": "Подписать",
        "about": "О приложении",
        "about_title": "О приложении",
        "version": "Версия",
        "project": "Проект",
        "ready": "Готово",
        "loading_certs": "Загрузка сертификатов...",
        "found_certs": "Найдено сертификатов: {count}",
        "error_loading_certs": "Ошибка загрузки сертификатов: {error}",
        "owner": "Владелец:",
        "issuer": "Издатель:",
        "serial": "Серийный номер:",
        "no_files": "Добавьте хотя бы один PDF-файл.",
        "no_certificate": "Выберите сертификат.",
        "signing": "Подписание...",
        "signing_progress": "Подписано {current} из {total}: {file}",
        "done": "Подписание завершено.",
        "processed_files": "Обработано файлов: {count}",
        "signing_failed": "Ошибка подписания:",
        "error": "Ошибка",
        "crypto_unavailable": "CryptoPro CSP недоступен",
        "minimal": "Минимальный",
        "standard": "Стандартный",
        "detailed": "Подробный",
        "bottom_right": "Правый нижний",
        "bottom_left": "Левый нижний",
        "top_right": "Правый верхний",
        "top_left": "Левый верхний",
        "select_pdf": "Выберите PDF-файлы",
        "select_output": "Выберите папку для подписанных PDF",
        "pdf_filter": "PDF-файлы (*.pdf);;Все файлы (*.*)",
        "file_count": "Файлов: {count}, размер: {size}",
    },
    "en": {
        "app_title": "PDF Signer Linux",
        "files": "PDF files",
        "add_files": "Add PDFs",
        "remove_file": "Remove",
        "clear": "Clear",
        "certificate": "Certificates",
        "cn": "Name",
        "store": "Store",
        "valid_to": "Valid to",
        "thumbprint": "Thumbprint",
        "refresh": "Refresh",
        "options": "Options",
        "output_folder": "Output folder",
        "browse": "Browse",
        "save_next_to": "Save next to source PDF",
        "verify_after": "Verify after signing",
        "signing_reason": "Signing reason",
        "default_reason": "Signed with PDF Signer Linux",
        "stamp_profile": "Stamp profile",
        "position": "Stamp position",
        "pages": "Pages",
        "sign": "Sign",
        "about": "About",
        "about_title": "About",
        "version": "Version",
        "project": "Project",
        "ready": "Ready",
        "loading_certs": "Loading certificates...",
        "found_certs": "Found {count} certificate(s)",
        "error_loading_certs": "Error loading certificates: {error}",
        "owner": "Owner:",
        "issuer": "Issuer:",
        "serial": "Serial:",
        "no_files": "Add at least one PDF file.",
        "no_certificate": "Select a certificate.",
        "signing": "Signing...",
        "signing_progress": "Signed {current} of {total}: {file}",
        "done": "Signing completed.",
        "processed_files": "Processed {count} file(s)",
        "signing_failed": "Signing failed:",
        "error": "Error",
        "crypto_unavailable": "CryptoPro CSP unavailable",
        "minimal": "Minimal",
        "standard": "Standard",
        "detailed": "Detailed",
        "bottom_right": "Bottom Right",
        "bottom_left": "Bottom Left",
        "top_right": "Top Right",
        "top_left": "Top Left",
        "select_pdf": "Select PDF files",
        "select_output": "Select output folder for signed PDFs",
        "pdf_filter": "PDF files (*.pdf);;All files (*.*)",
        "file_count": "Files: {count}, size: {size}",
    },
}


def _get_system_lang() -> str:
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            return lang[:2]
    except Exception:
        pass
    return "en"


_current_lang = None


def get_lang() -> str:
    global _current_lang
    if _current_lang is None:
        _current_lang = _get_system_lang()
    return _current_lang


def set_lang(lang: str):
    global _current_lang
    _current_lang = lang


def t(key: str, **kwargs) -> str:
    lang = get_lang()
    strings = _translations.get(lang, _translations["en"])
    text = strings.get(key, _translations["en"].get(key, key))
    if kwargs:
        text = text.format(**kwargs)
    return text
