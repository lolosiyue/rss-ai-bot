"""DeepSeek 尖峰窗口、法定節假日，以及略過 API 的路徑。"""

import os
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from src.ai_summarizer import AISummarizer
from src.deepseek_pricing import BEIJING, STATUTORY_HOLIDAYS, is_deepseek_peak


ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


def beijing(year, month, day, hour, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=BEIJING)


def completion(text):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))]
    )


class ScriptedCompletions:
    def __init__(self, effects):
        self.effects = list(effects)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        effect = self.effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect


class ScriptedClient:
    def __init__(self, effects):
        self.completions = ScriptedCompletions(effects)
        self.chat = SimpleNamespace(completions=self.completions)

    @property
    def calls(self):
        return self.completions.calls


def scripted_clock(*moments):
    pending = list(moments)

    def clock():
        if not pending:
            raise AssertionError("clock 被多叫了一次")
        return pending.pop(0)

    return clock


class PeakWindowTest(unittest.TestCase):
    def test_weekday_peak_windows_are_half_open(self):
        # 2026-11-16 是週一。官方窗口：北京時間 09:00–12:00、14:00–18:00。
        cases = [
            (8, 59, 0, False),
            (9, 0, 0, True),
            (11, 59, 59, True),
            (12, 0, 0, False),
            (13, 59, 59, False),
            (14, 0, 0, True),
            (17, 59, 59, True),
            (18, 0, 0, False),
            (0, 23, 0, False),
        ]
        for hour, minute, second, peak in cases:
            moment = beijing(2026, 11, 16, hour, minute, second)
            self.assertEqual(
                is_deepseek_peak(moment),
                peak,
                f"{hour:02d}:{minute:02d}:{second:02d}",
            )

    def test_utc_windows_match_beijing(self):
        # UTC 01:00–04:00、06:00–10:00 對上北京時間同一曆日。
        self.assertTrue(is_deepseek_peak(datetime(2026, 11, 16, 1, 0, tzinfo=UTC)))
        self.assertTrue(is_deepseek_peak(datetime(2026, 11, 16, 3, 59, tzinfo=UTC)))
        self.assertFalse(is_deepseek_peak(datetime(2026, 11, 16, 4, 0, tzinfo=UTC)))
        self.assertFalse(is_deepseek_peak(datetime(2026, 11, 16, 5, 30, tzinfo=UTC)))
        self.assertTrue(is_deepseek_peak(datetime(2026, 11, 16, 6, 0, tzinfo=UTC)))
        self.assertTrue(is_deepseek_peak(datetime(2026, 11, 16, 9, 59, tzinfo=UTC)))
        self.assertFalse(is_deepseek_peak(datetime(2026, 11, 16, 10, 0, tzinfo=UTC)))

    def test_weekends_and_makeup_workdays_stay_off_peak(self):
        # 2026-11-14 週六、11-15 週日。補班日 1 月 4 日是週日，仍算週末。
        self.assertFalse(is_deepseek_peak(beijing(2026, 11, 14, 10, 0)))
        self.assertFalse(is_deepseek_peak(beijing(2026, 11, 15, 15, 0)))
        self.assertFalse(is_deepseek_peak(beijing(2026, 1, 4, 10, 0)))
        self.assertNotIn(datetime(2026, 1, 4).date(), STATUTORY_HOLIDAYS)

    def test_incident_was_peak_and_new_cron_is_off_peak(self):
        # 2026-11-17 排程晚了約 6 小時 40 分，11:39 JST = 02:39 UTC = 北京 10:39。
        incident = datetime(2026, 11, 17, 2, 39, tzinfo=UTC)
        self.assertTrue(is_deepseek_peak(incident))
        # cron 23 16 * * *：UTC 16:23 = 香港 00:23 / 東京 01:23（翌日）。
        scheduled = datetime(2026, 11, 17, 16, 23, tzinfo=UTC)
        self.assertEqual(scheduled.astimezone(BEIJING).hour, 0)
        self.assertEqual(scheduled.astimezone(BEIJING).minute, 23)
        tokyo = scheduled.astimezone(timezone(timedelta(hours=9)))
        self.assertEqual((tokyo.hour, tokyo.minute), (1, 23))
        self.assertFalse(is_deepseek_peak(scheduled))

    def test_naive_datetime_is_rejected(self):
        with self.assertRaises(ValueError):
            is_deepseek_peak(datetime(2026, 11, 16, 10, 0))


