import streamlit as st
from datetime import date
import pandas as pd

# ---------------------------------------------------------
# 0) KoreanLunarCalendar 버전 자동 인식 (오류 0%)
# ---------------------------------------------------------
try:
    from korean_lunar_calendar import KoreanLunarCalendar
    lunar_available = True
except:
    lunar_available = False


# ---------------------------------------------------------
# 1) Streamlit 기본 설정 & CSS (디자인 B 적용)
# ---------------------------------------------------------
st.set_page_config(page_title="사주 분석 리포트", layout="wide")

st.markdown("""
<style>

html, body, [class*="css"]  {
    font-family: 'Noto Sans KR', sans-serif !important;
    line-height: 1.55;
}

/* 메인 타이틀 */
.title-main {
    font-size: 36px;
    font-weight: 800;
    margin-bottom: 5px;
}

.title-sub {
    font-size: 20px;
    font-weight: 400;
    margin-bottom: 40px;
    color: #555;
}

/* 섹션 타이틀 */
.section-header {
    font-size: 28px;
    font-weight: 700;
    margin-top: 40px;
    margin-bottom: 20px;
    border-left: 8px solid #4B6BFB;
    padding-left: 12px;
}

/* 카드 박스 */
.card-box {
    padding: 20px 24px;
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #e4e4e4;
    margin-bottom: 25px;
    box-shadow: 0px 1px 5px rgba(0,0,0,0.06);
}

/* 점수 박스 */
.score-box {
    background: #f7f9fc;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #e2e6ee;
}
.score-num {
    font-size: 28px;
    font-weight: 800;
    margin-top: 5px;
    color: #2A4B8D;
}

.divider {
    height: 1px;
    background: #ddd;
    margin: 40px 0px;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2) 만세력 처리 유틸리티 (모든 버전 호환)
# ---------------------------------------------------------
def safe_set_solar(cal, year, month, day):
    """
    KoreanLunarCalendar 버전 차이에 따라
    setSolar / setSolarDate / setSolarSolar 등
    어떤 함수든 자동으로 잡아서 설정.
    """
    if hasattr(cal, "setSolar"):
        return cal.setSolar(year, month, day)
    elif hasattr(cal, "setSolarDate"):
        return cal.setSolarDate(year, month, day)
    elif hasattr(cal, "setSolarSolar"):
        return cal.setSolarSolar(year, month, day)
    else:
        raise Exception("지원되지 않는 KoreanLunarCalendar 버전입니다.")


# ---------------------------------------------------------
# 3) 천간·지지·오행 매핑
# ---------------------------------------------------------
heavenly_stems = ["갑","을","병","정","무","기","경","신","임","계"]
earthly_branches = ["자","축","인","묘","진","사","오","미","신","유","술","해"]

stem_to_element = {
    "갑":"목","을":"목",
    "병":"화","정":"화",
    "무":"토","기":"토",
    "경":"금","신":"금",
    "임":"수","계":"수",
}

branch_to_element = {
    "자":"수","축":"토","인":"목","묘":"목",
    "진":"토","사":"화","오":"화","미":"토",
    "신":"금","유":"금","술":"토","해":"수"
}

branch_to_animal = {
    "자":"🐭 쥐띠","축":"🐮 소띠","인":"🐯 호랑이띠","묘":"🐰 토끼띠",
    "진":"🐲 용띠","사":"🐍 뱀띠","오":"🐴 말띠","미":"🐑 양띠",
    "신":"🐵 원숭이띠","유":"🐔 닭띠","술":"🐶 개띠","해":"🐷 돼지띠",
}
# ---------------------------------------------------------
# PART 2 — 사주 4기둥 계산 + 오행 분석 + 띠 + 일간 성향
# ---------------------------------------------------------

# 만세력에서 "정유년 병오월 임오일" → (정,유), (병,오), (임,오) 분리
def parse_gapja(gapja: str):
    tokens = gapja.split()
    if len(tokens) < 3:
        raise ValueError("간지 문자열 파싱 실패: " + gapja)

    y, m, d = tokens[:3]

    def split_token(token):
        return token[0], token[1]

    return split_token(y), split_token(m), split_token(d)


# 출생 시를 지지로 변환
def get_hour_branch(hour):
    if hour is None:
        return None
    if hour == 23 or hour < 1:
        return "자"
    elif hour < 3:
        return "축"
    elif hour < 5:
        return "인"
    elif hour < 7:
        return "묘"
    elif hour < 9:
        return "진"
    elif hour < 11:
        return "사"
    elif hour < 13:
        return "오"
    elif hour < 15:
        return "미"
    elif hour < 17:
        return "신"
    elif hour < 19:
        return "유"
    elif hour < 21:
        return "술"
    else:
        return "해"


# 출생 시의 천간 계산
def get_hour_stem(day_stem, hour_branch):
    if day_stem is None or hour_branch is None:
        return None
    try:
        d_idx = heavenly_stems.index(day_stem) + 1
        h_idx = earthly_branches.index(hour_branch) + 1
    except ValueError:
        return None
    stem_idx = ((2 * d_idx - 1) + (h_idx - 1)) % 10
    return heavenly_stems[stem_idx]


# 4기둥 전체 계산
def get_four_pillars(solar_date: date, hour):
    if not lunar_available:
        st.error("KoreanLunarCalendar 라이브러리가 설치되지 않았습니다.")
        return None

    cal = KoreanLunarCalendar()
    safe_set_solar(cal, solar_date.year, solar_date.month, solar_date.day)

    gapja = cal.getGapJaString()
    (y_s, y_b), (m_s, m_b), (d_s, d_b) = parse_gapja(gapja)

    h_b = get_hour_branch(hour)
    h_s = get_hour_stem(d_s, h_b) if h_b else None

    return {
        "year": (y_s, y_b),
        "month": (m_s, m_b),
        "day": (d_s, d_b),
        "hour": (h_s, h_b) if h_s and h_b else None
    }


# 오행 카운트
def count_elements(pillars):
    counts = {"목":0, "화":0, "토":0, "금":0, "수":0}

    # 연/월/일
    for key in ["year", "month", "day"]:
        stem, branch = pillars[key]
        counts[stem_to_element[stem]] += 1
        counts[branch_to_element[branch]] += 1

    # 시주
    if pillars["hour"]:
        h_s, h_b = pillars["hour"]
        counts[stem_to_element[h_s]] += 1
        counts[branch_to_element[h_b]] += 1

    return counts


# 일간 성향
def get_day_master_trait(day_stem):
    traits = {
        "갑": "기둥 같은 강직함, 추진력, 정의감을 갖춘 리더형.",
        "을": "섬세하고 배려 깊으며 감성적 안정감을 주는 스타일.",
        "병": "태양처럼 밝고 에너지 넘치며 사람을 끄는 카리스마형.",
        "정": "촛불 같은 따뜻함, 지식·지혜 기반의 전략가형.",
        "무": "산처럼 안정적, 책임감 강하고 뚝심 있는 기운.",
        "기": "논밭 같은 실속형, 현실적이며 균형 감각 뛰어남.",
        "경": "강철 같은 결단력·경쟁력, 추진력 강한 실전형.",
        "신": "보석 같은 매력, 감각적이며 창조적인 스타일.",
        "임": "큰 물 같은 포용력·직관력·영감 풍부.",
        "계": "가랑비 같은 섬세함, 분석력·관찰력 뛰어난 스타일."
    }
    return traits.get(day_stem, "일간 정보를 찾을 수 없습니다.")


# 띠 정보
def get_animal(branch):
    return branch_to_animal.get(branch, "")
# ---------------------------------------------------------
# PART 3 — 2026년 (병오년) 전체 운세 해석 + 종합 사주 해석
# ---------------------------------------------------------

YEAR_ELEMENT = "화"
YEAR_GANJI = "병오"

# 오행 상생/상극 관계
generate_map = {
    "목": "화",
    "화": "토",
    "토": "금",
    "금": "수",
    "수": "목",
}
control_map = {
    "목": "토",
    "토": "수",
    "수": "화",
    "화": "금",
    "금": "목",
}


# 2026년 – 일간과의 관계
def element_relation_2026(day_element):
    reverse_generate = {v: k for k, v in generate_map.items()}

    if day_element == YEAR_ELEMENT:
        return (
            "2026년은 당신의 일간과 같은 **화(火) 기운이 극대화되는 해**입니다.\n"
            "자신감·표현력·주도권이 강하게 살아나 스스로 길을 여는 힘이 커집니다."
        )
    elif generate_map.get(day_element) == YEAR_ELEMENT:
        return (
            "2026년의 화(火)는 당신이 에너지를 내어 키우는 흐름입니다.\n"
            "노력 대비 보상이 잘 들어오지만 체력 소모가 큰 해이니 균형이 필요합니다."
        )
    elif reverse_generate.get(day_element) == YEAR_ELEMENT:
        return (
            "2026년은 화(火)가 당신을 도와주는 구조입니다.\n"
            "귀인 등장·제안·기회·협력 같은 긍정적 흐름이 잘 들어오는 해입니다."
        )
    elif control_map.get(day_element) == YEAR_ELEMENT:
        return (
            "화(火)가 당신을 억누르는 구조라, 과도한 스트레스나 경쟁이 생기기 쉽습니다.\n"
            "큰 욕심보다 안정적인 전략이 더 유리한 해입니다."
        )
    elif control_map.get(YEAR_ELEMENT) == day_element:
        return (
            "2026년은 화(火) 기운을 다스리는 위치가 됩니다.\n"
            "리더십·관리·조율 능력이 필요하며 중요한 역할을 맡게 될 수 있습니다."
        )
    else:
        return (
            "2026년의 화(火)는 당신에게 중립적인 흐름입니다.\n"
            "큰 변동보다 꾸준함이 힘을 발휘하는 해입니다."
        )


# ---------------------------------------------------------
# ⭐ 사주 전체 종합 해석
# ---------------------------------------------------------
def full_saju_reading(pillars, element_counts, day_element):
    y_s, y_b = pillars["year"]
    m_s, m_b = pillars["month"]
    d_s, d_b = pillars["day"]
    h_s, h_b = pillars["hour"] if pillars["hour"] else (None, None)

    strong = [e for e,c in element_counts.items() if c >= 4]
    weak = [e for e,c in element_counts.items() if c <= 1]

    lines = []
    lines.append("## 🧿 사주 전체 종합 해석")

    # 기본 성향
    lines.append(f"### 🌈 기본 성향 (일간 중심)\n- 당신의 일간은 **{d_s}({day_element})** 입니다. "
                 f"이는 성향적으로 '{get_day_master_trait(d_s)}' 기운이 핵심 성격을 이끕니다.")

    # 오행 요약
    lines.append("### 🔍 오행 균형 분석")
    lines.append(
        f"- 목:{element_counts['목']} · 화:{element_counts['화']} · 토:{element_counts['토']} · 금:{element_counts['금']} · 수:{element_counts['수']}"
    )
    if strong:
        lines.append(f"- **강한 오행** → {', '.join(strong)} 기운이 성격·관계·기질에 큰 영향을 줍니다.")
    if weak:
        lines.append(f"- **약한 오행** → {', '.join(weak)} 분야에서 약점이 나타나기 쉬우며 보완이 필요합니다.")

    # 연주
    lines.append("### 👨‍👩‍👧 연주 기반 선천적 배경·가정운")
    lines.append(
        f"- 연주는 **{y_s}{y_b}**로, 유년기 환경과 선천적 기질을 의미합니다.\n"
        f"- 어린 시절부터 형성된 가치관, 안정감, 감정 습관이 현재 성격의 기초가 됩니다."
    )

    # 월주
    lines.append("### 🏛 월주 기반 사회성·직업·역량")
    lines.append(
        f"- 월주는 **{m_s}{m_b}**로, 사회적 능력·일 능력·직업 기조를 나타냅니다.\n"
        f"- 사회에서 어떤 역할을 맡기 좋은지, 일 처리 방식이 어떤지 드러나는 자리입니다."
    )

    # 일주
    lines.append("### ❤️ 일주 기반 성격·인간관계·연애")
    lines.append(
        f"- 일주는 **{d_s}{d_b}**이며, 당신의 성품·감정·대인관계 방식의 핵심입니다.\n"
        "- 타고난 성격, 사람을 대하는 방식, 연애 성향이 강하게 드러납니다."
    )

    # 시주
    if h_s:
        lines.append("### 🌙 시주 기반 재능·내면·노년운")
        lines.append(
            f"- 시주는 **{h_s}{h_b}**로, 겉으로 드러나지 않는 재능·내면적 만족감·노년 안정과 깊은 관련이 있습니다."
        )
    else:
        lines.append("### 🌙 시주 분석 없음")
        lines.append("- 태어난 시간이 없어 내면·노년운 분석이 제한됩니다.")

    # 디테일 성향 분석
    lines.append("### 🔥 상세 성향 분석")
    if '목' in strong: lines.append("- **목(木) 강함** → 성장욕구·도전·확장운이 강함.")
    if '화' in strong: lines.append("- **화(火) 강함** → 에너지·표현력·매력 대폭 상승.")
    if '토' in strong: lines.append("- **토(土) 강함** → 책임감·안정성·계획력이 우수.")
    if '금' in strong: lines.append("- **금(金) 강함** → 분석·판단·이성·정확함이 뛰어남.")
    if '수' in strong: lines.append("- **수(水) 강함** → 직감·지혜·유연함·지식 습득력 상승.")

    if weak:
        lines.append("\n### ⚠ 약점·보완 포인트")
        if '목' in weak: lines.append("- **목 부족** → 추진력 약함 → 목표·루틴 강화 필요.")
        if '화' in weak: lines.append("- **화 부족** → 의욕·표현력 약함 → 운동·대화 증가 필요.")
        if '토' in weak: lines.append("- **토 부족** → 책임감 약함 → 일정관리 습관이 필요.")
        if '금' in weak: lines.append("- **금 부족** → 집중력 떨어짐 → 정리·계획이 도움됨.")
        if '수' in weak: lines.append("- **수 부족** → 직관·지혜 약함 → 휴식·명상 필요.")

    lines.append("### 🧩 종합 결론")
    lines.append(
        "- 강한 오행은 인생의 무기가 되고, 약한 오행을 조금만 보완해도 전체 삶의 균형이 크게 높아집니다."
    )

    return "\n".join(lines)


# ---------------------------------------------------------
# 2026 연애운
# ---------------------------------------------------------
def love_2026(day_element, counts):
    fire = counts["화"]
    water = counts["수"]
    wood = counts["목"]

    lines = []
    lines.append(f"### 💖 2026년 연애운 ({YEAR_GANJI})\n")
    lines.append(element_relation_2026(day_element))

    if fire >= 4:
        lines.append(
            "- 화(火)가 매우 강해 감정기복이 커지고 예민해질 수 있는 해입니다.\n"
            "- 연애 중이라면 **소통 방식이 가장 큰 변수**가 됩니다."
        )
    elif water >= 3:
        lines.append(
            "- 수(水) 기운이 넉넉해 상대 마음을 잘 읽고 따뜻하게 다가갈 수 있습니다.\n"
            "- 표현만 조금만 늘려도 훨씬 좋은 흐름이 만들어집니다."
        )
    else:
        lines.append(
            "- 새로운 인연보다는 **기존 관계가 깊어지는 진심의 해**입니다.\n"
            "- 과거 인연과 재회할 가능성도 있습니다."
        )

    if wood == 0:
        lines.append(
            "- 목(木) 부족 → 주도성이 약해 타이밍을 놓치기 쉬움.\n"
            "- 작은 메시지·안부만 먼저 보내도 연애운이 크게 상승합니다."
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# 2026 재물운
# ---------------------------------------------------------
def money_2026(day_element, counts):
    metal = counts["금"]
    earth = counts["토"]

    lines = []
    lines.append("### 💰 2026년 재물운\n")
    lines.append("- 화(火)의 영향으로 **돈의 흐름이 빠르게 순환**하는 해입니다.")

    if metal >= 4:
        lines.append(
            "- 금(金) 강함 → 투자 감각 상승, 숫자 감각 날카로움.\n"
            "- 단, 욕심이 과하면 손실 위험 커짐. 리스크 관리 필수!"
        )
    elif earth >= 3:
        lines.append(
            "- 토(土) 많음 → 기반 다지기·저축·부채정리 유리.\n"
            "- 급하게 투자하기보다 안정적 구조가 유리."
        )
    else:
        lines.append(
            "- ‘버는 만큼 나가는’ 구조.\n"
            "- 소비 관리·정기 지출 점검이 핵심."
        )

    lines.append("- **2026 재테크 키워드:** 현금흐름 관리, 지출 통제, 계약 조항 확인.")

    return "\n".join(lines)


# ---------------------------------------------------------
# 2026 직업·커리어운
# ---------------------------------------------------------
def job_2026(day_element, counts):
    wood = counts["목"]
    fire = counts["화"]
    metal = counts["금"]

    lines = []
    lines.append("### 💼 2026년 직업·커리어운\n")
    lines.append("- 환경 변화가 잦고 새로운 기회가 자주 들어오는 해입니다.")

    if wood >= 3:
        lines.append(
            "- 목(木) 강함 → 이직·전직·창업 욕구 증가.\n"
            "- 상반기 준비·하반기 실행이 이상적."
        )

    if fire >= 3:
        lines.append(
            "- 화(火) 강함 → 영업·교육·홍보·기획 등 ‘사람을 상대하는 직무’에서 성과 상승.\n"
            "- 과로 주의!"
        )

    if metal == 0:
        lines.append(
            "- 금(金) 부족 → 문서·계약·법적 실수 주의. 서류 2회 검토 필수."
        )
    else:
        lines.append(
            "- 새로운 사람·조직과의 협력이 많아지고 네트워크 확장이 유리."
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# 2026 건강운
# ---------------------------------------------------------
def health_2026(day_element, counts):
    fire = counts["화"]
    water = counts["수"]
    earth = counts["토"]

    lines = []
    lines.append("### 💊 2026년 건강운\n")
    lines.append("- 화(火)는 심장·혈압·눈·신경계와 직접적 관련이 있습니다.")

    if fire >= 4:
        lines.append(
            "- 화 과다 → 심혈·혈압 문제 가능성.\n"
            "- 카페인·야식·스트레스 관리 필수."
        )

    if water == 0:
        lines.append(
            "- 수 부족 → 순환기·신장·방광 불균형.\n"
            "- 물 섭취·유산소 운동이 큰 도움."
        )

    if earth >= 3:
        lines.append(
            "- 토 과다 → 소화기 부담.\n"
            "- 밀가루·과식 줄이고 쉽게 소화되는 식단 추천."
        )

    lines.append("- 작은 습관을 꾸준히 만들면 문제 없이 지나가는 해입니다.")

    return "\n".join(lines)


# ---------------------------------------------------------
# 2026 이사·주거운
# ---------------------------------------------------------
def moving_2026(day_element, counts):
    wood = counts["목"]
    earth = counts["토"]

    lines = []
    lines.append("### 🏡 2026년 이사·주거운\n")
    lines.append("- 생활 환경을 정리하거나 바꾸고 싶은 욕구가 커지는 해입니다.")

    if earth >= 4:
        lines.append(
            "- 토(土) 강함 → 실제 이사보다 인테리어·정리·개선이 더 유리."
        )
    elif wood >= 3:
        lines.append(
            "- 목(木) 강함 → 실제 이사 가능성이 큼.\n"
            "- 채광·통풍·거리·편의성 위주로 선택하면 좋음."
        )
    else:
        lines.append(
            "- 무난한 이사운이 들어오는 해.\n"
            "- 계약 조건·보증금만 꼼꼼히 확인!"
        )

    return "\n".join(lines)
# ---------------------------------------------------------
# PART 4 — Streamlit 최종 UI
# ---------------------------------------------------------

st.markdown("<div class='title-main'>🔮 사주 분석 리포트</div>", unsafe_allow_html=True)
st.markdown("<div class='title-sub'>생년월일과 태어난 시를 기반으로 4기둥·오행·성향·2026년 운세를 종합 분석합니다.</div>", unsafe_allow_html=True)

st.markdown("<div class='section-header'>1️⃣ 기본정보 입력</div>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.2, 0.8, 0.8])

with col1:
    birth_date = st.date_input(
        "📅 생년월일(양력)",
        min_value=date(1900,1,1),
        max_value=date(2500,12,31)
    )

with col2:
    hour_opt = st.selectbox(
        "⏰ 태어난 시",
        ["모름"] + list(range(24)),
        format_func=lambda x: f"{x}시" if isinstance(x,int) else x
    )
    birth_hour = None if hour_opt == "모름" else hour_opt

with col3:
    gender = st.radio("성별", ["남성","여성"])

st.divider()

# ---------------------------------------------------------
# 4기둥 계산
# ---------------------------------------------------------
pillars = get_four_pillars(birth_date, birth_hour)

if not pillars:
    st.error("사주 정보를 계산할 수 없습니다.")
    st.stop()

y_s, y_b = pillars["year"]
m_s, m_b = pillars["month"]
d_s, d_b = pillars["day"]
h_s, h_b = pillars["hour"] if pillars["hour"] else (None, None)

day_element = stem_to_element[d_s]
animal = get_animal(y_b)

# 오행 카운트
element_counts = count_elements(pillars)

# ---------------------------------------------------------
# 1) 사주 4기둥 출력
# ---------------------------------------------------------
st.markdown("<div class='section-header'>2️⃣ 사주 4기둥 (년·월·일·시)</div>", unsafe_allow_html=True)

colA, colB, colC, colD = st.columns(4)

with colA:
    st.markdown("<div class='card-box'><b>연주(年柱)</b><br>"
                f"{y_s}{y_b}<br>{animal}</div>", unsafe_allow_html=True)
with colB:
    st.markdown("<div class='card-box'><b>월주(月柱)</b><br>"
                f"{m_s}{m_b}</div>", unsafe_allow_html=True)
with colC:
    st.markdown("<div class='card-box'><b>일주(日柱)</b><br>"
                f"{d_s}{d_b}<br>(일간: {day_element})</div>", unsafe_allow_html=True)
with colD:
    if h_s:
        st.markdown("<div class='card-box'><b>시주(時柱)</b><br>"
                    f"{h_s}{h_b}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card-box'><b>시주(時柱)</b><br>정보 없음</div>", unsafe_allow_html=True)

# -----------------------------------------------------
# ⭐ NEW: 사주 전체 종합 해석 출력
# -----------------------------------------------------

full_reading_text = full_saju_reading(pillars, element_counts, day_element)

st.markdown("""
<div class='card-box'>
    <h3 style='margin-bottom:10px;'>🧿 사주 전체 종합 해석</h3>
</div>
""", unsafe_allow_html=True)

st.markdown(full_reading_text)

st.divider()

# ---------------------------------------------------------
# 2) 일간 성향
# ---------------------------------------------------------
st.markdown("<div class='section-header'>3️⃣ 일간 성향 분석</div>", unsafe_allow_html=True)
st.markdown(f"<div class='card-box'>{get_day_master_trait(d_s)}</div>", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------
# 3) 오행 분포 (가로형 + 동그란 숫자)
# ---------------------------------------------------------

st.markdown("<div class='section-header'>4️⃣ 오행 분포</div>", unsafe_allow_html=True)

# CSS – 원형 숫자 스타일
st.markdown("""
<style>
.element-row {
    display: flex;
    gap: 25px;
    align-items: center;
    margin-top: 10px;
    margin-bottom: 25px;
}
.element-box {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
}
.circle-num {
    width: 38px;
    height: 38px;
    background: #f0f3ff;
    border: 2px solid #4B6BFB;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 700;
    color: #2A3F8D;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class='card-box'>
    <div class='element-row'>
        <div class='element-box'>🌳 목 <div class='circle-num'>{element_counts['목']}</div></div>
        <div class='element-box'>🔥 화 <div class='circle-num'>{element_counts['화']}</div></div>
        <div class='element-box'>⛰️ 토 <div class='circle-num'>{element_counts['토']}</div></div>
        <div class='element-box'>⚔️ 금 <div class='circle-num'>{element_counts['금']}</div></div>
        <div class='element-box'>💧 수 <div class='circle-num'>{element_counts['수']}</div></div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------
# 4) 2026년 운세 (연애·재물·직업·건강·이사)
# ---------------------------------------------------------

st.markdown("<div class='section-header'>5️⃣ 2026년 종합 운세 (병오년)</div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["💖 연애운", "💰 재물운", "💼 직업운", "💊 건강운", "🏡 이사·주거운"]
)

with tab1:
    st.markdown(love_2026(day_element, element_counts))

with tab2:
    st.markdown(money_2026(day_element, element_counts))

with tab3:
    st.markdown(job_2026(day_element, element_counts))

with tab4:
    st.markdown(health_2026(day_element, element_counts))

with tab5:
    st.markdown(moving_2026(day_element, element_counts))
# ---------------------------------------------------------
# 🖼 PNG EXPORT (탭 외부 안정 버전)
# ---------------------------------------------------------

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import io

# 1) 한글 폰트 자동 설정
def set_korean_font():
    font_list = fm.findSystemFonts(fontpaths=["C:/Windows/Fonts"])
    target_fonts = ["malgun.ttf", "malgunbd.ttf", "gulim.ttc", "batang.ttc"]

    selected_font = None
    for f in font_list:
        lf = f.lower()
        if any(tf in lf for tf in target_fonts):
            selected_font = f
            break

    if selected_font:
        prop = fm.FontProperties(fname=selected_font)
        plt.rc("font", family=prop.get_name())
    else:
        plt.rc("font", family="sans-serif")

set_korean_font()

# 2) 리포트 텍스트 생성
report_text = f"""
🔮 프리미엄 사주 분석 리포트

[기본 정보]
- 생년월일: {birth_date}
- 태어난 시: {hour_opt}
- 성별: {gender}

[사주 4기둥]
- 연주: {y_s}{y_b} ({animal})
- 월주: {m_s}{m_b}
- 일주: {d_s}{d_b} ({day_element})
- 시주: {h_s}{h_b if h_s else '정보 없음'}

[오행 분포]
- 목:{element_counts['목']}  화:{element_counts['화']}  토:{element_counts['토']}
- 금:{element_counts['금']}  수:{element_counts['수']}

[사주 전체 종합 해석]
{full_saju_reading(pillars, element_counts, day_element)}

[2026년 연애운]
{love_2026(day_element, element_counts)}

[2026년 재물운]
{money_2026(day_element, element_counts)}

[2026년 직업운]
{job_2026(day_element, element_counts)}

[2026년 건강운]
{health_2026(day_element, element_counts)}

[2026년 이사·주거운]
{moving_2026(day_element, element_counts)}
"""

# 3) PNG 이미지 생성
fig = plt.figure(figsize=(8, 14), dpi=200)
plt.text(0.01, 0.99, report_text, va="top", fontsize=9, wrap=True)
plt.axis("off")

buf = io.BytesIO()
plt.savefig(buf, format="png", dpi=200, bbox_inches="tight")
buf.seek(0)
plt.close()

# 4) 다운로드 버튼 (이제 정상 표시됨)
st.download_button(
    label="📥 사주 리포트 PNG 다운로드",
    data=buf,
    file_name="saju_report.png",
    mime="image/png"
)
