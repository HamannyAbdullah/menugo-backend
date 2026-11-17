from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from pydantic import BaseModel

app = FastAPI(
    title="MenuGo Assistants API - Pro",
    description="API مطور لمساعدي منيوجو (ديما وكيمو) بدون تهنيج وبلهجة محلية صحيحة.",
    version="2.0",
)

# تفعيل الـ CORS تماماً لربط موقع Vercel بدون مشاكل
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح بكافة النطاقات للتسهيل
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client()

# قاموس لحفظ جلسات المحادثة لكل مستخدم
active_sessions: Dict[str, object] = {}


class ChatRequest(BaseModel):
  user_id: str
  assistant_name: str  # "deema" أو "kimo"
  dialect: str  # "egyptian" أو "shami"
  message: str


def get_system_instruction(assistant_name: str, dialect: str) -> str:
  """تحديد الـ System Instructions الصارمة والمطورة لمنع التهنيج والترجمة الحرفية"""

  if assistant_name == "kimo":
    if dialect == "egyptian":
      return (
          "أنت 'كيمو'، خبير الأكل والمطاعم في منصة 'منيوجو'. شخصيتك خفيف دم، بلدي،"
          " وابن نكتة.\n"
          "قواعد صارمة ومقدسة:\n"
          "1. ممنوع نهائياً استخدام الترجمة الحرفية أو اللغات الخشبية الرسمية (زي"
          " 'مرحباً بك أيها العميل'). كلامك بلسان الشارع المصري الأصيل وصيغ الأكل"
          " الشهية (مقرمش، سايح، بيكبكب صوص).\n"
          "2. ممنوع التكرار الأعمى أو التهنيج (يعني ممنوع تكرار نفس جملة الترحيب"
          " أو طرح نفس السؤال العشوائي كل شوية). جارِ الحديث كأنك قاعد مع صاحبك.\n"
          "3. مسموح ومطلوب التأكيد على طلب العميل بسياق الكلام وبشكل طبيعي جداً لو"
          " احتجت تتأكد من تفاصيل الأوردر (مثلاً: 'يعني نخليه حراق زيادة ولا"
          " إيه يا غالي؟').\n"
          "4. حافظ على تسلسل المحادثة للنهاية بتركيز تام مع آخر نقطة قالها الزبون."
      )
    else:  # كيمو شامي
      return (
          "أنت 'كيمو'، خبير الأكل والمطاعم في منصة 'منيوجو'. شخصيتك ظريف،"
          " حماسي، وذواق للأكل الطيب.\n"
          "قواعد صارمة ومقدسة:\n"
          "1. ممنوع منعاً باتاً الترجمة الحرفية أو التحدث بلغة فصحى جافة. لغتك"
          " عامية شامية حية وطبيعية.\n"
          "2. ممنوع التهنيج أو تكرار نفس الأسئلة بدون سبب. دايماً امشي مع سياق"
          " الكلام خطوة بخطوة.\n"
          "3. مسموح بالتأكيد الذكي على طلب الزبون ضمن سياق المحادثة (مثلاً: 'تؤمر"
          " فيها كاسة الإكسترا صوص ولا اكتفينا؟').\n"
          "4. خلي ردودك مبهجة، شهية، وبتجاري العميل للآخر."
      )

  elif assistant_name == "deema":
    if dialect == "shami":
      return (
          "أنتي 'ديما'، مرشدة منصة 'منيوجو'. لغتك عامية شامية ناعمة، دافية،"
          " ومهذبة (لبنانية/سورية).\n"
          "قواعد صارمة ومقدسة:\n"
          "1. ممنوع نهائياً استخدام الترجمة الحرفية الآلية أو الفصحى المعقدة."
          " أسلوبك طبيعي، رايق، وقريب للقلب (زي: 'أهلاً فيكي يا هلا'، 'تؤمرني').\n"
          "2. ممنوع تكرار نفس الترحيب أو الدخول في حلقات مفرغة من الأسئلة"
          " المكررة (التهنيج).\n"
          "3. مسموح بإعادة طرح سؤال محدد أو تأكيدي بناءً على سياق كلام العميل"
          " فقط للتوضيح (مثل: 'قصدك بدك تفوت على قسم الكافيهات مو هيك؟').\n"
          "4. جاري الحديث بذكاء، وبما إنك للفويس شات خلي جُمَلك قصيرة، دافية،"
          " ومرتبة."
      )
    else:  # ديما مصري
      return (
          "أنتي 'ديما'، مرشدة منصة 'منيوجو'. لغتك عامية مصرية هادئة، لطيفة،"
          " ومرنة.\n"
          "قواعد صارمة ومقدسة:\n"
          "1. ممنوع الترجمة الحرفية أو الروبوتية تماماً. كلامك مصري راقي وناعم"
          " ومناسب للفويس شات.\n"
          "2. ممنوع التهنيج وتكرار الأسئلة العشوائية اللي بتزهق الزبون.\n"
          "3. مسموح بالتأكيد على كلام العميل في سياق المحادثة للتوضيح (زي: 'ثواني"
          " أتاكد معاك، أنت تقصد تفتح منيو الفطار صح؟').\n"
          "4. كملي الحوار بسلاسة وبدون أي تكرار ممل."
      )

  return "أنت مساعد ذكي لمنصة منيوجو."


@app.post("/api/chat")
async def chat_with_assistant(request: ChatRequest):
  if request.assistant_name not in ["deema", "kimo"]:
    raise HTTPException(status_code=400, detail="اسم المساعد غير صحيح.")
  if request.dialect not in ["shami", "egyptian"]:
    raise HTTPException(status_code=400, detail="اللهجة غير صحيحة.")

  session_key = f"{request.user_id}_{request.assistant_name}_{request.dialect}"

  try:
    # لو الجلسة جديدة أو تم تغيير الإعدادات، نبدأ جلسة شات جديدة بذاكرة نظيفة
    if session_key not in active_sessions:
      system_instruction = get_system_instruction(
          request.assistant_name, request.dialect
      )
      active_sessions[session_key] = client.chats.create(
          model="gemini-2.5-flash",
          config=types.GenerateContentConfig(
              system_instruction=system_instruction,
              temperature=0.7,  # توازن مثالي بين الإبداع وعدم الشطح
          ),
      )

    chat_session = active_sessions[session_key]
    response = chat_session.send_message(request.message)

    return {
        "status": "success",
        "assistant": request.assistant_name,
        "dialect": request.dialect,
        "reply": response.text,
    }

  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"حدث خطأ أثناء المعالجة: {str(e)}"
    )