import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 평점 문자열을 숫자로 변환하기 위한 딕셔너리
RATING_MAPPING = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}


def scrape_books_data():
    books_data = []

    # 진행 상태를 표시하기 위한 Streamlit 요소
    progress_bar = st.progress(0)
    status_text = st.empty()

    # 전체 50페이지 스크래핑 (총 1000권)
    total_pages = 50

    for page in range(1, total_pages + 1):
        url = f"https://books.toscrape.com/catalogue/page-{page}.html"
        response = requests.get(url)

        if response.status_code != 200:
            st.error(f"{page} 페이지를 불러오는 데 실패했습니다.")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        articles = soup.find_all("article", class_="product_pod")

        for article in articles:
            # 1. 도서 제목 추출
            title = article.h3.a["title"]

            # 2. 가격 추출 (문자열에서 '£' 및 특수문자 제거 후 실수형으로 변환)
            price_str = article.find("p", class_="price_color").text
            price = float(price_str.replace("£", "").replace("Â", "").strip())

            # 3. 평점 추출
            rating_class = article.find("p", class_="star-rating")["class"][1]
            rating = RATING_MAPPING.get(rating_class, 0)

            books_data.append({
                "도서명": title,
                "가격(£)": price,
                "평점": rating
            })

        # 진행률 업데이트
        progress_bar.progress(page / total_pages)
        status_text.text(f"데이터 수집 중... ({page}/{total_pages} 페이지 완료)")

    status_text.text("✅ 데이터 수집이 완료되었습니다!")
    time.sleep(1)  # 완료 메시지를 잠시 보여주기 위한 대기
    status_text.empty()  # 상태 텍스트 초기화
    progress_bar.empty()  # 프로그레스 바 초기화

    return pd.DataFrame(books_data)


# --- 화면 구성 ---

# 사이트 제목
st.set_page_config(page_title="도서 데이터 분석기", page_icon="📚", layout="wide")
st.title("📚 Books to Scrape 데이터 수집 및 분석")
st.write("버튼을 누르면 [books.toscrape.com](https://books.toscrape.com/) 사이트의 모든 도서 데이터를 수집합니다.")

# 데이터 수집 버튼
if st.button("도서 데이터 수집 시작", type="primary"):
    with st.spinner("데이터를 가져오는 중입니다. 잠시만 기다려주세요..."):
        # 스크래핑 함수 실행
        df = scrape_books_data()

    if not df.empty:
        st.success("총 1,000권의 도서 데이터를 성공적으로 수집했습니다!")

        # 데이터 분석 (총 도서 수, 평균 가격, 평균 평점 계산)
        total_books = len(df)
        avg_price = df["가격(£)"].mean()
        avg_rating = df["평점"].mean()

        # 지표(Metrics) 표시
        st.markdown("### 📊 데이터 요약")
        col1, col2, col3 = st.columns(3)
        col1.metric("총 도서 수", f"{total_books:,} 권")
        col2.metric("평균 가격", f"£ {avg_price:.2f}")
        col3.metric("평균 평점", f"{avg_rating:.2f} 점")

        st.markdown("---")

        # 상세 데이터 표시
        st.markdown("### 📖 수집된 도서 상세 정보")
        # 데이터프레임을 인터랙티브한 표 형태로 출력
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "가격(£)": st.column_config.NumberColumn(format="£ %.2f"),
                "평점": st.column_config.NumberColumn(format="%d 점")
            }
        )

        # CSV 다운로드 버튼 (선택 사항)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="수집된 데이터 CSV로 다운로드",
            data=csv,
            file_name='scraped_books.csv',
            mime='text/csv',
        )
    else:
        st.error("데이터 수집에 실패했습니다.")