# -*- coding: utf-8 -*-
import streamlit as st
import datetime
import pandas as pd
from recipes import RECIPES

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
    # 기본 테스트 식재료 셋
    st.session_state.ingredients = [
        {"name": "두부", "expiry_date": datetime.date.today() + datetime.timedelta(days=2), "quantity": 1},
        {"name": "대파", "expiry_date": datetime.date.today() + datetime.timedelta(days=5), "quantity": 2},
        {"name": "새우", "expiry_date": datetime.date.today() - datetime.timedelta(days=1), "quantity": 5},
        {"name": "소고기", "expiry_date": datetime.date.today() + datetime.timedelta(days=1), "quantity": 1}
    ]

if 'rescued_count' not in st.session_state:
    st.session_state.rescued_count = 0

# 계산식 기반 에코 메트릭값 계산
saved_budget = st.session_state.rescued_count * 3000
reduced_co2 = st.session_state.rescued_count * 1.5

# ----------------- 기능 A: 음식 취향 분석 설문 (최초 진입) -----------------
if not st.session_state.survey_completed:
    st.markdown('<div class="main-title">🌿 Zero Waste 음식 취향 테스트 🥑</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">나만의 식습관과 선호를 파악하여 최적의 친환경 레시피를 추천해 드립니다!</div>', unsafe_allow_html=True)
    
    # 상단 프로그레스 바
    # 설문 항목 중 '선택 안 함'이 아닌 비율 계산
    answered_count = sum(1 for v in st.session_state.survey_answers.values() if v != "선택 안 함")
    total_questions = len(st.session_state.survey_answers)
    progress_ratio = answered_count / total_questions
    
    st.progress(progress_ratio)
    st.caption(f"**진행률:** {answered_count} / {total_questions} 문항 완료 ({(progress_ratio*100):.0f}%)")
    
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
    
    # 실시간 화면 갱신 유도
    if st.button("답변 실시간 반영하기 🔄"):
        st.rerun()

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
    
    # 취향 재설정 버튼
    if st.sidebar.button("🔄 취향 분석 다시 하기", use_container_width=True):
        st.session_state.survey_completed = False
        st.session_state.survey_answers = {k: "선택 안 함" for k in st.session_state.survey_answers.keys()}
        st.rerun()
        
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
        
        if st.button("💡 레시피 추천 받기", type="primary", use_container_width=True):
            if not selected_materials:
                st.warning("레시피를 조회할 식재료를 최소 1개 이상 선택해 주세요!")
            else:
                st.session_state.selected_materials = selected_materials
                # 매칭 스코어링 시작
                user_pref = st.session_state.survey_answers
                scored_recipes = []
                
                for r in RECIPES:
                    # 1. 알레르기/기피 재료 필터링
                    avoid = user_pref['avoidance']
                    if avoid == "갑각류" and "새우" in r['ingredients']:
                        continue
                    if avoid == "견과류" and any(nut in r['ingredients'] for nut in ["아몬드", "호두", "견과류"]):
                        continue
                    if avoid == "유제품" and any(dairy in r['ingredients'] for dairy in ["우유", "치즈", "요거트"]):
                        continue
                    if avoid == "비건 선호" and "비건 선호" not in r['avoidance']:
                        continue
                        
                    # 2. 매칭 스코어링
                    score = 0
                    
                    # 주 식재료 매칭 점수 (선택한 재료가 들어가는 만큼 추가)
                    matched_in_recipe = [m for m in selected_materials if m in r['ingredients']]
                    if not matched_in_recipe:
                        # 선택 재료가 아예 없는 레시피는 점수를 깎거나 하단으로 제외
                        score -= 5
                    else:
                        score += len(matched_in_recipe) * 3  # 선택 재료 1개 매칭당 +3점
                        
                    # 선호 스타일
                    if r['style'] == user_pref['style']:
                        score += 2
                    
                    # 요리할 때 가장 중요하게 생각하는 것
                    if user_pref['importance'] == "조리 시간(초간단)" and r['cooking_time'] <= 10:
                        score += 3
                    elif user_pref['importance'] == "영양 밸런스" and r['importance'] == "영양 밸런스":
                        score += 2
                    elif user_pref['importance'] == "비주얼" and r['importance'] == "비주얼":
                        score += 2
                    elif user_pref['importance'] == "맛의 깊이" and r['importance'] == "맛의 깊이":
                        score += 2
                        
                    # 매운맛 수준
                    if r['spicy'] == user_pref['spicy']:
                        score += 2
                        
                    # 메인 재료 부류
                    if r['main_category'] == user_pref['main_category']:
                        score += 2
                        
                    # 오늘 요리 컨셉
                    if r['concept'] == user_pref['concept']:
                        score += 2
                        
                    # 선호 조리법
                    if r['method'] == user_pref['method']:
                        score += 1
                        
                    # 디저트 선호 조건
                    is_dessert_pref = "디저트가 필요해요" in user_pref['dessert']
                    is_recipe_dessert = r.get('is_dessert', False)
                    if is_dessert_pref == is_recipe_dessert:
                        score += 2
                        
                    scored_recipes.append({
                        "recipe": r,
                        "score": score,
                        "matched_ingredients": matched_in_recipe
                    })
                
                # 스코어 높은 순으로 정렬
                scored_recipes = sorted(scored_recipes, key=lambda x: x['score'], reverse=True)
                # 상위 3개 선별
                top_recommendations = scored_recipes[:3]
                
                st.session_state.recommendations = top_recommendations
                
        # 추천 레시피 결과 출력
        if 'recommendations' in st.session_state and st.session_state.recommendations:
            st.success("정교한 매칭 결과, 아래 레시피들을 추천해 드립니다! 🎉")
            
            # 카드 레이아웃 출력
            for idx, item in enumerate(st.session_state.recommendations):
                r = item['recipe']
                score = item['score']
                matched = item['matched_ingredients']
                
                # HTML Card 디자인
                badges_html = f"""
                <span class="badge badge-style">{r['style']}</span>
                <span class="badge badge-time">⏱️ {r['cooking_time']}분</span>
                <span class="badge badge-diff">📊 난이도: {r['difficulty']}</span>
                <span class="badge badge-cal">🔥 {r['calories']} kcal</span>
                """
                
                st.markdown(f"""
                <div class="recipe-card">
                    <div class="recipe-title">🍳 {r['name']}</div>
                    <div style="margin-bottom:12px;">{badges_html}</div>
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
                        # 메트릭 누적 증가
                        rescued_count_increment = len(rescued_list)
                        st.session_state.rescued_count += rescued_count_increment
                        
                        st.balloons()
                        st.success(f"성공적으로 요리를 마쳤습니다! 냉장고에서 [{', '.join(rescued_list)}] 재료 {rescued_count_increment}개를 무사히 구출하여 지구를 지켰습니다! 🌍")
                        
                        # 결과 추천 초기화
                        st.session_state.recommendations = []
                        st.rerun()
