import tkinter as tk
from tkinter import messagebox, font
import requests
import datetime
import os
from dotenv import load_dotenv
import re

# .env 파일에서 API 키 로드
load_dotenv()
API_KEY = os.getenv("NEIS_API_KEY")

# 학교 이름으로 교육청 코드와 학교 코드를 가져오는 함수
def get_school_codes(school_name):
    url = f"https://open.neis.go.kr/hub/schoolInfo?KEY={API_KEY}&Type=json&SCHUL_NM={school_name}"
    response = requests.get(url)
    data = response.json()

    try:
        school_info = data["schoolInfo"][1]["row"][0]
        office_code = school_info["ATPT_OFCDC_SC_CODE"]
        school_code = school_info["SD_SCHUL_CODE"]
        return office_code, school_code
    except (KeyError, IndexError):
        return None, None

# 급식 정보를 가져오는 함수
def get_meal_info(office_code, school_code, date):
    url = (f"https://open.neis.go.kr/hub/mealServiceDietInfo?KEY={API_KEY}"
           f"&ATPT_OFCDC_SC_CODE={office_code}&SD_SCHUL_CODE={school_code}"
           f"&MLSV_YMD={date}&Type=json")
    response = requests.get(url)
    data = response.json()

    try:
        meal_info = data["mealServiceDietInfo"][1]["row"][0]["DDISH_NM"]
        # 괄호 안의 숫자(영양소 정보) 제거
        meal_info = re.sub(r"\([^)]*\)", "", meal_info)
        return meal_info.replace("<br/>", "\n")
    except (KeyError, IndexError):
        return "오늘은 급식 정보가 없습니다."

# 급식과 건강 정보를 분석하는 함수
def check_meal_health(meal, health_conditions):
    warnings = []
    allergy_warnings = []  # 알레르기 관련 경고를 따로 저장
    
    unique_foods = []  # 중복 제거를 위한 배열

    # 메뉴를 줄 단위로 분리하여 중첩 반복문으로 분석
    for line in meal.split("\n"):
        for food in line.split(", "):  # ',' 기준으로 개별 음식 추출
            food = food.strip()  # 음식 이름의 공백 제거
            if food not in unique_foods:
                unique_foods.append(food)  # 중복 제거
                # 음식별 건강 상태 체크
                if health_conditions["고혈압"] and ("짠 음식" in food or "김치" in food):
                    warnings.append(f"염분이 높은 음식({food})이 포함되어 있습니다.")
                if health_conditions["당뇨"] and ("디저트" in food or "설탕" in food):
                    warnings.append(f"당분이 높은 음식({food})이 포함되어 있습니다.")
                if health_conditions["알레르기"]:
                    for allergy in health_conditions["알레르기"]:
                        if allergy and allergy in food:
                            allergy_warnings.append(f"알레르기 유발 음식({allergy})이 포함되어 있습니다.")

    # 알레르기 경고는 마지막에 추가
    warnings.extend(allergy_warnings)

    return warnings if warnings else ["오늘 급식은 건강에 적합합니다."]

# 버튼 클릭 시 실행되는 함수
def on_check_meal():
    school_name = entry_school_name.get()
    if not school_name:
        messagebox.showwarning("입력 오류", "학교 이름을 입력하세요.")
        return

    office_code, school_code = get_school_codes(school_name)
    if not office_code or not school_code:
        messagebox.showerror("오류", "학교 정보를 가져오지 못했습니다. 학교 이름을 확인하세요.")
        return

    today = datetime.datetime.now().strftime("%Y%m%d")
    meal = get_meal_info(office_code, school_code, today)

    # 급식 정보 출력
    meal_label.config(state="normal")
    meal_label.delete("1.0", tk.END)
    meal_label.insert(tk.END, f"오늘의 급식 메뉴:\n{meal}")
    meal_label.tag_add("center", "1.0", "end")  # 가운데 정렬
    meal_label.config(state="disabled")
    adjust_meal_label_size(meal)  # 출력 크기 유동 조정

    # 건강 상태 분석
    health_conditions = {
        "고혈압": var_hbp.get(),
        "당뇨": var_dm.get(),
        "알레르기": entry_allergy.get().split(","),
    }

    analysis = check_meal_health(meal, health_conditions)
    result_label.config(text="\n".join(analysis))

# 급식 출력 상자 크기 조정 함수
def adjust_meal_label_size(meal):
    lines = meal.count("\n") + 2  # 줄 수 계산
    max_line_length = max(len(line) for line in meal.split("\n")) + 5  # 가장 긴 줄의 길이
    meal_label.config(height=min(lines, 20), width=min(max_line_length, 50))  # 크기 조정

# Tkinter 윈도우 설정
root = tk.Tk()
root.title("급식 & 건강 분석 프로그램")
root.geometry("450x650")
root.configure(bg="#F5F5F5")

# 타이틀 섹션
title_label = tk.Label(
    root, text="급식 & 건강 분석 프로그램", font=("Pretendard", 18, "bold"), bg="#F5F5F5", fg="#333333"
)
title_label.pack(pady=20)

# 학교 이름 입력 (가로 배치)
school_frame = tk.Frame(root, bg="#F5F5F5")
school_frame.pack(pady=10)

tk.Label(school_frame, text="학교 이름:", font=("Pretendard", 14, "bold"), bg="#F5F5F5").pack(side="left", padx=5)
entry_school_name = tk.Entry(school_frame, font=("Pretendard", 12), width=20)
entry_school_name.pack(side="left")

# 건강 상태 입력
tk.Label(root, text="건강 상태를 입력하세요:", font=("Pretendard", 14, "bold"), bg="#F5F5F5").pack(pady=10)

var_hbp = tk.BooleanVar()
chk_hbp = tk.Checkbutton(root, text="고혈압", variable=var_hbp, font=("Pretendard", 12), bg="#F5F5F5", relief="flat")
chk_hbp.pack(pady=5)

var_dm = tk.BooleanVar()
chk_dm = tk.Checkbutton(root, text="당뇨", variable=var_dm, font=("Pretendard", 12), bg="#F5F5F5", relief="flat")
chk_dm.pack(pady=5)

allergy_frame = tk.Frame(root, bg="#F5F5F5")
allergy_frame.pack(pady=5)

tk.Label(allergy_frame, text="알레르기:", font=("Pretendard", 14, "bold"), bg="#F5F5F5").pack(side="left", padx=5)
entry_allergy = tk.Entry(allergy_frame, font=("Pretendard", 12), width=20)
entry_allergy.pack(side="left")

# 급식 확인 버튼
check_button = tk.Button(
    root, text="급식 확인 및 분석", font=("Pretendard", 14, "bold"), bg="#4CAF50", fg="#FFFFFF",
    activebackground="#388E3C", activeforeground="#FFFFFF", command=on_check_meal
)
check_button.pack(pady=20)

# 급식 정보와 분석 결과
meal_label = tk.Text(root, font=("Pretendard", 12), height=10, width=30, state="disabled", wrap="word", bg="#FFFFFF", relief="flat")
meal_label.tag_configure("center", justify="center")  # 텍스트 가운데 정렬 설정
meal_label.pack(pady=10)

result_label = tk.Label(root, text="", font=("Pretendard", 12), bg="#F5F5F5", fg="#333333", justify="left")
result_label.pack(pady=10)

# 프로그램 실행
root.mainloop()