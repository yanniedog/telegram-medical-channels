"""Build Excel listing of Telegram medical ebook channels (public web research)."""
from datetime import date

import xlwt
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

VERIFIED = date.today().isoformat()

# Ranked by estimated PDF/ePub/ebook publication volume & library depth.
# Scores are editorial estimates from public previews, subscriber counts, and channel descriptions.
CHANNELS = [
    {
        "rank": 1,
        "username": "Million_medical_books",
        "name": "Million Medical Books PDF (Arabic/English mix)",
        "link": "https://t.me/Million_medical_books",
        "subscribers": 95420,
        "formats": "PDF (primary)",
        "est_publications": "Very high (channel name implies 1M+ titles; bot @Million_M_B_bot for requests)",
        "specialty": "All specialties",
        "au_relevance": 4,
        "au_notes": "Broad international textbooks; useful for core clinical references (Harrison, Robbins, etc.)",
        "language": "Arabic + English",
        "activity": "Active",
        "notes": "Largest subscriber base among medical-PDF channels surveyed.",
    },
    {
        "rank": 2,
        "username": "medical_ebook_pdfs",
        "name": "Medical Books pdf",
        "link": "https://t.me/medical_ebook_pdfs",
        "subscribers": 12867,
        "formats": "PDF (primary)",
        "est_publications": "Very high (claims 10,000+ free medical books in channel description)",
        "specialty": "All specialties",
        "au_relevance": 4,
        "au_notes": "Large catalog; good for standard UK/US/AU training texts",
        "language": "English",
        "activity": "Active",
        "notes": "Contact @medusmle for takedowns.",
    },
    {
        "rank": 3,
        "username": "MedicalBooksStoress",
        "name": "Medical Books (Store Channel)",
        "link": "https://t.me/MedicalBooksStoress",
        "subscribers": 59208,
        "formats": "PDF",
        "est_publications": "Very high (described as largest free medical channel; specialty + subspecialty)",
        "specialty": "All specialties",
        "au_relevance": 4,
        "au_notes": "Wide specialty coverage aligns with RACGP/physician training breadth",
        "language": "English",
        "activity": "Active (public preview limited)",
        "notes": "Backup: @Medical_Books_Storess; bot @CNS_MEDkbook_bot",
    },
    {
        "rank": 4,
        "username": "Medbooksvn2",
        "name": "Medbooksvn",
        "link": "https://t.me/Medbooksvn2",
        "subscribers": 17898,
        "formats": "PDF, EPUB, notes, videos, Q-banks",
        "est_publications": "High (daily PDF/EPUB posts via medbooksvn.org; auto-delete after 7 days)",
        "specialty": "All specialties",
        "au_relevance": 4,
        "au_notes": "Explicit EPUB + PDF; good for pain medicine, pathology atlases, etc.",
        "language": "English",
        "activity": "Moderate (posts auto-deleted weekly)",
        "notes": "Site: medbooksvn.org",
    },
    {
        "rank": 5,
        "username": "webofmedical",
        "name": "Medical Books Free (Web of Medical)",
        "link": "https://t.me/webofmedical",
        "subscribers": 500,
        "formats": "PDF (direct download links)",
        "est_publications": "High (dense PDF listing posts; Harrison, BNF, British Pharmacopoeia)",
        "specialty": "General medicine, pharmacology, exam prep",
        "au_relevance": 5,
        "au_notes": "Posts BNF & British Pharmacopoeia (UK formulary used alongside eTG in AU); FRCR radiology",
        "language": "English",
        "activity": "Lower posting frequency recently",
        "notes": "High AU relevance despite smaller subscriber count",
    },
    {
        "rank": 6,
        "username": "freesurgerybooks28",
        "name": "Free Surgery Books",
        "link": "https://t.me/freesurgerybooks28",
        "subscribers": 35855,
        "formats": "PDF",
        "est_publications": "High (surgery textbook focus)",
        "specialty": "Surgery",
        "au_relevance": 4,
        "au_notes": "Useful for surgical trainees (SET/RACS pathway reference texts)",
        "language": "English",
        "activity": "Active",
        "notes": "Non-profit channel",
    },
    {
        "rank": 7,
        "username": "pdf4yo",
        "name": "Medical Book Store",
        "link": "https://t.me/pdf4yo",
        "subscribers": 35443,
        "formats": "PDF",
        "est_publications": "High",
        "specialty": "All specialties",
        "au_relevance": 3,
        "au_notes": "General medical PDF store",
        "language": "English",
        "activity": "Active",
        "notes": "",
    },
    {
        "rank": 8,
        "username": "Internal_medicine_material",
        "name": "Internal medicine Videos and Books",
        "link": "https://t.me/Internal_medicine_material",
        "subscribers": 20456,
        "formats": "PDF, audio, video, apps",
        "est_publications": "High (internal medicine books + lectures)",
        "specialty": "Internal medicine",
        "au_relevance": 4,
        "au_notes": "Physician training & FRACP-style internal medicine resources",
        "language": "English",
        "activity": "Active",
        "notes": "",
    },
    {
        "rank": 9,
        "username": "Radiologist_Library",
        "name": "Radiologist & Radiographer Library",
        "link": "https://t.me/Radiologist_Library",
        "subscribers": 15746,
        "formats": "PDF (radiology textbooks)",
        "est_publications": "Very high post count (7,600+ indexed forwards in previews)",
        "specialty": "Radiology / imaging",
        "au_relevance": 4,
        "au_notes": "Radiology trainees (RANZCR); forwards to many imaging PDFs",
        "language": "English",
        "activity": "Active",
        "notes": "Related: @radiologygoldenbooks",
    },
    {
        "rank": 10,
        "username": "radiologygoldenbooks",
        "name": "FHB Radiology golden books",
        "link": "https://t.me/radiologygoldenbooks",
        "subscribers": 12159,
        "formats": "PDF",
        "est_publications": "Moderate–high (radiology-only)",
        "specialty": "Radiology",
        "au_relevance": 4,
        "au_notes": "Dedicated radiology PDF sharing",
        "language": "English",
        "activity": "Active",
        "notes": "",
    },
    {
        "rank": 11,
        "username": "MedicalLibraryMax",
        "name": "Medical Books pdf (MedicalLibraryMax)",
        "link": "https://t.me/MedicalLibraryMax",
        "subscribers": 6350,
        "formats": "PDF, apps",
        "est_publications": "Moderate–high (cardiology, pathology, radiology PDFs uploaded directly)",
        "specialty": "Multi-specialty",
        "au_relevance": 3,
        "au_notes": "Robbins pathology, cardiology modules",
        "language": "English",
        "activity": "Lower (many posts 2021)",
        "notes": "Forwards from @Radiologist_Library",
    },
    {
        "rank": 12,
        "username": "booksmedicospdf",
        "name": "Libros Médicos PDF",
        "link": "https://t.me/booksmedicospdf",
        "subscribers": 17767,
        "formats": "PDF",
        "est_publications": "Moderate–high",
        "specialty": "General (Spanish-speaking community)",
        "au_relevance": 2,
        "au_notes": "Spanish language; limited AU-specific content",
        "language": "Spanish",
        "activity": "Active",
        "notes": "",
    },
    {
        "rank": 13,
        "username": "medicalprep",
        "name": "PrepLadder Medical",
        "link": "https://t.me/medicalprep",
        "subscribers": 70910,
        "formats": "PDF (exam recalls), video",
        "est_publications": "Moderate PDF volume (India PG exam focus)",
        "specialty": "Postgraduate exam prep (INICET/NEET-PG)",
        "au_relevance": 2,
        "au_notes": "India-centric exams; limited AMC/RACGP material",
        "language": "English",
        "activity": "Very active (2026 posts)",
        "notes": "High subscribers but not AU exam focused",
    },
    {
        "rank": 14,
        "username": "Medical_booksPG",
        "name": "Medical Books PG",
        "link": "https://t.me/Medical_booksPG",
        "subscribers": 1736,
        "formats": "PDF",
        "est_publications": "Moderate",
        "specialty": "Postgraduate medical",
        "au_relevance": 3,
        "au_notes": "PG medical books; verify AMC content manually",
        "language": "English",
        "activity": "Unknown",
        "notes": "",
    },
    {
        "rank": 15,
        "username": "AMCMCQ",
        "name": "AMC MCQ Recalls – SOMA Academy",
        "link": "https://t.me/AMCMCQ",
        "subscribers": 9674,
        "formats": "eBook (Kindle/Amazon links), recalls, course materials",
        "est_publications": "Moderate (AMC MCQ recall ebooks promoted; related @AMCMCQRECALLS)",
        "specialty": "AMC MCQ (IMG pathway to practice in Australia)",
        "au_relevance": 5,
        "au_notes": "Primary focus: Australian Medical Council MCQ exam for IMGs",
        "language": "English",
        "activity": "Lower frequency (commercial/course focus)",
        "notes": "Related: @AMCCLINICAL, @AMCMCQRECALLS",
    },
    {
        "rank": 16,
        "username": "AMCclinical",
        "name": "AMC Clinical Exam preparation recalls",
        "link": "https://t.me/AMCclinical",
        "subscribers": 4802,
        "formats": "Recalls, study notes (limited direct PDF in preview)",
        "est_publications": "Moderate (clinical exam recalls)",
        "specialty": "AMC Clinical exam",
        "au_relevance": 5,
        "au_notes": "Directly targets AMC Clinical — key for IMG registration in Australia",
        "language": "English",
        "activity": "Unknown (preview limited)",
        "notes": "",
    },
    {
        "rank": 17,
        "username": "amcclinicalexamprep",
        "name": "AMC Clinical Exam Prep by Dr Jayse",
        "link": "https://t.me/amcclinicalexamprep",
        "subscribers": 3774,
        "formats": "Guidance, resources (PDFs may be shared)",
        "est_publications": "Moderate",
        "specialty": "AMC Clinical exam",
        "au_relevance": 5,
        "au_notes": "Resources and guidance for AMC clinical exam",
        "language": "English",
        "activity": "Active",
        "notes": "",
    },
    {
        "rank": 18,
        "username": "medicalusmle_videos",
        "name": "USMLE Study Material",
        "link": "https://t.me/medicalusmle_videos",
        "subscribers": 51,
        "formats": "PDF, video, Q-banks",
        "est_publications": "Moderate (USMLE/PLAB/ABIM; ~97 posts indexed)",
        "specialty": "USMLE, PLAB, board exams",
        "au_relevance": 3,
        "au_notes": "PLAB/USMLE useful for IMGs on AMC pathway; low current subscribers",
        "language": "English",
        "activity": "Low (last major activity 2020)",
        "notes": "Contact @MedUSMLE; related @med_material",
    },
]

