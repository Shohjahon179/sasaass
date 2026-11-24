# Vagon Boshqaruvi — PostgreSQL ulash

## Loyiha tarkibi
- `app/`: mavjud Android Jetpack Compose ilovasi.
- `server/`: Flask REST API.
- `docker-compose.yml`: PostgreSQL 16 bazasi.

Android ilovasi serverdan `GET/PUT/DELETE /api/vagon_app/{users|records|messages}` orqali ma'lumot oladi. Ilova 4 soniyada bir marta sinxronlashni davom ettiradi; chat matnlari va vagon yozuvlari barcha telefonlarda umumiy bo'ladi.

## 1. Kompyuterda PostgreSQL ishga tushirish
Docker Desktop o'rnating va loyiha asosiy papkasida terminal oching:

```bash
docker compose up -d postgres
```

## 2. API serverni ishga tushirish
Python 3.10+ kerak:

```bash
cd server
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:DATABASE_URL="postgresql://vagon_user:vagon_pass_change_this@localhost:5432/vagon_db"
python app.py
```

Server tekshiruvi: `http://127.0.0.1:5000/health` — `{"ok":true,"database":"postgresql"}` qaytishi kerak.

## 3. Android ilovani ulash
Ilovada server manzili sozlamasiga quyidagilardan mosini yozing:
- Android Emulator: `http://10.0.2.2:5000`
- Xuddi shu Wi-Fi'dagi haqiqiy telefon: kompyuterning LAN IP manzili, masalan `http://192.168.1.20:5000` (misoldagi IP'ni o'zingiznikiga almashtiring).

Windows Firewall'da TCP 5000 portiga lokal tarmoq uchun ruxsat bering. Telefon va kompyuter bir Wi-Fi tarmog'ida bo'lsin.

## 4. Internet orqali boshqa joydan ulash
Kompyuter serveri ishlayotganida, bir Wi-Fi ichidagi telefonlar ishlay oladi. Boshqa internet/tarmoqdan ishlashi uchun API serverni doimiy hosting/VPS'ga joylang, PostgreSQL'ni private network ichida saqlang va HTTPS domenini o'rnating. APK ichiga `localhost` yoki `10.0.2.2` yozmang; hosting domenini kiriting.

## Muhim xavfsizlik eslatmasi
Bu paket sinov/prototip ulanishidir. API hozircha autentifikatsiya qilmaydi, mavjud ilova esa foydalanuvchi parolini ham sinxronlanadigan User obyektida saqlaydi. Uni ochiq internetga joylab, haqiqiy foydalanuvchi ma'lumotlari bilan ishlatmang. Ishlab chiqarishdan oldin server tomonida login/token, parolni Argon2/bcrypt bilan xeshlash, rollar bo'yicha ruxsat, HTTPS, zaxira nusxa va chat fayllarini serverga yuklash mexanizmini qo'shish shart. `localFilePath` telefondagi fayl yo'li bo'lgani uchun boshqa telefonda faylning o'zi ko'rinmaydi; hozir faqat chat matni/metadata sinxronlanadi.
