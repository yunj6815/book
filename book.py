import streamlit as st
import pandas as pd
import requests
import time

# 🔑 네이버 API 마스터키
# 큰따옴표("") 안에 공백 없이 정확히 키만 붙여넣고 반드시 저장(Ctrl+S)해 주세요!
CLIENT_ID = "CeoJyvYZXRWXsoCAChtj"
CLIENT_SECRET = "jTS0iTfm1W"


def get_book_info(query):
    """네이버 도서 검색 API를 통해 도서 정보를 가져옵니다."""
    url = "https://openapi.naver.com/v1/search/book.json"
    headers = {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET
    }
    params = {"query": query, "display": 1}

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        # 1. API 키 오류 등 네이버에서 거절한 경우 명확한 에러 출력
        if 'errorMessage' in data:
            return f"인증 에러 (키 확인 필요)", f"에러코드: {data.get('errorCode')}", "-"

        # 2. 검색 결과가 있는 경우
        if data.get('items'):
            item = data['items'][0]
            # 네이버는 도서 API에서 정가(price) 제공을 중단하고 판매가(discount)만 제공하는 경우가 많습니다.
            return item.get('discount', '정보 없음'), item.get('discount', '정보 없음'), item.get('title', '-').replace('<b>',
                                                                                                                '').replace(
                '</b>', '')

        # 3. 검색 결과가 없는 경우
        return "결과 없음", "결과 없음", "-"

    except Exception as e:
        return "네트워크/통신 오류", "-", "-"


# 스트림릿 페이지 설정
st.set_page_config(page_title="도서 정가 검색기", layout="wide")
st.title("📚 도서 데이터 통합 정가 검색기")

uploaded_file = st.file_uploader("파일을 선택하세요 (CSV 또는 XLSX)", type=['csv', 'xlsx'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, engine='openpyxl')

    st.write("📋 업로드된 데이터 확인:", df.head())

    required_cols = ['책제목', '저자']
    if all(col in df.columns for col in required_cols):
        if st.button("🔍 정가 검색 시작"):

            # 💡 수정 포인트: 검색 조건을 느슨하게 (책제목 + 저자 만으로 검색)
            df['검색키워드'] = df['책제목'].astype(str) + " " + df['저자'].astype(str)

            prices, discounts, found_titles = [], [], []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, query in enumerate(df['검색키워드']):
                p, d, t = get_book_info(query)
                prices.append(p)
                discounts.append(d)
                found_titles.append(t)

                time.sleep(0.1)
                progress_bar.progress((i + 1) / len(df))
                status_text.text(f"진행 중: {i + 1}/{len(df)} 권 완료")

            df['API_조회_제목'] = found_titles
            df['정가'] = prices
            df['판매가'] = discounts

            st.success("조사가 완료되었습니다!")
            final_df = df.drop(columns=['검색키워드'])
            st.dataframe(final_df)

            csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 결과 파일 다운로드 (CSV)",
                data=csv_data,
                file_name="book_price_results.csv",
                mime="text/csv"
            )
    else:
        st.error("파일에 '책제목', '저자', '출판사' 컬럼이 모두 포함되어 있는지 확인해 주세요.")