#!/usr/bin/env python3
"""
weather-gui: A desktop weather app powered by Open-Meteo.
No API key required. Built with tkinter.
"""

import sys
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
from datetime import datetime

# ============ 配置 ============
GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: ("☀️", "晴朗", "#B8860B"),
    1: ("🌤", "大部晴朗", "#4682B4"),
    2: ("⛅", "多云", "#708090"),
    3: ("☁️", "阴天", "#696969"),
    45: ("🌫", "雾", "#808080"),
    48: ("🌫", "雾凇", "#A9A9A9"),
    51: ("🌦", "毛毛雨", "#5F9EA0"),
    53: ("🌦", "中度毛毛雨", "#5F9EA0"),
    55: ("🌧", "密集毛毛雨", "#4682B4"),
    61: ("🌧", "小雨", "#4682B4"),
    63: ("🌧", "中雨", "#4169E1"),
    65: ("🌧", "大雨", "#0000CD"),
    71: ("🌨", "小雪", "#87CEEB"),
    73: ("🌨", "中雪", "#87CEEB"),
    75: ("❄️", "大雪", "#4682B4"),
    77: ("❄️", "雪粒", "#B0E0E6"),
    80: ("🌦", "小阵雨", "#5F9EA0"),
    81: ("🌧", "中阵雨", "#4682B4"),
    82: ("🌧", "强阵雨", "#0000CD"),
    85: ("🌨", "小阵雪", "#87CEEB"),
    86: ("❄️", "强阵雪", "#4682B4"),
    95: ("⛈", "雷雨", "#483D8B"),
    96: ("⛈", "雷雨伴小冰雹", "#4B0082"),
    99: ("⛈", "雷雨伴大冰雹", "#191970"),
}

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌤 天气查询")
        self.root.geometry("520x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f4f8")

        # 设置窗口居中
        self.center_window()

        self.setup_ui()

    def center_window(self):
        self.root.update_idletasks()
        width = 520
        height = 700
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        # 标题
        title = tk.Label(
            self.root,
            text="🌤 天气查询",
            font=("Microsoft YaHei", 24, "bold"),
            bg="#f0f4f8",
            fg="#2c3e50"
        )
        title.pack(pady=15)

        # 输入框区域
        input_frame = tk.Frame(self.root, bg="#f0f4f8")
        input_frame.pack(pady=10)

        self.city_entry = tk.Entry(
            input_frame,
            font=("Microsoft YaHei", 14),
            width=18,
            justify="center",
            relief="solid",
            bd=2
        )
        self.city_entry.pack(side=tk.LEFT, padx=5)
        self.city_entry.insert(0, "北京")
        self.city_entry.bind('<Return>', lambda e: self.query_weather())

        # 查询按钮
        self.query_btn = tk.Button(
            input_frame,
            text="🔍 查询",
            font=("Microsoft YaHei", 12),
            bg="#3498db",
            fg="white",
            activebackground="#2980b9",
            activeforeground="white",
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.query_weather
        )
        self.query_btn.pack(side=tk.LEFT, padx=5)

        # 加载提示
        self.loading_label = tk.Label(
            self.root,
            text="",
            font=("Microsoft YaHei", 12),
            bg="#f0f4f8",
            fg="#3498db"
        )
        self.loading_label.pack(pady=5)

        # 结果区域 - 当前天气
        self.current_frame = tk.Frame(
            self.root,
            bg="white",
            relief="flat",
            bd=0
        )
        self.current_frame.pack(fill=tk.X, padx=20, pady=5)

        # 结果区域 - 预报
        self.forecast_frame = tk.Frame(
            self.root,
            bg="white",
            relief="flat",
            bd=0
        )
        self.forecast_frame.pack(fill=tk.X, padx=20, pady=5)

        # 底部信息
        footer = tk.Label(
            self.root,
            text="数据来源: Open-Meteo API | 无需 API Key",
            font=("Microsoft YaHei", 9),
            bg="#f0f4f8",
            fg="#95a5a6"
        )
        footer.pack(side=tk.BOTTOM, pady=10)

    def query_weather(self):
        city = self.city_entry.get().strip()
        if not city:
            messagebox.showwarning("提示", "请输入城市名")
            return

        self.query_btn.config(state=tk.DISABLED)
        self.loading_label.config(text="🔄 正在查询...")
        self.clear_results()

        # 在新线程中查询，避免界面卡死
        Thread(target=self.fetch_weather, args=(city,), daemon=True).start()

    def clear_results(self):
        for widget in self.current_frame.winfo_children():
            widget.destroy()
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

    def fetch_weather(self, city):
        try:
            location = self.get_coordinates(city)
            data = self.get_weather(location["lat"], location["lon"])

            # 回到主线程更新UI
            self.root.after(0, self.display_current, location, data["current"])
            self.root.after(0, self.display_forecast, data["daily"])
            self.root.after(0, self.on_query_done)

        except Exception as e:
            self.root.after(0, self.on_error, str(e))

    def on_query_done(self):
        self.query_btn.config(state=tk.NORMAL)
        self.loading_label.config(text="✅ 查询完成")

    def on_error(self, error_msg):
        self.query_btn.config(state=tk.NORMAL)
        self.loading_label.config(text="❌ 查询失败")
        messagebox.showerror("错误", f"查询失败:\n{error_msg}")

    def get_coordinates(self, city):
        resp = requests.get(GEO_URL, params={"name": city, "count": 1, "language": "zh"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("results"):
            raise ValueError(f"未找到城市: {city}")

        result = data["results"][0]
        return {
            "lat": result["latitude"],
            "lon": result["longitude"],
            "name": result.get("name", city),
            "country": result.get("country", ""),
            "admin1": result.get("admin1", ""),
        }

    def get_weather(self, lat, lon):
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "weather_code",
                "wind_speed_10m",
                "apparent_temperature",
                "pressure_msl",
            ],
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "wind_speed_10m_max",
            ],
            "timezone": "auto",
            "forecast_days": 4,
        }

        resp = requests.get(WEATHER_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def display_current(self, location, current):
        code = current["weather_code"]
        emoji, desc, color = WMO_CODES.get(code, ("❓", "未知", "#808080"))

        location_str = location["name"]
        if location["admin1"]:
            location_str += f", {location['admin1']}"

        # 清空并重建
        for widget in self.current_frame.winfo_children():
            widget.destroy()

        # 地点
        tk.Label(
            self.current_frame,
            text=f"📍 {location_str}",
            font=("Microsoft YaHei", 14, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(pady=(15, 5))

        # 天气图标
        tk.Label(
            self.current_frame,
            text=emoji,
            font=("Segoe UI Emoji", 48),
            bg="white"
        ).pack()

        # 天气描述
        tk.Label(
            self.current_frame,
            text=desc,
            font=("Microsoft YaHei", 16, "bold"),
            bg="white",
            fg=color
        ).pack()

        # 温度
        tk.Label(
            self.current_frame,
            text=f"{current['temperature_2m']}°C",
            font=("Microsoft YaHei", 36, "bold"),
            bg="white",
            fg="#e74c3c"
        ).pack(pady=5)

        # 详细信息网格
        info_frame = tk.Frame(self.current_frame, bg="white")
        info_frame.pack(pady=10)

        infos = [
            (f"体感 {current['apparent_temperature']}°C", "#e67e22"),
            (f"湿度 {current['relative_humidity_2m']}%", "#3498db"),
            (f"风速 {current['wind_speed_10m']} km/h", "#27ae60"),
            (f"气压 {current['pressure_msl']} hPa", "#9b59b6"),
        ]

        for i, (text, color) in enumerate(infos):
            tk.Label(
                info_frame,
                text=text,
                font=("Microsoft YaHei", 11),
                bg="white",
                fg=color,
                padx=8
            ).grid(row=0, column=i, padx=5)

    def display_forecast(self, daily):
        # 清空
        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

        tk.Label(
            self.forecast_frame,
            text="📅 未来预报",
            font=("Microsoft YaHei", 14, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(pady=(10, 5))

        # 预报卡片容器
        cards_frame = tk.Frame(self.forecast_frame, bg="white")
        cards_frame.pack(pady=5)

        for i in range(1, min(4, len(daily["time"]))):
            date = daily["time"][i]
            weekday = WEEKDAYS[datetime.strptime(date, "%Y-%m-%d").weekday()]

            code = daily["weather_code"][i]
            emoji, desc, color = WMO_CODES.get(code, ("❓", "未知", "#808080"))

            # 单日卡片
            card = tk.Frame(
                cards_frame,
                bg="#f8f9fa",
                relief="flat",
                bd=1
            )
            card.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.Y)

            tk.Label(
                card,
                text=weekday,
                font=("Microsoft YaHei", 11, "bold"),
                bg="#f8f9fa",
                fg="#2c3e50"
            ).pack(pady=(8, 0))

            tk.Label(
                card,
                text=date[5:],
                font=("Microsoft YaHei", 9),
                bg="#f8f9fa",
                fg="#7f8c8d"
            ).pack()

            tk.Label(
                card,
                text=emoji,
                font=("Segoe UI Emoji", 24),
                bg="#f8f9fa"
            ).pack(pady=3)

            tk.Label(
                card,
                text=desc,
                font=("Microsoft YaHei", 10),
                bg="#f8f9fa",
                fg=color
            ).pack()

            tk.Label(
                card,
                text=f"↑{daily['temperature_2m_max'][i]}° ↓{daily['temperature_2m_min'][i]}°",
                font=("Microsoft YaHei", 10, "bold"),
                bg="#f8f9fa",
                fg="#e74c3c"
            ).pack(pady=(0, 8))


def main():
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
