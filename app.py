import os
import streamlit as st
from google import genai
import datetime

# ==============================================================================
# 🔑 API 키 보안 설정 (배포 시 키 유출 및 차단 방지)
# ==============================================================================
if "GEMINI_API_KEY" in st.secrets:
    YOUR_GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
else:YOUR_GEMINI_API_KEY = "AQ.Ab8RN6IDbt7I6wc5ZsIGTmqd53u2SpiHlytDmXrXsR49eXhl8w"

# 1. 페이지 설정
st.set_page_config(
    page_title="2026 다관(茶館) : 소상공인 1:1 맞춤 AI 처방전",
    page_icon="🍵",
    layout="wide"
)

# 2. GenAI 클라이언트 생성
def get_client(key):
    if not key or "여기에" in key or len(key.strip()) < 10:
        return None
    try:
        return genai.Client(api_key=key.strip())
    except Exception:
        return None

client = get_client(YOUR_GEMINI_API_KEY)
ai_available = client is not None

# 3. AI 호출 함수 (최신 gemini-3.8-flash 우선 적용 및 오류 완벽 차단)
def call_gemini_ai(prompt_text):
    if not client:
        return None
    
    # 구글 서버 권장 최신 모델(gemini-3.8-flash) 우선 순위 후보군
    candidate_models = [
        "gemini-3.8-flash",
        "models/gemini-3.8-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash"
    ]
    
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text
            )
            if response and hasattr(response, 'text') and response.text:
                return response.text
        except Exception:
            continue
            
    # 통신 실패 시에도 날것의 빨간 에러 메시지를 화면에 노출하지 않음
    return None

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "saved_library" not in st.session_state:
    st.session_state.saved_library = []
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "initial_report" not in st.session_state:
    st.session_state.initial_report = ""

