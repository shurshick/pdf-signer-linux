# PDF Signer Linux

Настольное приложение для подписи PDF-файлов с видимым штампом электронной подписи через CryptoPro CSP на Linux.

Полный порт [PDF Signer Windows v0.8.0](https://github.com/shurshick/pdf-signer-windows) на Linux.

## Возможности

- **Встроенная PDF-подпись** — CAdES-BES подпись через PKCS#11 (pyHanko)
- **Откреплённая `.sig` подпись** — через csptest CLI
- **Видимый штамп** на всех страницах PDF
- **3 профиля штампа**: минимальный (70×25 мм), стандартный (90×35 мм), подробный (120×45 мм)
- **Умное размещение** штампа по текстовым блокам PDF
- **Ручное размещение** — X/Y координаты в мм
- **Логотип PNG/JPG** в штампе с масштабом и ограничением 1 МБ
- **Проверка подписи** — `.sig` файлы и встроенные подписи в PDF
- **Диагностика CryptoPro** — проверка certmgr, csptest, сертификатов
- **Экспорт/импорт настроек** — JSON
- **Дружественные ошибки** — понятные описания вместо сырых исключений
- **Логирование** — запись действий с санитизацией секретов
- **Пакетное подписание** — несколько PDF за один запуск
- **Автоматический интерфейс** — русский/английский по языку системы
- **Горячие клавиши** — Delete для удаления, Ctrl+A для выделения всех
- **Тултипы** для длинных путей файлов
- **Двойной клик** — открытие расположения файла

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
pip install wheel build
python -m build
# или
rpmbuild -bb packaging/rpm/pdfsigner.spec
```

## Сборка DEB

```bash
pip install wheel build
python -m build
# или
dpkg-deb --build packaging/deb/pdfsigner_1.0.0_amd64/
```

## Тесты

```bash
pip install pytest
pytest tests/ -v
```

## Лицензия

AGPL-3.0-or-later

---

Desktop PDF signing and visible stamp tool for Linux with CryptoPro CSP.

Full port of [PDF Signer Windows v0.8.0](https://github.com/shurshick/pdf-signer-windows) to Linux.

## Features

- **Embedded PDF signature** — CAdES-BES via PKCS#11 (pyHanko)
- **Detached `.sig` signature** — via csptest CLI
- **Visible stamp** on all PDF pages
- **3 stamp profiles**: minimal (70×25 mm), standard (90×35 mm), detailed (120×45 mm)
- **Smart stamp placement** based on PDF text blocks
- **Manual placement** — X/Y coordinates in mm
- **PNG/JPG logo** in stamp with scaling and 1 MB limit
- **Signature verification** — `.sig` files and embedded PDF signatures
- **CryptoPro diagnostics** — check certmgr, csptest, certificates
- **Settings export/import** — JSON
- **Friendly errors** — human-readable error descriptions
- **Logging** — timestamped file logging with secret sanitization
- **Batch signing** — multiple PDFs in one run
- **Bilingual UI** — Russian/English from system language
- **Keyboard shortcuts** — Delete to remove, Ctrl+A to select all
- **Tooltips** for long file paths
- **Double-click** to open file location

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
