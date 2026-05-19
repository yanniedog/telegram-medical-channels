"""Build multi-sheet Excel workbook for medical Telegram channel analysis."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(color="FFFFFF", bold=True)
YEAR_START, YEAR_END = 1985, 2030


def _write_headers(ws, headers: list[str], row: int = 1) -> None:
    for col, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=col, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center", wrap_text=True)


def _autosize(ws, widths: list[int]) -> None:
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def build_comprehensive_workbook(
    out_path: Path,
    analyses: list[Any],
    posts_rows: list[dict],
    excluded: list[dict],
    discovery_meta: dict,
    run_meta: dict,
    keywords_rows: list[dict] | None = None,
) -> None:
    wb = Workbook()

    # ---- 1. Channels_Fact (PRIMARY pivot source) ----
    ws = wb.active
    ws.title = "Channels_Fact"
    fact_headers = [
        "channel_key",
        "username",
        "title",
        "telegram_link",
        "subscribers",
        "scrape_source",
        "data_coverage_pct",
        "channel_created_proxy",
        "first_post_date",
        "last_ebook_date",
        "posts_scraped",
        "posts_total_in_sample",
        "ebook_posts",
        "link_only_posts",
        "pdf_count",
        "epub_count",
        "other_book_formats",
        "powerpoint_count",
        "apk_count",
        "audio_video_count",
        "unique_book_titles",
        "posts_per_day",
        "ebooks_per_day",
        "total_views_on_ebook_posts",
        "posts_per_avg_ebook_view",
        "uniqueness_score_0_100",
        "breadth_score_0_100",
        "channel_lang_1",
        "channel_lang_1_pct",
        "channel_lang_2",
        "channel_lang_2_pct",
        "channel_lang_3",
        "channel_lang_3_pct",
        "book_lang_1",
        "book_lang_1_pct",
        "book_lang_2",
        "book_lang_2_pct",
        "book_lang_3",
        "book_lang_3_pct",
        "specialty_top1",
        "specialty_top1_count",
        "specialty_top2",
        "specialty_top2_count",
        "specialty_top3",
        "specialty_top3_count",
        "region_top1",
        "region_top1_count",
        "pub_year_median",
        "pub_year_min",
        "pub_year_max",
        "top_keyword_1",
        "top_keyword_1_count",
        "top_keyword_2",
        "top_keyword_2_count",
        "top_keyword_3",
        "top_keyword_3_count",
        "unique_tokens",
        "total_tokens",
        "agent_specialty_tags",
        "specialty_keyword_hits_json",
        "notes",
    ]
    _write_headers(ws, fact_headers)

    def _lang_parts(json_str: str) -> list[tuple[str, int]]:
        try:
            items = json.loads(json_str or "[]")
            return [(a, b) for a, b in items[:3]]
        except json.JSONDecodeError:
            return []

    def _top_from_json(json_str: str, n: int = 3) -> list[tuple[str, int]]:
        try:
            d = json.loads(json_str or "{}")
            if isinstance(d, dict):
                return sorted(d.items(), key=lambda x: -x[1])[:n]
        except json.JSONDecodeError:
            pass
        return []

    for row_idx, a in enumerate(analyses, 2):
        meta = discovery_meta.get(a.username.lower(), {})
        ch_langs = _lang_parts(a.channel_langs_top3)
        bk_langs = _lang_parts(a.book_langs_top3)
        specs = _top_from_json(a.specialty_json, 3)
        regions = _top_from_json(a.region_json, 1)
        years_d = json.loads(a.year_histogram_json or "{}")
        years_nums = [int(y) for y in years_d.keys()] if years_d else []
        med_year = sorted(years_nums)[len(years_nums) // 2] if years_nums else None

        total_ch = sum(c for _, c in ch_langs) or 1
        total_bk = sum(c for _, c in bk_langs) or 1

        values = [
            a.username.lower(),
            a.username,
            meta.get("title"),
            f"https://t.me/{a.username}",
            a.subscribers,
            a.scrape_source,
            a.data_coverage_pct,
            a.channel_created_proxy,
            a.first_post_date,
            a.last_ebook_date,
            a.posts_scraped,
            a.posts_total,
            a.ebook_posts,
            a.link_only_posts,
            a.pdf_count,
            a.epub_count,
            a.other_book_count,
            a.ppt_count,
            a.apk_count,
            a.av_count,
            a.unique_titles,
            a.posts_per_day,
            a.ebooks_per_day,
            a.total_views_ebooks,
            a.post_to_ebook_view_ratio,
            a.uniqueness_score,
            a.breadth_score,
        ]
        for i in range(3):
            if i < len(ch_langs):
                lang, cnt = ch_langs[i]
                values.extend([lang, round(100 * cnt / total_ch, 1)])
            else:
                values.extend([None, None])
        for i in range(3):
            if i < len(bk_langs):
                lang, cnt = bk_langs[i]
                values.extend([lang, round(100 * cnt / total_bk, 1)])
            else:
                values.extend([None, None])
        for i in range(3):
            if i < len(specs):
                values.extend([specs[i][0], specs[i][1]])
            else:
                values.extend([None, None])
        if regions:
            values.extend([regions[0][0], regions[0][1]])
        else:
            values.extend([None, None])
        agent_tags = meta.get("agent_specialty_tags") or []
        if isinstance(agent_tags, list):
            agent_tags_str = ", ".join(agent_tags)
        else:
            agent_tags_str = str(agent_tags)
        values.extend(
            [
                med_year,
                min(years_nums) if years_nums else None,
                max(years_nums) if years_nums else None,
                a.top_keyword_1,
                a.top_keyword_1_count,
                a.top_keyword_2,
                a.top_keyword_2_count,
                a.top_keyword_3,
                a.top_keyword_3_count,
                a.unique_tokens,
                a.total_tokens,
                agent_tags_str or a.agent_specialty_tags_json,
                a.specialty_keyword_hits_json,
                a.notes,
            ]
        )
        for col, val in enumerate(values, 1):
            ws.cell(row=row_idx, column=col, value=val)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(fact_headers))}{len(analyses) + 1}"
    _autosize(ws, [14] + [12] * (len(fact_headers) - 1))

    # ---- 2. Posts_Fact (long, pivot-ready) ----
    ws2 = wb.create_sheet("Posts_Fact")
    post_headers = [
        "channel_key",
        "username",
        "post_id",
        "post_datetime_utc",
        "is_ebook",
        "is_forward",
        "is_link_only",
        "views",
        "format_primary",
        "file_names",
        "normalized_title",
        "specialty",
        "pub_year",
        "pub_region",
        "text_excerpt",
        "scrape_source",
    ]
    _write_headers(ws2, post_headers)
    from content_analyzer import (
        classify_region,
        classify_specialties,
        extract_year,
        is_direct_ebook_post,
        is_ebook_post,
        is_link_only_channel_post,
        normalize_title,
    )

    pr = 2
    for p in posts_rows:
        text = (p.get("text") or "")[:500]
        fn = p.get("file_names") or []
        exts = p.get("file_extensions") or []
        fmt = exts[0] if exts else ("pdf" if ".pdf" in text.lower() else "other")
        nt = normalize_title(p.get("text") or "", fn)
        specs = classify_specialties(text + " " + " ".join(fn))
        ws2.append(
            [
                (p.get("channel") or p.get("channel_username", "")).lower(),
                p.get("channel") or p.get("channel_username"),
                p.get("post_id"),
                p.get("datetime_utc"),
                is_direct_ebook_post(p),
                p.get("is_forward"),
                is_link_only_channel_post(p),
                p.get("views"),
                fmt,
                "; ".join(fn)[:300],
                nt[:200],
                specs[0] if specs else None,
                extract_year(text + " " + " ".join(fn)),
                classify_region(text),
                text[:240],
                p.get("_source", "tme"),
            ]
        )
        pr += 1
    ws2.freeze_panes = "A2"

    # ---- Keywords_Long (pivot-ready) ----
    ws_kw = wb.create_sheet("Keywords_Long")
    _write_headers(ws_kw, ["channel_key", "username", "rank", "keyword", "count", "type"])
    for row in keywords_rows or []:
        ws_kw.append(
            [
                row.get("channel_key"),
                row.get("username"),
                row.get("rank"),
                row.get("keyword"),
                row.get("count"),
                row.get("type"),
            ]
        )
    ws_kw.freeze_panes = "A2"

    # ---- Specialty keyword hits (taxonomy) ----
    ws_skh = wb.create_sheet("Specialty_Keyword_Hits")
    _write_headers(ws_skh, ["channel_key", "username", "taxonomy_key", "hit_count"])
    for a in analyses:
        try:
            hits = json.loads(a.specialty_keyword_hits_json or "{}")
        except json.JSONDecodeError:
            hits = {}
        for k, v in hits.items():
            ws_skh.append([a.username.lower(), a.username, k, v])

    # ---- 3. Specialty_Long ----
    ws3 = wb.create_sheet("Specialty_Long")
    _write_headers(ws3, ["channel_key", "username", "specialty", "post_count"])
    r = 2
    for a in analyses:
        try:
            spec_d = json.loads(a.specialty_json or "{}")
        except json.JSONDecodeError:
            continue
        for sp, cnt in spec_d.items():
            ws3.append([a.username.lower(), a.username, sp, cnt])
            r += 1

    # ---- 4. Language_Long ----
    ws4 = wb.create_sheet("Language_Long")
    _write_headers(ws4, ["channel_key", "username", "language_scope", "rank", "language", "count"])
    for a in analyses:
        for scope, json_s in (("channel", a.channel_langs_top3), ("book", a.book_langs_top3)):
            try:
                items = json.loads(json_s or "[]")
            except json.JSONDecodeError:
                items = []
            for rank, (lang, cnt) in enumerate(items, 1):
                ws4.append([a.username.lower(), a.username, scope, rank, lang, cnt])

    # ---- 5. PubYear_Long ----
    ws5 = wb.create_sheet("PubYear_Long")
    _write_headers(ws5, ["channel_key", "username", "pub_year", "ebook_post_count"])
    for a in analyses:
        try:
            yd = json.loads(a.year_histogram_json or "{}")
        except json.JSONDecodeError:
            yd = {}
        for year, cnt in sorted(yd.items(), key=lambda x: int(x[0])):
            ws5.append([a.username.lower(), a.username, int(year), cnt])

    # ---- 6. PubRegion_Long ----
    ws6 = wb.create_sheet("PubRegion_Long")
    _write_headers(ws6, ["channel_key", "username", "region", "ebook_post_count"])
    for a in analyses:
        try:
            rd = json.loads(a.region_json or "{}")
        except json.JSONDecodeError:
            rd = {}
        for region, cnt in rd.items():
            ws6.append([a.username.lower(), a.username, region, cnt])

    # ---- 7. Format_Long ----
    ws7 = wb.create_sheet("Format_Long")
    _write_headers(ws7, ["channel_key", "username", "format", "count"])
    fmt_map = [
        ("pdf", "pdf_count"),
        ("epub", "epub_count"),
        ("other_book", "other_book_count"),
        ("powerpoint", "ppt_count"),
        ("apk", "apk_count"),
        ("audio_video", "av_count"),
    ]
    for a in analyses:
        for fmt, attr in fmt_map:
            ws7.append([a.username.lower(), a.username, fmt, getattr(a, attr)])

    # ---- 8. Uniqueness_Matrix ----
    ws8 = wb.create_sheet("Scores_Ranking")
    _write_headers(
        ws8,
        [
            "rank_by_breadth",
            "username",
            "subscribers",
            "ebook_posts",
            "unique_titles",
            "uniqueness_score",
            "breadth_score",
            "scrape_source",
        ],
    )
    ranked = sorted(analyses, key=lambda x: -(x.breadth_score or 0))
    for i, a in enumerate(ranked, 2):
        ws8.append(
            [
                i - 1,
                a.username,
                a.subscribers,
                a.ebook_posts,
                a.unique_titles,
                a.uniqueness_score,
                a.breadth_score,
                a.scrape_source,
            ]
        )

    # ---- 9. Channels_Excluded ----
    ws9 = wb.create_sheet("Channels_Excluded")
    _write_headers(ws9, ["username", "subscribers", "exclusion_reason"])
    for ex in excluded:
        ws9.append([ex.get("username"), ex.get("subscribers"), ex.get("reason")])

    # ---- 10. AU_Doctors ----
    ws10 = wb.create_sheet("AU_Doctors")
    _write_headers(
        ws10,
        ["username", "subscribers", "amc_related_posts", "uk_formulary_posts", "au_score_notes"],
    )
    import re

    for a in analyses:
        amc = uk = 0
        path = Path("data/posts") / f"{a.username.lower()}.json"
        if path.exists():
            posts = json.loads(path.read_text(encoding="utf-8"))
            for p in posts:
                t = (p.get("text") or "").lower()
                if re.search(r"\bamc\b|\bmccqe\b|\bracgp\b|\baustralian medical", t):
                    amc += 1
                if re.search(r"\bbnf\b|british pharmacopoeia|therapeutic guidelines", t):
                    uk += 1
        note = "High" if amc else "General medical library"
        ws10.append([a.username, a.subscribers, amc, uk, note])

    # ---- 11. Methodology ----
    ws11 = wb.create_sheet("Methodology")
    lines = [
        "Medical Telegram Channel Comprehensive Analysis",
        f"Generated: {run_meta.get('generated_at')}",
        f"Minimum subscribers: {run_meta.get('min_subscribers')}",
        f"Channels in fact table: {run_meta.get('channels_analyzed')}",
        "",
        "DATA SOURCES",
        "- Public Telegram web previews (t.me/s/...) with full pagination where enabled",
        "- TGStat public channel pages (~20 recent posts) when preview disabled",
        "- Lyzem search + seed list for discovery",
        "",
        "INCLUSION RULE (ebooks)",
        "- Only channels that post PDF/EPUB (etc.) as Telegram file attachments are included.",
        "- External catalog links (subscription sites, storefronts, Google Drive teasers) are excluded.",
        "- Example excluded pattern: @ophthbooks linking only to ophthbooks.com/More.aspx.",
        "",
        "LIMITATIONS (read before pivoting)",
        "- Channels without public web preview have partial samples only (data_coverage_pct < 100).",
        "- Full historical archive requires Telegram API (MTProto) credentials — not used in this run.",
        "- Publication year/region inferred from post text heuristics, not ISBN metadata.",
        "- Download counts are NOT public; posts_per_avg_ebook_view uses view counts as proxy.",
        "- Channel created date uses first scraped post date as proxy when creation date unavailable.",
        "- Uniqueness score = % of normalized titles that appear on only one channel in this dataset.",
        "- Breadth score = composite of unique titles, specialty diversity, and ebook volume (0-100).",
        "",
        "PIVOT TABLE TIPS",
        "- Use Channels_Fact as primary; join Specialty_Long / PubYear_Long on channel_key.",
        "- Filter scrape_source = tme_full_preview for highest-confidence metrics.",
    ]
    for i, line in enumerate(lines, 1):
        ws11.cell(row=i, column=1, value=line)
    ws11.column_dimensions["A"].width = 110

    # Run metadata appended to Methodology sheet
    mr = ws11.max_row + 2
    ws11.cell(row=mr, column=1, value="--- Run metadata ---")
    for i, (k, v) in enumerate(run_meta.items(), mr + 1):
        ws11.cell(row=i, column=1, value=k)
        ws11.cell(row=i, column=2, value=str(v))

    # ---- PubYear wide matrix (histogram pivot source) ----
    # ---- Title catalog (uniqueness audit) ----
    ws_titles = wb.create_sheet("Title_Catalog")
    _write_headers(
        ws_titles,
        ["channel_key", "username", "normalized_title", "format_primary", "pub_year", "specialty"],
    )
    tr = 2
    for p in posts_rows:
        from content_analyzer import classify_specialties, extract_year, normalize_title

        text = (p.get("text") or "") + " " + " ".join(p.get("file_names") or [])
        nt = normalize_title(p.get("text") or "", p.get("file_names") or [])
        if len(nt) < 8:
            continue
        exts = p.get("file_extensions") or []
        fmt = exts[0] if exts else "unknown"
        specs = classify_specialties(text)
        ws_titles.append(
            [
                (p.get("channel") or p.get("channel_username", "")).lower(),
                p.get("channel") or p.get("channel_username"),
                nt,
                fmt,
                extract_year(text),
                specs[0],
            ]
        )
        tr += 1

    ws_hist = wb.create_sheet("PubYear_Matrix")
    year_cols = list(range(YEAR_START, YEAR_END + 1))
    _write_headers(ws_hist, ["channel_key", "username"] + [str(y) for y in year_cols])
    for row_idx, a in enumerate(analyses, 2):
        try:
            yd = {int(k): v for k, v in json.loads(a.year_histogram_json or "{}").items()}
        except (json.JSONDecodeError, ValueError):
            yd = {}
        row = [a.username.lower(), a.username] + [yd.get(y, 0) for y in year_cols]
        for col, val in enumerate(row, 1):
            ws_hist.cell(row=row_idx, column=col, value=val)

    wb.save(out_path)