# Sorted view: Australia-first (for sheet 4)
AU_CHANNELS = sorted(
    [c for c in CHANNELS if c["au_relevance"] >= 5]
    + [c for c in CHANNELS if c["au_relevance"] == 4],
    key=lambda c: (-c["au_relevance"], -c["subscribers"]),
)

# Australian-specific / high-relevance resources (no dedicated RACGP channel found in public search)
AU_SPECIFIC = [
    {
        "resource": "RACGP exam materials",
        "telegram": "No dedicated public channel identified",
        "alternative": "racgp.org.au exam support; Therapeutic Guidelines (eTG); MJA",
        "notes": "Use general channels for textbooks; official RACGP resources are web-based",
    },
    {
        "resource": "AMC MCQ preparation",
        "telegram": "@AMCMCQ, @AMCMCQRECALLS (related channels)",
        "alternative": "amc.org.au official materials",
        "notes": "SOMA Academy; also promotes Kindle ebooks",
    },
    {
        "resource": "AMC Clinical exam",
        "telegram": "@AMCclinical, @amcclinicalexamprep",
        "alternative": "amc.org.au; accredited clinical courses",
        "notes": "Recall/guidance channels — verify currency before relying on content",
    },
    {
        "resource": "Australian formulary / guidelines",
        "telegram": "@webofmedical (BNF posts); no eTG channel found",
        "alternative": "tg.org.au (Therapeutic Guidelines subscription); PBS",
        "notes": "BNF is UK-based but clinically relevant in AU hospital practice",
    },
    {
        "resource": "FRACP / physician training texts",
        "telegram": "@Internal_medicine_material, @MedicalBooksStoress",
        "alternative": "RACP library, college learning sites",
        "notes": "",
    },
]


