"""DeepSeek 尖峰計價判斷。

只判斷某個時刻會不會落到官方高峰窗口，不記載單價。

官方規則（簡體原文）：
「空闲时段价格为高峰时段价格的一半。北京时间周一至周五（不含中国法定节假日）
9:00 - 12:00、14:00 - 18:00 为高峰时段；其余时段，包括周末及中国法定节假日全天均为空闲时段。」
https://api-docs.deepseek.com/zh-cn/quick_start/pricing
英文同一規則：UTC 01:00–04:00 與 06:00–10:00，週一至週五，不含中國法定節假日。
https://api-docs.deepseek.com/quick_start/pricing/

窗口實作為半開區間 [09:00, 12:00)、[14:00, 18:00) 北京時間
（UTC [01:00, 04:00)、[06:00, 10:00)）。12:00 與 18:00 整點起算離峰。
北京時間全年 UTC+8，無夏令時。法定節假日以北京時間的曆日整天計算。

法定節假日只含《全國年節及紀念日放假辦法》（2024-11-10 修訂）裡
「全體公民放假」的當日，不含國務院放假安排裡的調休連休，也不含僅部分公民放假的日子。
https://www.mohrss.gov.cn/xxgk2020/fdzdgknr/zcfg/fg/202011/t20201103_394937.html
  元旦 1 月 1 日
  春節 除夕、正月初一至初三
  清明當日
  勞動節 5 月 1 日、5 月 2 日
  端午當日
  中秋當日
  國慶 10 月 1 日至 3 日

農曆與清明的公曆日期取自香港天文台對照表（表內月份名稱表示當天是該月初一）：
  2026 https://www.hko.gov.hk/tc/gts/time/calendar/pdf/files/2026.pdf
  2027 https://www.hko.gov.hk/tc/gts/time/calendar/pdf/files/2027.pdf
國務院當年安排只用來核對，調休與補班日不進本表：
  2026 國辦發明電〔2025〕7號 https://www.gov.cn/zhengce/zhengceku/202511/content_7047091.htm
  2027 國辦發明電〔2026〕10號 https://www.gov.cn/zhengce/content/202611/content_7085101.htm

更新：國務院公布下一年安排、且天文台對照表可核對後，只追加全體公民放假當日。
表內沒有的年份不當成假期，平日尖峰窗口仍視為尖峰（寧可不呼叫，也不付高峰價）。
"""

from datetime import date, datetime, time, timedelta, timezone


# 北京時間。中國自 1991 年起無夏令時。
BEIJING = timezone(timedelta(hours=8))

# (start inclusive, end exclusive) in Beijing local time.
PEAK_WINDOWS = (
    (time(9, 0), time(12, 0)),
    (time(14, 0), time(18, 0)),
)

# 全體公民法定節假日。調休連休（例如 2026-01-02、2026-02-20、2026-10-05）故意不在這裡。
STATUTORY_HOLIDAYS = {
    # 2026
    date(2026, 1, 1): "元旦",
    date(2026, 2, 16): "除夕",  # 臘月廿九
    date(2026, 2, 17): "正月初一",
    date(2026, 2, 18): "正月初二",
    date(2026, 2, 19): "正月初三",
    date(2026, 4, 5): "清明",
    date(2026, 5, 1): "勞動節",
    date(2026, 5, 2): "勞動節",
    date(2026, 6, 19): "端午",  # 五月初五
    date(2026, 9, 25): "中秋",  # 八月十五
    date(2026, 10, 1): "國慶",
    date(2026, 10, 2): "國慶",
    date(2026, 10, 3): "國慶",
    # 2027
    date(2027, 1, 1): "元旦",
    date(2027, 2, 5): "除夕",  # 國辦發明電〔2026〕10號寫明當日為除夕
    date(2027, 2, 6): "正月初一",
    date(2027, 2, 7): "正月初二",
    date(2027, 2, 8): "正月初三",
    date(2027, 4, 5): "清明",
    date(2027, 5, 1): "勞動節",
    date(2027, 5, 2): "勞動節",
    date(2027, 6, 9): "端午",  # 國辦通知當日只放這一天
    date(2027, 9, 15): "中秋",  # 國辦通知當日只放這一天
    date(2027, 10, 1): "國慶",
    date(2027, 10, 2): "國慶",
    date(2027, 10, 3): "國慶",
}


def is_statutory_holiday(day: date) -> bool:
    """北京時間曆日是否為全體公民法定節假日。"""
    return day in STATUTORY_HOLIDAYS


def is_deepseek_peak(moment: datetime) -> bool:
    """這個時刻呼叫 DeepSeek 模型是否會落在高峰計價。

    `moment` 必須帶時區。回傳 True 時不應發出會計費的 API 請求。
    """
    if moment.tzinfo is None:
        raise ValueError("moment 必須帶時區")

    beijing = moment.astimezone(BEIJING)
    if is_statutory_holiday(beijing.date()):
        return False
    if beijing.weekday() >= 5:
        return False

    clock = time(beijing.hour, beijing.minute, beijing.second, beijing.microsecond)
    return any(start <= clock < end for start, end in PEAK_WINDOWS)