# 커스텀 스타일
st.markdown("""
<style>
    .title-text { font-size: 2.0rem; font-weight: 800; color: #1E3A8A; }
    .empathy-card { background-color: #EFF6FF; padding: 18px; border-radius: 12px; border: 1px solid #BFDBFE; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# 4. 사이드바 : 지난 상담 기록
with st.sidebar:
    st.header("📜 지난 상담 기록")
    if st.session_state.saved_library:
        for item in reversed(st.session_state.saved_library):
            with st.expander(f"📌 {item['date']} ({item['type']})"):
                st.write(f"**고민 내용**: {item['story']}")
    else:
        st.info("저장된 상담 기록이 없습니다.")
        
    st.markdown("---")
    if st.button("🧹 대화 내용 초기화"):
        st.session_state.chat_history = []
        st.session_state.report_generated = False
        st.session_state.initial_report = ""
        st.rerun()

# 5. 메인 화면
st.markdown('<p class="title-text">🍵 사장님 시름 털어내는 2026 다관(茶館) 처방전</p>', unsafe_allow_html=True)
st.markdown("전 세계 기업 위기 극복 사례와 사회·경영학 프레임워크를 기반으로 AI가 맞춤 처방을 작성합니다.")
st.markdown("---")

col_in, col_out = st.columns([1, 2.2])

with col_in:
    st.subheader("🗣️ 사장님의 속마음 터놓기")
    
    biz_type = st.selectbox("매장 업종", ["식음료/카페·음식점", "도소매/쇼핑몰", "뷰티/서비스업", "기타 자영업"])
    user_story = st.text_area(
        "어떤 점이 가장 힘드신가요?",
        placeholder="예: 임대료랑 재료비는 오르는데 손님은 줄어 고정비 내기가 벅찹니다.",
        height=180
    )
    
    btn_analyze = st.button("🔍 맞춤 처방전 및 1:1 대화 시작", use_container_width=True, type="primary")

SYSTEM_INSTRUCTION = """
당신은 경영학(PEST, Pivoting), 사회학(아노미 이론), 희곡 '다관(茶館)'의 지혜를 융합한 전문 AI 컨설턴트입니다.
소상공인의 고민을 듣고 글로벌 기업 사례(스타벅스, 닌텐도 등)와 현실적인 고정비 절감 수칙을 바탕으로 다채롭고 정중하게 답변하세요.
"""

with col_out:
    if btn_analyze and user_story:
        if not ai_available:
            st.warning("⚠️ 12번째 줄 `YOUR_GEMINI_API_KEY`에 올바른 구글 API 키를 입력해주세요.")
        else:
            with st.spinner("AI가 진단서를 작성 중입니다..."):
                prompt = f"""
                {SYSTEM_INSTRUCTION}
                
                [상담 내용]
                업종: {biz_type}
                고민 내용: {user_story}
                
                위 고민을 가진 사장님을 위해 다음 구조로 직관적인 진단 리포트를 작성해주세요:
                1. [💡 고정비 절감 및 공간 개량(Pivoting) 실행 지침] (전 세계 유사 위기 극복 사례 포함)
                2. [🗣️ 단골을 지키는 가치 전달 소통법]
                3. [🔍 위기의 사회학적 원인(아노미) 및 현실 지원책]
                
                ※ 세부 이론 설명이나 소설 다관과의 학술적 비교는 맨 아래 '자세히 보기' 세션으로 구분해 주세요.
                """
                ai_result = call_gemini_ai(prompt)
                
                if ai_result:
                    st.session_state.report_generated = True
                    st.session_state.initial_report = ai_result
                    
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.saved_library.append({
                        "date": now_str,
                        "type": biz_type,
                        "story": user_story[:20] + "..."
                    })
                    
                    st.session_state.chat_history = [{
                        "role": "assistant",
                        "content": f"안녕하세요 사장님! '{biz_type}' 고민에 대해 AI 맞춤 진단이 완료되었습니다. 위 리포트를 읽어보시고, 세부적인 질문이나 추가 고민은 아래 대화창에 편하게 물어보세요!"
                    }]
                else:
                    st.session_state.report_generated = False
                    st.error("현재 서버 통장 및 키 권한 확인이 필요합니다.")

    # 정상 결과가 존재할 때만 처방전 및 상담창 표시
    if st.session_state.report_generated and st.session_state.initial_report:
        st.subheader("📋 AI 맞춤 진단 처방전")
        st.markdown(st.session_state.initial_report)
        
        st.markdown("""
        <div class="empathy-card">
            <h4>❤️ 사장님, 오늘 하루도 정말 고생 많으셨습니다.</h4>
            <p>혼자 고민하지 마시고 아래 대화창에 어떤 작은 질문이라도 편하게 남겨주세요. AI가 끝까지 함께 해결책을 찾아드립니다.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("💬 1:1 무제한 AI 딥러닝 꼬리물기 상담")
        
        for msg in st.session_state.chat_history:
            if msg["role"] == "assistant":
                st.chat_message("assistant", avatar="🍵").write(msg["content"])
            else:
                st.chat_message("user", avatar="👤").write(msg["content"])
                
        if user_query := st.chat_input("추가로 궁금한 점을 물어보세요"):
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            st.chat_message("user", avatar="👤").write(user_query)
            
            if ai_available:
                with st.spinner("AI가 답변을 작성 중입니다..."):
                    chat_context = f"{SYSTEM_INSTRUCTION}\n[초기 고민]: {user_story}\n"
                    for h in st.session_state.chat_history[-6:]:
                        chat_context += f"{h['role']}: {h['content']}\n"
                    
                    ai_reply = call_gemini_ai(chat_context)
                    if not ai_reply:
                        ai_reply = "답변 생성 중 일시적 통신 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
            else:
                ai_reply = "API 키 설정 오류로 대화를 진행할 수 없습니다."

            st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})
            st.rerun()

    elif not btn_analyze:
        st.info("👈 좌측 상자에 고민을 입력하고 [맞춤 처방전 및 1:1 대화 시작] 버튼을 눌러주세요.")