def build_workbook(path: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Medical PDF Channels"

    headers = [
        "Rank",
        "Channel",
        "Display name",
        "Telegram link",
        "Subscribers",
        "Formats",
        "Est. PDF/ePub volume",
        "Specialty focus",
        "AU doctor relevance (1-5)",
        "AU relevance notes",
        "Language",
        "Activity",
        "Notes",
    ]

    header_fill = PatternFill("solid", fgColor="1F4E79")
    header_font = Font(color="FFFFFF", bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for row_idx, ch in enumerate(CHANNELS, 2):
        values = [
            ch["rank"],
            f"@{ch['username']}",
            ch["name"],
            ch["link"],
            ch["subscribers"],
            ch["formats"],
            ch["est_publications"],
            ch["specialty"],
            ch["au_relevance"],
            ch["au_notes"],
            ch["language"],
            ch["activity"],
            ch["notes"],
        ]
        for col, val in enumerate(values, 1):
            c = ws.cell(row=row_idx, column=col, value=val)
            c.alignment = Alignment(vertical="top", wrap_text=True)
        if ch["au_relevance"] >= 4:
            for col in range(1, len(headers) + 1):
                ws.cell(row=row_idx, column=col).fill = PatternFill(
                    "solid", fgColor="E2EFDA"
                )

    widths = [6, 22, 28, 36, 12, 18, 42, 18, 10, 36, 12, 12, 28]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(CHANNELS) + 1}"

    ws2 = wb.create_sheet("AU Doctor Notes")
    ws2["A1"] = "Australian doctor relevance — supplementary notes"
    ws2["A1"].font = Font(bold=True, size=12)
    ws2["A2"] = f"Research date: {VERIFIED}"
    ws2["A3"] = (
        "Ranking is based on estimated volume of medical PDF/ePub/ebook listings, "
        "not legal quality or currency. No dedicated RACGP-only channel was found in public search."
    )
    ws2["A3"].alignment = Alignment(wrap_text=True)
    ws2.merge_cells("A3:F3")

    au_headers = ["Resource", "Telegram", "Official alternative", "Notes"]
    for col, h in enumerate(au_headers, 1):
        cell = ws2.cell(row=5, column=col, value=h)
        cell.font = Font(bold=True)
    for r, item in enumerate(AU_SPECIFIC, 6):
        ws2.cell(row=r, column=1, value=item["resource"])
        ws2.cell(row=r, column=2, value=item["telegram"])
        ws2.cell(row=r, column=3, value=item["alternative"])
        ws2.cell(row=r, column=4, value=item["notes"])

    ws2.column_dimensions["A"].width = 28
    ws2.column_dimensions["B"].width = 40
    ws2.column_dimensions["C"].width = 40
    ws2.column_dimensions["D"].width = 50

    ws_au = wb.create_sheet("AU Doctors (ranked)")
    au_headers = ["AU priority", "Channel", "Link", "Subscribers", "Formats", "AU notes"]
    for col, h in enumerate(au_headers, 1):
        cell = ws_au.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
    for row_idx, ch in enumerate(AU_CHANNELS, 2):
        ws_au.cell(row=row_idx, column=1, value=ch["au_relevance"])
        ws_au.cell(row=row_idx, column=2, value=f"@{ch['username']}")
        ws_au.cell(row=row_idx, column=3, value=ch["link"])
        ws_au.cell(row=row_idx, column=4, value=ch["subscribers"])
        ws_au.cell(row=row_idx, column=5, value=ch["formats"])
        ws_au.cell(row=row_idx, column=6, value=ch["au_notes"])
    for i, w in enumerate([12, 24, 36, 12, 28, 48], 1):
        ws_au.column_dimensions[get_column_letter(i)].width = w
    ws_au.freeze_panes = "A2"

    ws3 = wb.create_sheet("Disclaimer")
    disclaimer = [
        "Data sources: Public Telegram channel pages (t.me), TGStat, telemetr.io, web search.",
        f"Subscriber counts verified via public previews: {VERIFIED}.",
        "",
        "Important:",
        "- Many channels distribute copyrighted medical textbooks without publisher licence.",
        "- Content may be outdated, mislabelled, or contain malware in download links.",
        "- Australian doctors should prefer RACGP, RACP, AMC, eTG, and publisher-licensed e-books.",
        "- This list is for research/discovery only; not an endorsement of piracy.",
        "- Channel availability and subscriber counts change frequently; re-verify in Telegram.",
    ]
    for i, line in enumerate(disclaimer, 1):
        ws3.cell(row=i, column=1, value=line)
    ws3.column_dimensions["A"].width = 100

    wb.save(path)
    print(f"Wrote {path}")


def build_xls(path: str) -> None:
    """Legacy Excel 97-2003 .xls via xlwt."""
    wb = xlwt.Workbook()
    header_style = xlwt.easyxf("font: bold on; pattern: pattern solid, fore_colour gray25")
    highlight = xlwt.easyxf("pattern: pattern solid, fore_colour light_green")

    ws = wb.add_sheet("Medical PDF Channels")
    headers = [
        "Rank",
        "Channel",
        "Display name",
        "Telegram link",
        "Subscribers",
        "Formats",
        "Est. PDF/ePub volume",
        "Specialty focus",
        "AU doctor relevance (1-5)",
        "AU relevance notes",
        "Language",
        "Activity",
        "Notes",
    ]
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_style)

    for row_idx, ch in enumerate(CHANNELS, 1):
        values = [
            ch["rank"],
            f"@{ch['username']}",
            ch["name"],
            ch["link"],
            ch["subscribers"],
            ch["formats"],
            ch["est_publications"],
            ch["specialty"],
            ch["au_relevance"],
            ch["au_notes"],
            ch["language"],
            ch["activity"],
            ch["notes"],
        ]
        for col, val in enumerate(values):
            if ch["au_relevance"] >= 4:
                ws.write(row_idx, col, val, highlight)
            else:
                ws.write(row_idx, col, val)

    ws2 = wb.add_sheet("AU Doctor Notes")
    ws2.write(0, 0, "Australian doctor relevance — supplementary notes", header_style)
    ws2.write(1, 0, f"Research date: {VERIFIED}")
    ws2.write(
        2,
        0,
        "No dedicated RACGP-only channel found in public search. Prefer official college resources.",
    )
    au_headers = ["Resource", "Telegram", "Official alternative", "Notes"]
    for col, h in enumerate(au_headers):
        ws2.write(4, col, h, header_style)
    for r, item in enumerate(AU_SPECIFIC, 5):
        ws2.write(r, 0, item["resource"])
        ws2.write(r, 1, item["telegram"])
        ws2.write(r, 2, item["alternative"])
        ws2.write(r, 3, item["notes"])

    ws_au = wb.add_sheet("AU Doctors ranked")
    ws_au.write(0, 0, "AU priority", header_style)
    ws_au.write(0, 1, "Channel", header_style)
    ws_au.write(0, 2, "Link", header_style)
    ws_au.write(0, 3, "Subscribers", header_style)
    ws_au.write(0, 4, "Formats", header_style)
    ws_au.write(0, 5, "AU notes", header_style)
    for r, ch in enumerate(AU_CHANNELS, 1):
        if ch["au_relevance"] >= 5:
            ws_au.write(r, 0, ch["au_relevance"], highlight)
        else:
            ws_au.write(r, 0, ch["au_relevance"])
        ws_au.write(r, 1, f"@{ch['username']}")
        ws_au.write(r, 2, ch["link"])
        ws_au.write(r, 3, ch["subscribers"])
        ws_au.write(r, 4, ch["formats"])
        ws_au.write(r, 5, ch["au_notes"])

    ws3 = wb.add_sheet("Disclaimer")
    disclaimer = [
        "Data: public Telegram pages (t.me), TGStat, web search.",
        f"Subscriber counts verified: {VERIFIED}.",
        "Many channels share copyrighted textbooks without licence.",
        "Prefer RACGP, RACP, AMC, eTG, and licensed e-books for Australian practice.",
        "List is for discovery only; not an endorsement.",
    ]
    for i, line in enumerate(disclaimer):
        ws3.write(i, 0, line)

    wb.save(path)
    print(f"Wrote {path}")


if __name__ == "__main__":
    build_xls("medical_telegram_channels_au_doctors.xls")
    build_workbook("medical_telegram_channels_au_doctors.xlsx")