class StatutoryHolidayTest(unittest.TestCase):
    def test_statutory_weekdays_are_off_peak_all_day(self):
        holidays = [
            beijing(2026, 1, 1, 10, 0),  # 週四元旦
            beijing(2026, 2, 16, 10, 0),  # 週一除夕
            beijing(2026, 2, 19, 15, 30),  # 週四正月初三
            beijing(2026, 5, 1, 9, 0),  # 週五勞動節
            beijing(2026, 6, 19, 14, 0),  # 週五端午
            beijing(2026, 9, 25, 17, 59),  # 週五中秋
            beijing(2026, 10, 1, 10, 39),  # 週四國慶
            beijing(2026, 10, 2, 10, 0),  # 週五國慶
            beijing(2027, 2, 5, 11, 0),  # 週五除夕
            beijing(2027, 2, 8, 9, 0),  # 週一正月初三
            beijing(2027, 4, 5, 14, 0),  # 週一清明
            beijing(2027, 6, 9, 16, 0),  # 週三端午
            beijing(2027, 9, 15, 9, 30),  # 週三中秋
            beijing(2027, 10, 1, 10, 0),  # 週五國慶
        ]
        for moment in holidays:
            self.assertIn(moment.date(), STATUTORY_HOLIDAYS, moment.date())
            self.assertLess(moment.weekday(), 5, moment.date())
            self.assertFalse(is_deepseek_peak(moment), moment.isoformat())

    def test_adjusted_rest_days_are_not_holidays_and_stay_peak(self):
        # 國務院放假調休裡的連休，不是全體公民法定節假日。
        adjusted = [
            beijing(2026, 1, 2, 10, 0),  # 週五，元旦調休
            beijing(2026, 2, 20, 10, 0),  # 週五，正月初四
            beijing(2026, 2, 23, 15, 0),  # 週一，正月初七
            beijing(2026, 4, 6, 9, 0),  # 週一，清明連休
            beijing(2026, 5, 4, 14, 0),  # 週一，勞動節調休
            beijing(2026, 5, 5, 11, 0),  # 週二
            beijing(2026, 10, 5, 10, 39),  # 週一，國慶調休
            beijing(2026, 10, 7, 16, 0),  # 週三
            beijing(2027, 2, 9, 10, 0),  # 週二，正月初四
            beijing(2027, 2, 12, 15, 0),  # 週五，正月初七
            beijing(2027, 5, 3, 9, 0),  # 週一，勞動節調休
            beijing(2027, 10, 4, 14, 0),  # 週一，國慶調休
        ]
        for moment in adjusted:
            self.assertNotIn(moment.date(), STATUTORY_HOLIDAYS, moment.date())
            self.assertTrue(moment.weekday() < 5, moment.date())
            self.assertTrue(is_deepseek_peak(moment), moment.isoformat())

    def test_day_before_national_day_is_peak(self):
        # 2026-09-30 週三，國慶從 10 月 1 日才開始。
        moment = beijing(2026, 9, 30, 10, 0)
        self.assertTrue(is_deepseek_peak(moment))

    def test_unknown_year_is_not_treated_as_a_holiday(self):
        moment = datetime(2028, 6, 1, 10, 0, tzinfo=BEIJING)
        while moment.weekday() >= 5:
            moment += timedelta(days=1)
        self.assertNotIn(moment.date(), STATUTORY_HOLIDAYS)
        self.assertTrue(is_deepseek_peak(moment))


class ScheduleFileTest(unittest.TestCase):
    def test_workflow_cron_is_utc_1623_without_manual_dispatch(self):
        text = (ROOT / ".github" / "workflows" / "rss-bot.yml").read_text(encoding="utf-8")
        self.assertIn("cron: '23 16 * * *'", text)
        self.assertNotIn("cron: '0 20 * * *'", text)
        self.assertNotIn("workflow_dispatch", text)
        self.assertIn("UTC", text)
        self.assertIn("東京", text)
        self.assertIn("香港", text)


