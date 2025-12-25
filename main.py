import os
import base64
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot
from aiogram.types import BufferedInputFile

# 1. SOZLAMALAR
# Renderda "Environment Variables" bo'limiga BOT_TOKEN qo'shiladi
TOKEN = os.getenv("BOT_TOKEN")

# Agar token bo'lmasa xato bermasligi uchun tekshiruv (lokal test uchun)
if not TOKEN:
    print("DIQQAT: BOT_TOKEN topilmadi! Render Environment Variables tekshiring.")

app = FastAPI()
bot = Bot(token=TOKEN) if TOKEN else None

# 2. CORS (Xavfsizlik) - Sayt serverga bog'lanishi uchun ruxsat
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hamma saytlarga ruxsat berish
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. MA'LUMOT MODELI (HTML dan keladigan format)
class FileRequest(BaseModel):
    telegram_id: int
    file_data: str  # Base64 formatidagi fayl kodi
    file__name__: str
    file_type: str
    price: int = 0

# 4. ASOSIY ENDPOINT (Sayt shu yerga murojaat qiladi)
@app.post("/webhook/download-file")
async def receive_file(request: FileRequest):
    if not bot:
        raise HTTPException(status_code=500, detail="Bot tokeni topilmadi serverda.")

    try:
        print(f"?? Fayl qabul qilindi: {request.file__name__} ({request.telegram_id})")

        # Base64 kodni tozalash (data:application/pdf;base64, qismini olib tashlash)
        if "," in request.file_data:
            header, encoded = request.file_data.split(",", 1)
        else:
            encoded = request.file_data

        # Kodni faylga aylantirish
        file_bytes = base64.b64decode(encoded)

        # Telegram uchun fayl obyektini yasash
        input_file = BufferedInputFile(file_bytes, filename=request.file__name__)

        # Foydalanuvchiga yuborish
        await bot.send_document(
            chat_id=request.telegram_id,
            document=input_file,
            caption=f"? <b>{request.file__name__}</b> tayyor!\n\n?? Xizmat ko'rsatildi.",
            parse_mode="HTML"
        )

        # Saytga muvaffaqiyatli javob qaytarish
        return {
            "status": "success", 
            "message": "Yuborildi",
            "new_balance": 50000 # Bu yerda keyinchalik haqiqiy balans logikasini ulashingiz mumkin
        }

    except Exception as e:
        print(f"? Xatolik: {e}")
        # Saytga xatolik haqida xabar qaytarish
        raise HTTPException(status_code=500, detail=str(e))

# 5. Ishga tushirish (Render o'zi shuni chaqiradi)
if name == "main":
    uvicorn.run(app, host="0.0.0.0", port=10000)