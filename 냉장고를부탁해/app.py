# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import pandas as pd
from recipes import RECIPES
import google.generativeai as genai
import json


# 페이지 기본 설정 및 디자인
st.set_page_config(
    page_title="Zero Waste AI 냉장고 대시보드",
    page_icon="🥑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich premium eco-friendly styling
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
<style>
    /* Global style override */
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    /* Title style */
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #558B2F;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card design */
    .recipe-card {
        background-color: #FFFFFF;
        border: 2px solid #E8F5E9;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(46, 125, 50, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(46, 125, 50, 0.1);
        border-color: #A5D6A7;
    }
    .recipe-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #1B5E20;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-style { background-color: #E8F5E9; color: #2E7D32; }
    .badge-time { background-color: #FFF3E0; color: #EF6C00; }
    .badge-diff { background-color: #E3F2FD; color: #1565C0; }
    .badge-cal { background-color: #F3E5F5; color: #6A1B9A; }
    
    /* Zero Waste Box */
    .zero-waste-box {
        background-color: #F1F8E9;
        border-left: 5px solid #7CB342;
        padding: 12px 16px;
        border-radius: 8px;
        margin-top: 15px;
        font-size: 0.9rem;
        color: #33691E;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- 세션 상태 초기화 -----------------
if 'survey_completed' not in st.session_state:
    st.session_state.survey_completed = False

if 'survey_answers' not in st.session_state:
    st.session_state.survey_answers = {
        'style': "선택 안 함",
        'avoidance': "선택 안 함",
        'importance': "선택 안 함",
        'spicy': "선택 안 함",
        'main_category': "선택 안 함",
        'concept': "선택 안 함",
        'method': "선택 안 함",
        'dessert': "선택 안 함"
    }

if 'ingredients' not in st.session_state:
    # 기본 테스트 식재료 셋 (비워달라는 요청 반영)
    st.session_state.ingredients = []

if 'rescued_count' not in st.session_state:
    st.session_state.rescued_count = 0

# 계산식 기반 에코 메트릭값 계산
saved_budget = st.session_state.rescued_count * 3000
reduced_co2 = st.session_state.rescued_count * 1.5

# ----------------- 기능 A: 음식 취향 분석 설문 (최초 진입) -----------------
if not st.session_state.survey_completed:
    st.markdown('<div class="main-title">🌿 Zero Waste 음식 취향 테스트 🥑</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">나만의 식습관과 선호를 파악하여 최적의 친환경 레시피를 추천해 드립니다!</div>', unsafe_allow_html=True)
    
    # 상단 프로그레스 바 영역 (하단에서 실시간 계산 후 채움)
    progress_container = st.container()
    
    st.write("---")
    
    # 2열 설문지 배치
    col1, col2 = st.columns(2)
    
    with col1:
        q_style = st.selectbox(
            "1. 평소 선호하는 요리 스타일은?",
            ["선택 안 함", "한식", "중식", "일식", "양식", "퓨전"],
            index=["선택 안 함", "한식", "중식", "일식", "양식", "퓨전"].index(st.session_state.survey_answers['style'])
        )
        q_avoidance = st.selectbox(
            "2. 기피하거나 알레르기가 있는 식재료가 있나요?",
            ["선택 안 함", "없음", "견과류", "갑각류", "유제품", "비건 선호"],
            index=["선택 안 함", "없음", "견과류", "갑각류", "유제품", "비건 선호"].index(st.session_state.survey_answers['avoidance'])
        )
        q_importance = st.selectbox(
            "3. 요리할 때 가장 중요하게 생각하는 가치는?",
            ["선택 안 함", "조리 시간(초간단)", "영양 밸런스", "비주얼", "맛의 깊이"],
            index=["선택 안 함", "조리 시간(초간단)", "영양 밸런스", "비주얼", "맛의 깊이"].index(st.session_state.survey_answers['importance'])
        )
        q_spicy = st.selectbox(
            "4. 평소 즐겨 드시는 매운맛의 강도는?",
            ["선택 안 함", "백김치 수준", "신라면 수준", "불닭 수준"],
            index=["선택 안 함", "백김치 수준", "신라면 수준", "불닭 수준"].index(st.session_state.survey_answers['spicy'])
        )

    with col2:
        q_main_category = st.selectbox(
            "5. 선호하는 메인 식재료 부류는?",
            ["선택 안 함", "육류 중심", "해산물 중심", "채소·두부 중심", "탄수화물류 면·밥"],
            index=["선택 안 함", "육류 중심", "해산물 중심", "채소·두부 중심", "탄수화물류 면·밥"].index(st.session_state.survey_answers['main_category'])
        )
        q_concept = st.selectbox(
            "6. 오늘 드시고 싶은 요리 컨셉은?",
            ["선택 안 함", "홈파티 정취 요리", "건강한 다이어트식", "든든한 보양식"],
            index=["선택 안 함", "홈파티 정취 요리", "건강한 다이어트식", "든든한 보양식"].index(st.session_state.survey_answers['concept'])
        )
        q_method = st.selectbox(
            "7. 가장 다루기 편하거나 선호하는 조리법은?",
            ["선택 안 함", "국물·탕·찌개", "볶음·구이", "샐러드·무침", "에어프라이어·오븐"],
            index=["선택 안 함", "국물·탕·찌개", "볶음·구이", "샐러드·무침", "에어프라이어·오븐"].index(st.session_state.survey_answers['method'])
        )
        q_dessert = st.selectbox(
            "8. 식사 후 디저트 배는 따로 있으신가요?",
            ["선택 안 함", "네! 상큼한 디저트가 필요해요", "아니요, 깔끔한 마무리로 충분해요"],
            index=["선택 안 함", "네! 상큼한 디저트가 필요해요", "아니요, 깔끔한 마무리로 충분해요"].index(st.session_state.survey_answers['dessert'])
        )
        
    # 변경 사항 즉시 반영하기 위해 세션에 임시 저장
    st.session_state.survey_answers = {
        'style': q_style,
        'avoidance': q_avoidance,
        'importance': q_importance,
        'spicy': q_spicy,
        'main_category': q_main_category,
        'concept': q_concept,
        'method': q_method,
        'dessert': q_dessert
    }
    
    # 실시간 화면 갱신 시 컨테이너에 진행률 그리기
    answered_count = sum(1 for v in st.session_state.survey_answers.values() if v != "선택 안 함")
    total_questions = len(st.session_state.survey_answers)
    progress_ratio = answered_count / total_questions
    
    with progress_container:
        st.progress(progress_ratio)
        st.caption(f"**진행률:** {answered_count} / {total_questions} 문항 완료 ({(progress_ratio*100):.0f}%)")

    st.write("---")
    
    # 버튼 비활성화 여부 제어
    all_answered = all(v != "선택 안 함" for v in st.session_state.survey_answers.values())
    
    if all_answered:
        if st.button("🌱 취향 분석 완료 후 대시보드 진입", use_container_width=True, type="primary"):
            st.session_state.survey_completed = True
            st.success("분석이 완료되었습니다! 대시보드로 이동합니다.")
            st.rerun()
    else:
        st.button("🚫 모든 질문에 답변해 주세요 (대시보드 잠김)", use_container_width=True, disabled=True)

# ----------------- 메인 대시보드 화면 (설문 완료 후) -----------------
else:
    # 대시보드 타이틀
    st.markdown('<div class="main-title">🌿 Zero Waste AI Refrigerator 🍳</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">식재료 유통기한을 지키고 탄소 발자국을 줄이는 친환경 스마트 냉장고 관리자</div>', unsafe_allow_html=True)

    # ----------------- 기능 B: 사이드바 (식재료 입력 및 관리) -----------------
    st.sidebar.markdown("### 🛒 냉장고 식재료 추가")
    
    input_name = st.sidebar.text_input("식재료명 (예: 두부, 대파, 양파)", placeholder="이름 입력")
    input_expiry = st.sidebar.date_input("유통기한 선택", datetime.date.today())
    input_qty = st.sidebar.number_input("수량 설정", min_value=1, value=1, step=1)
    
    if st.sidebar.button("➕ 냉장고에 넣기", use_container_width=True):
        if input_name.strip() == "":
            st.sidebar.error("식재료 이름을 입력해 주세요!")
        else:
            # 중복 검사 또는 신규 추가
            new_item = {"name": input_name.strip(), "expiry_date": input_expiry, "quantity": int(input_qty)}
            st.session_state.ingredients.append(new_item)
            st.sidebar.success(f"'{input_name}' {input_qty}개가 냉장고에 보관되었습니다.")
            st.rerun()
            
    st.sidebar.write("---")
    
    # 나의 취향 프로필 표시
    st.sidebar.markdown("### 👤 나의 에코 쿠킹 프로필")
    answers = st.session_state.survey_answers
    st.sidebar.markdown(f"""
    <div style="background-color: #F1F8E9; padding: 14px; border-radius: 12px; border: 1px solid #C8E6C9; margin-bottom: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.03);">
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🍳 스타일:</b> {answers.get('style')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🥩 메인 재료:</b> {answers.get('main_category')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🔥 맵기:</b> {answers.get('spicy')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🍳 조리법:</b> {answers.get('method')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>💡 중요도:</b> {answers.get('importance')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🎯 컨셉:</b> {answers.get('concept')}</p>
        <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #2E7D32;"><b>🍰 디저트:</b> {answers.get('dessert', '').split(',')[0][:15] + '...' if len(answers.get('dessert', '')) > 15 else answers.get('dessert')}</p>
        <p style="margin: 0; font-size: 0.88rem; color: #C62828;"><b>🚫 기피/알러지:</b> <b>{answers.get('avoidance')}</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    # 취향 재설정 버튼
    if st.sidebar.button("🔄 취향 분석 다시 하기", use_container_width=True):
        st.session_state.survey_completed = False
        st.session_state.survey_answers = {k: "선택 안 함" for k in st.session_state.survey_answers.keys()}
        st.rerun()
        
    st.sidebar.write("---")
    st.sidebar.markdown("### 🔑 API 설정")
    
    # 1순위: st.secrets, 2순위: 환경 변수, 3순위: 사용자 직접 입력
    import os
    env_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            env_key = st.secrets["GEMINI_API_KEY"]
    except:
        pass
        
    if not env_key:
        env_key = os.environ.get("GEMINI_API_KEY", "")
        
    api_key_input = st.sidebar.text_input(
        "Gemini API Key",
        value=st.session_state.get("api_key", env_key),
        type="password",
        placeholder="API 키 입력 (AI 추천 기능 활성화)"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input
        genai.configure(api_key=api_key_input)
    else:
        st.session_state.api_key = ""
        
    st.sidebar.write("---")
    st.sidebar.caption("🌍 SDGs 12 - 책임감 있는 소비와 생산 패턴을 위해 음식물 쓰레기를 최소화합시다.")

    # ----------------- 기능 C: 메인 대시보드 (상단 현황판) -----------------
    col_dash_left, col_dash_right = st.columns([2, 1])

    with col_dash_left:
        st.markdown("### 🧊 나의 냉장고 인벤토리")
        if not st.session_state.ingredients:
            st.info("냉장고가 비어 있습니다. 사이드바에서 식재료를 추가해 주세요!")
        else:
            # 재료 목록 표 및 삭제 액션
            df_ingredients = pd.DataFrame(st.session_state.ingredients)
            
            # 유통기한 기준으로 남은 일수 계산
            today = datetime.date.today()
            df_ingredients['남은 기간'] = df_ingredients['expiry_date'].apply(lambda x: (x - today).days)
            
            # 테이블 가독성 처리
            def format_days(days):
                if days < 0:
                    return f"❌ 유통기한 만료 ({-days}일 경과)"
                elif days == 0:
                    return "🚨 오늘까지!"
                elif days <= 3:
                    return f"⚠️ 임박 ({days}일 남음)"
                else:
                    return f"✅ 안전 ({days}일 남음)"
            
            df_ingredients['상태'] = df_ingredients['남은 기간'].apply(format_days)
            
            # 정렬 (유통기한 임박한 것이 위로 오게)
            df_ingredients = df_ingredients.sort_values(by="남은 기간")
            
            # 표시 테이블 구성
            display_df = df_ingredients[['name', 'quantity', 'expiry_date', '상태']].copy()
            display_df.columns = ['식재료명', '수량', '유통기한', '상태 정보']
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # 개별 삭제(소비) 인터페이스
            st.write("**식재료 직접 관리 (폐기 또는 수동 사용):**")
            del_cols = st.columns([3, 1])
            with del_cols[0]:
                to_delete = st.selectbox("꺼낼 재료 선택", [item['name'] for item in st.session_state.ingredients], key="delete_select")
            with del_cols[1]:
                if st.button("🗑️ 냉장고에서 꺼내기", use_container_width=True):
                    for idx, item in enumerate(st.session_state.ingredients):
                        if item['name'] == to_delete:
                            st.session_state.ingredients.pop(idx)
                            st.success(f"'{to_delete}'를 냉장고에서 꺼냈습니다.")
                            st.rerun()

    with col_dash_right:
        st.markdown("### 🌎 Zero Waste 에코 스코어")
        # 에코 메트릭 출력
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("🥬 구출한 식재료", f"{st.session_state.rescued_count} 개")
        with m_col2:
            st.metric("💰 절약한 비용", f"{saved_budget:,} 원")
            
        st.metric("🌱 온실가스 저감량 ($CO_2$)", f"{reduced_co2:.1f} kg")
        st.caption("※ 탄소 저감량은 식재료 폐기 억제 시 발생하는 평균적 절감량을 근거로 산출되었습니다.")

    # 유통기한 임박 알림 경고판
    st.write("---")
    st.markdown("### 🚨 유통기한 알림판")
    
    today = datetime.date.today()
    critical_items = []
    expired_items = []
    
    for item in st.session_state.ingredients:
        days_left = (item['expiry_date'] - today).days
        if days_left < 0:
            expired_items.append(f"**{item['name']}** ({-days_left}일 경과함)")
        elif 0 <= days_left <= 3:
            critical_items.append(f"**{item['name']}** (유통기한이 {days_left}일 남음)")
            
    if expired_items:
        st.error(f"❌ **이미 유통기한이 지난 식재료가 있습니다!** 어서 소비하시거나 폐기해 주세요: {', '.join(expired_items)}")
    
    if critical_items:
        st.warning(f"⚠️ **유통기한 임박 알림 (3일 이내):** 아래 재료를 최우선으로 요리에 사용해 주세요! \n\n {', '.join(critical_items)}")
    
    if not expired_items and not critical_items:
        st.success("✅ 모든 보관 식재료의 유통기한이 넉넉하게 남아 있습니다. 참 잘하셨어요!")

    # ----------------- 기능 D: AI 맞춤형 레시피 추천 (하단) -----------------
    st.write("---")
    st.markdown("### 🤖 AI 맞춤 제로 웨이스트 레시피 추천")
    st.write("냉장고 속 재료들 중 오늘 요리에 사용할 재료들을 선택해 주시면, 취향과 조합하여 최적의 환경 친화적 메뉴를 골라 드립니다.")

    if not st.session_state.ingredients:
        st.info("냉장고에 식재료가 있어야 레시피 추천을 받을 수 있습니다.")
    else:
        # 다중 선택박스
        avail_names = list(set([item['name'] for item in st.session_state.ingredients]))
        # 기본값으로 임박 식재료 자동 선택되도록 유도
        default_selections = []
        for item in st.session_state.ingredients:
            days_left = (item['expiry_date'] - today).days
            if days_left <= 3 and item['name'] not in default_selections:
                default_selections.append(item['name'])
                
        selected_materials = st.multiselect(
            "🍳 사용할 식재료 다중 선택 (임박한 재료가 자동 추천 세팅됩니다)",
            options=avail_names,
            default=default_selections
        )
        
        if st.button("💡 AI 실시간 레시피 추천 받기", type="primary", use_container_width=True):
            if not selected_materials:
                st.warning("레시피를 조회할 식재료를 최소 1개 이상 선택해 주세요!")
            elif not st.session_state.get("api_key", ""):
                st.error("👈 왼쪽 사이드바(Sidebar) 하단에서 Gemini API Key를 먼저 입력해 주세요!")
            else:
                st.session_state.selected_materials = selected_materials
                user_pref = st.session_state.survey_answers
                
                # Gemini 실시간 레시피 생성 진행
                with st.spinner("Gemini AI가 냉장고 속 재료와 취향을 분석하여 환경 친화적 레시피를 창작하고 있습니다... 🧑‍🍳"):
                    prompt = f"""
                    You are a Zero Waste AI chef helping users cook to achieve SDGs Target 12 (Zero Waste).
                    Based on the following parameters, suggest exactly 3 eco-friendly recipes.
                    
                    Available Ingredients in Refrigerator: {', '.join(selected_materials)}
                    User Cooking Style preference: {user_pref.get('style')}
                    Avoided Ingredients/Allergies: {user_pref.get('avoidance')}
                    Cooking Importance: {user_pref.get('importance')}
                    Preferred Spiciness: {user_pref.get('spicy')}
                    Preferred Category: {user_pref.get('main_category')}
                    Concept: {user_pref.get('concept')}
                    Preferred Cooking Method: {user_pref.get('method')}
                    Dessert Preference: {user_pref.get('dessert')}
                    
                    Zero Waste Constraint: The recipes MUST utilize at least one of the available ingredients listed. Explain how this recipe prevents food waste.
                    Avoidance Constraint: DO NOT include any avoided ingredients in the recipe ingredients list.
                    
                    Output MUST be a valid JSON array of exactly 3 objects. Do not include markdown code block formatting (like ```json), just return raw JSON text.
                    Each object in the array must strictly have the following keys (do not add others):
                    - "name": Recipe name in Korean, with an English subtitle in parentheses, e.g. "두부 청경채 볶음 (Tofu Bok Choy Stir-fry)".
                    - "ingredients": A list of strings representing the key ingredients (e.g. ["두부", "청경채", "굴소스"]).
                    - "style": Cooking style in Korean (e.g. "한식", "중식").
                    - "difficulty": "쉬움", "보통", or "어려움".
                    - "cooking_time": Cooking time in minutes (integer).
                    - "calories": Calories in kcal (integer).
                    - "description": Description of the recipe in Korean.
                    - "zero_waste_tip": A short tip in Korean explaining why this recipe is eco-friendly or how to reduce waste (e.g., using vegetable scraps).
                    - "image_keyword": 1 or 2 English search terms to find a relevant image on Unsplash (e.g., "tofu stirfry", "mushroom soup"). Do not use spaces in a single keyword, separate multiple keywords with comma.
                    """
                    
                    try:
                        model = genai.GenerativeModel('gemini-3.5-flash')
                        response = model.generate_content(prompt)
                        text = response.text.strip()
                        
                        # Markdown 코드 블록 제거 및 순수 JSON 파싱
                        if text.startswith("```"):
                            lines = text.split("\n")
                            if lines[0].startswith("```"):
                                lines = lines[1:]
                            if lines[-1].startswith("```"):
                                lines = lines[:-1]
                            text = "\n".join(lines).strip()
                            
                        data = json.loads(text)
                        
                        top_recommendations = []
                        for idx, r in enumerate(data):
                            top_recommendations.append({
                                "recipe": r,
                                "score": 100 - idx,
                                "matched_ingredients": [m for m in selected_materials if m in r.get('ingredients', [])]
                            })
                        
                        st.session_state.recommendations = top_recommendations
                        st.success("Gemini가 완성도 높은 친환경 레시피를 실시간으로 설계했습니다! 🎉")
                    except Exception as e:
                        st.error(f"Gemini API 호출 및 레시피 생성 중 오류가 발생했습니다: {str(e)}")
                
        # 추천 레시피 결과 출력
        if 'recommendations' in st.session_state and st.session_state.recommendations:
            st.success("정교한 매칭 결과, 아래 레시피들을 추천해 드립니다! 🎉")
            
            # 카드 레이아웃 출력
            for idx, item in enumerate(st.session_state.recommendations):
                r = item['recipe']
                score = item['score']
                matched = item['matched_ingredients']
                
                # HTML Card 디자인 (안전하게 get 적용)
                badges_html = f"""
                <span class="badge badge-style">{r.get('style', '기타')}</span>
                <span class="badge badge-time">⏱️ {r.get('cooking_time', 15)}분</span>
                <span class="badge badge-diff">📊 난이도: {r.get('difficulty', '보통')}</span>
                <span class="badge badge-cal">🔥 {r.get('calories', 200)} kcal</span>
                """
                
                # 레시피별 정확히 일치하는 고화질 Unsplash 이미지 URL 매핑
                # 1. 기존 12종 리스트와 일치하면 검증된 사진 사용
                base_name = r.get('name', '').split(" (")[0]
                image_map = {
                    "두부 야채 볶음": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=300&q=80",
                    "매콤 소고기 볶음": "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=300&q=80",
                    "갈릭 크림 파스타": "https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=300&q=80",
                    "불닭 볶음 우동": "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=300&q=80",
                    "해물 토마토 스튜": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=300&q=80",
                    "견과류 멸치 볶음": "https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=300&q=80",
                    "초간단 계란 간장밥": "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=300&q=80",
                    "연어 샐러드": "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=300&q=80",
                    "버섯 전골": "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=300&q=80",
                    "꿔바로우식 버섯 탕수": "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=300&q=80",
                    "상큼 과일 요거트볼": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=300&q=80",
                    "상큼 민트 레몬에이드": "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=300&q=80"
                }
                
                if base_name in image_map:
                    image_url = image_map[base_name]
                else:
                    # 2. AI 추천 및 동적 생성 레시피를 위한 스마트 카테고리 매핑 (고화질 Unsplash 이미지 매칭)
                    recipe_name = r.get('name', '')
                    ingredients = r.get('ingredients', [])
                    desc = r.get('description', '')
                    method = r.get('method', '')
                    style = r.get('style', '')
                    
                    # 검색용 텍스트 병합
                    scan_text = f"{recipe_name} {' '.join(ingredients)} {desc} {method} {style}".lower()
                    
                    if any(x in scan_text for x in ["레몬에이드", "에이드", "음료", "주스", "tea", "drink", "lemonade"]):
                        image_url = "https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["요거트", "디저트", "과일", "yoghurt", "yogurt", "dessert", "fruit"]):
                        image_url = "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["파스타", "스파게티", "pasta", "spaghetti"]):
                        image_url = "https://images.unsplash.com/photo-1546549032-9571cd6b27df?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["우동", "라면", "면", "국수", "noodle", "udon", "ramen"]):
                        image_url = "https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["간장밥", "볶음밥", "비빔밥", "덮밥", "밥", "rice", "bibimbap"]):
                        image_url = "https://images.unsplash.com/photo-1512058564366-18510be2db19?auto=format&fit=crop&w=300&q=80"
                    elif "연어" in scan_text or "salmon" in scan_text:
                        image_url = "https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["새우", "오징어", "해물", "조개", "생선", "seafood", "shrimp", "squid", "fish"]):
                        image_url = "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["소고기", "쇠고기", "beef"]):
                        image_url = "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["돼지고기", "삼겹살", "제육", "pork"]):
                        image_url = "https://images.unsplash.com/photo-1602489114888-6625801334f5?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["닭고기", "치킨", "닭발", "chicken"]):
                        image_url = "https://images.unsplash.com/photo-1598515214211-89d3e73ae83b?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["전골", "찌개", "국", "탕", "스튜", "soup", "stew", "hotpot"]):
                        image_url = "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=300&q=80"
                    elif "두부" in scan_text or "tofu" in scan_text:
                        image_url = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=300&q=80"
                    elif "버섯" in scan_text or "mushroom" in scan_text:
                        image_url = "https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?auto=format&fit=crop&w=300&q=80"
                    elif any(x in scan_text for x in ["샐러드", "무침", "salad", "vegetable", "green"]):
                        image_url = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=300&q=80"
                    elif "계란" in scan_text or "달걀" in scan_text or "egg" in scan_text:
                        image_url = "https://images.unsplash.com/photo-1525351484163-7529414344d8?auto=format&fit=crop&w=300&q=80"
                    else:
                        # 3. 매핑 실패 시: Cleaned loremflickr fallback
                        kw = r.get('image_keyword', 'food').lower()
                        kw_cleaned = kw.replace(" ", ",").replace("-", ",").strip()
                        kw_list = [k for k in kw_cleaned.split(",") if k]
                        kw_list = kw_list[:2]  # 검색 신뢰도를 높이기 위해 태그는 최대 2개로 제한
                        if kw_list:
                            image_url = f"https://loremflickr.com/300/300/food,{','.join(kw_list)}/all?lock={idx+10}"
                        else:
                            image_url = "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=300&q=80"
                
                st.markdown(f"""
                <div class="recipe-card">
                    <div style="display:flex; gap: 20px; align-items: center; margin-bottom: 15px;">
                        <img src="{image_url}" style="width:120px; height:120px; border-radius:12px; object-fit:cover; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" alt="Recipe Image">
                        <div>
                            <div class="recipe-title" style="margin-bottom:8px;">🍳 {r['name']}</div>
                            <div>{badges_html}</div>
                        </div>
                    </div>
                    <p style="color: #424242; font-size: 0.95rem;">{r['description']}</p>
                    <p style="font-size:0.9rem; font-weight:600; color:#1B5E20; margin-bottom:5px;">필요 핵심 재료: {", ".join(r['ingredients'])}</p>
                    <div class="zero-waste-box">
                        <strong>🌿 Eco Zero Waste Tip:</strong> {r['zero_waste_tip']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 요리 완료 액션 버튼
                btn_cols = st.columns([4, 1])
                with btn_cols[1]:
                    if st.button(f"🍽️ 요리 완료 및 재료 구출!", key=f"cook_{idx}_{r['name']}"):
                        # 소진된 재료들을 냉장고 리스트에서 소진/제거 처리
                        rescued_list = []
                        new_ingredients = []
                        
                        # 레시피에 들어가는 재료 중 현재 냉장고에 있는 것들을 지우거나 개수 감소
                        # 여기서는 사용자가 선택해서 레시피 매칭에 사용된 재료 목록(matched)을 제거
                        for ing in st.session_state.ingredients:
                            if ing['name'] in matched:
                                rescued_list.append(ing['name'])
                            else:
                                new_ingredients.append(ing)
                                
                        st.session_state.ingredients = new_ingredients
                        # 메트릭 누적 증가 (냉장고에 추가된 재료가 없었더라도 레시피 완성 시 기본 보상 지급)
                        rescued_count_increment = len(rescued_list) if len(rescued_list) > 0 else len(r['ingredients'])
                        st.session_state.rescued_count += rescued_count_increment
                        
                        st.balloons()
                        st.success(f"성공적으로 요리를 마쳤습니다! 냉장고에서 [{', '.join(rescued_list)}] 재료 {rescued_count_increment}개를 무사히 구출하여 지구를 지켰습니다! 🌍")
                        
                        # 결과 추천 초기화
                        st.session_state.recommendations = []
                        st.rerun()