class SkipPathTest(unittest.TestCase):
    def test_peak_skips_the_api_and_does_not_consume_the_article(self):
        client = ScriptedClient([completion("不該被用到")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(datetime(2026, 11, 17, 2, 39, tzinfo=UTC)),
        )
        summary = bot.summarize("標題", "<p>正文</p>")
        self.assertIsNone(summary)
        self.assertEqual(client.calls, 0)
        self.assertEqual(bot.peak_skip_count, 1)
        self.assertEqual(bot.success_count, 0)
        self.assertEqual(bot.fail_count, 0)

    def test_off_peak_calls_the_api(self):
        client = ScriptedClient([completion("  繁體摘要  ")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(datetime(2026, 11, 17, 16, 23, tzinfo=UTC)),
        )
        summary = bot.summarize("標題", "正文")
        self.assertEqual(summary, "繁體摘要")
        self.assertEqual(client.calls, 1)
        self.assertEqual(bot.success_count, 1)
        self.assertEqual(bot.peak_skip_count, 0)

    def test_statutory_holiday_during_peak_clock_still_calls(self):
        # 2026-10-01 10:00 北京時間 = 02:00 UTC，國慶整天離峰。
        client = ScriptedClient([completion("國慶摘要")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(datetime(2026, 10, 1, 2, 0, tzinfo=UTC)),
        )
        self.assertEqual(bot.summarize("標題", "正文"), "國慶摘要")
        self.assertEqual(client.calls, 1)

    def test_each_article_rechecks_instead_of_using_the_job_start(self):
        client = ScriptedClient([completion("第一篇"), completion("不該呼叫")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(
                datetime(2026, 11, 18, 0, 30, tzinfo=UTC),  # 離峰
                datetime(2026, 11, 18, 2, 0, tzinfo=UTC),  # 已進入尖峰
            ),
        )
        self.assertEqual(bot.summarize("一", "正文一"), "第一篇")
        self.assertIsNone(bot.summarize("二", "正文二"))
        self.assertEqual(client.calls, 1)
        self.assertEqual(bot.peak_skip_count, 1)

    def test_retry_rechecks_and_does_not_call_during_peak(self):
        client = ScriptedClient([TimeoutError("逾時"), completion("不該重試")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(
                datetime(2026, 11, 18, 0, 30, tzinfo=UTC),
                datetime(2026, 11, 18, 1, 5, tzinfo=UTC),
            ),
        )
        summary = bot.summarize("標題", "正文")
        self.assertIsNone(summary)
        self.assertEqual(client.calls, 1)
        self.assertEqual(bot.peak_skip_count, 1)
        self.assertEqual(bot.fail_count, 0)

    def test_off_peak_retry_then_success(self):
        client = ScriptedClient([TimeoutError("逾時"), completion("重試成功")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(
                datetime(2026, 11, 18, 0, 30, tzinfo=UTC),
                datetime(2026, 11, 18, 0, 31, tzinfo=UTC),
            ),
        )
        self.assertEqual(bot.summarize("標題", "正文"), "重試成功")
        self.assertEqual(client.calls, 2)
        self.assertEqual(bot.peak_skip_count, 0)

    def test_api_failure_uses_local_summary_without_another_peak_call(self):
        client = ScriptedClient([TimeoutError("一次"), TimeoutError("兩次")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(
                datetime(2026, 11, 18, 0, 30, tzinfo=UTC),
                datetime(2026, 11, 18, 0, 31, tzinfo=UTC),
            ),
        )
        content = "本地後備不會送給 DeepSeek。"
        summary = bot.summarize("標題", f"<b>{content}</b>")
        self.assertEqual(summary, content)
        self.assertEqual(client.calls, 2)
        self.assertEqual(bot.fail_count, 1)
        self.assertEqual(bot.peak_skip_count, 0)

    def test_empty_completion_does_not_retry(self):
        client = ScriptedClient([completion("   "), completion("不該再叫")])
        bot = AISummarizer(
            client=client,
            clock=scripted_clock(datetime(2026, 11, 18, 0, 30, tzinfo=UTC)),
        )
        summary = bot.summarize("標題", "後備正文")
        self.assertEqual(summary, "後備正文")
        self.assertEqual(client.calls, 1)
        self.assertEqual(bot.fail_count, 1)

    def test_sdk_retries_stay_off_so_the_gate_sees_every_attempt(self):
        os.environ["DEEPSEEK_API_KEY"] = "test-key"
        bot = AISummarizer()
        self.assertEqual(bot.client.max_retries, 0)


if __name__ == "__main__":
    unittest.main()
