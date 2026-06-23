# PDF Signer Linux

Настольное приложение для подписи PDF-файлов с видимым штампом электронной подписи через CryptoPro CSP на Linux.

## Возможности

- **Встроенная PDF-подпись** — CAdES-BES подпись через PKCS#11 (pyHanko)
- **Откреплённая `.sig` подпись** — через csptest CLI
- **Видимый штамп** на всех страницах PDF (ГОСТ Р 7.0.97-2025)
- **3 профиля штампа**: минимальный (70×25 мм), стандартный (90×35 мм), подробный (120×45 мм)
- **Проверка подписи** — `.sig` файлы и встроенные подписи в PDF
- **Диагностика CryptoPro** — проверка certmgr, csptest, сертификатов
- **Редактор штампа** — настройка шаблона, позиции, размера, полей
- **Настройки** — сохранение профиля, экспорт/импорт JSON
- **Дружественные ошибки** — понятные описания вместо сырых исключений
- **Логирование** — запись действий с санитизацией секретов
- **Пакетное подписание** — несколько PDF за один запуск
- **Автоматический интерфейс** — русский/английский по языку системы

## Требования

- Linux x86_64 с графическим окружением
- Python 3.9+
- CryptoPro CSP (certmgr, csptest)
- Сертификат с закрытым ключом в хранилище

## Установка

```bash
pip install -e .
```

Запуск:
```bash
pdfsigner
```

## Сборка RPM

```bash
pip install wheel
python -m build
# или
rpmbuild -bb pdfsigner.spec
```

## Сборка DEB

```bash
pip install wheel
python -m build
# или
dpkg-deb --build dist/pdfsigner_1.0.0_amd64/
```

## Тесты

```bash
pip install pytest
pytest tests/ -v
```

## Лицензия

AGPL-3.0-or-later

---

# PDF Signer Linux

Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP.

## Features

- **Embedded PDF signature** — CAdES-BES via PKCS#11 (pyHanko)
- **Detached `.sig` signature** — via csptest CLI
- **Visible stamp** on all PDF pages (GOST R 7.0.97-2025)
- **3 stamp profiles**: minimal (70×25 mm), standard (90×35 mm), detailed (120×45 mm)
- **Signature verification** — `.sig` files and embedded PDF signatures
- **CryptoPro diagnostics** — check certmgr, csptest, certificates
- **Stamp editor** — configure template, position, size, fields
- **Settings persistence** — stamp profile saved, JSON export/import
- **Friendly errors** — human-readable error descriptions
- **Logging** — timestamped file logging with secret sanitization
- **Batch signing** — multiple PDFs in one run
- **Bilingual UI** — Russian/English from system language

## Requirements

- Linux x86_64 desktop environment
- Python 3.9+
- CryptoPro CSP (certmgr, csptest)
- Certificate with accessible private key

## Install

```bash
pip install -e .
```

Run:
```bash
pdfsigner
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```

## License

AGPL-3.0-or-later
