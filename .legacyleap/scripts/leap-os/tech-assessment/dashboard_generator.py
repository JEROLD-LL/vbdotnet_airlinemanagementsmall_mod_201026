#!/usr/bin/env python3
"""
Technical Debt Assessment Dashboard Generator v2
Generic version — resolves paths from .legacyleap/metadata.json or config_loader.
"""

import base64
import html as html_lib
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote


def _resolve_workspace():
    """Walk up from CWD to find .legacyleap/metadata.json and derive all paths."""
    cwd = Path.cwd()
    search = cwd
    while search != search.parent:
        meta_path = search / ".legacyleap" / "metadata.json"
        if meta_path.exists():
            return search, meta_path
        search = search.parent
    return cwd, None


def _load_metadata(meta_path):
    if meta_path and meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {}


WORKSPACE_ROOT, _META_FILE = _resolve_workspace()
_METADATA = _load_metadata(_META_FILE)

_scan_reports_raw = _METADATA.get("scan_assessment_reports", "scan_assessment_reports")
if os.path.isabs(_scan_reports_raw):
    BASE_DIR = Path(_scan_reports_raw)
else:
    BASE_DIR = WORKSPACE_ROOT / _scan_reports_raw

TECH_DIR = BASE_DIR / "tech_assessment"
SOURCE_JSONS_DIR = TECH_DIR / "Source_code_JSONs"
META_PATH = BASE_DIR / "meta_cognitive_model.json"

TECHNOLOGY = _METADATA.get("legacyleap_plugin", "").lower()
FRAMEWORK = _METADATA.get("legacy_framework", "")
APP_TYPE = _METADATA.get("legacy_application_type", "")
PROJECT_NAME = _METADATA.get("name", "Unknown")

TECHNOLOGY_DISPLAY = TECHNOLOGY.capitalize() if TECHNOLOGY else "Legacy"
TECH_LABEL = f"{TECHNOLOGY_DISPLAY}" if TECHNOLOGY else "Legacy"

REPO_ROOT = WORKSPACE_ROOT

def _find_by_filename(filename):
    """Recursively search WORKSPACE_ROOT for a file by name.
    If multiple matches exist, return the most recently modified one.
    Returns Path or None.
    """
    matches = sorted(
        WORKSPACE_ROOT.rglob(filename),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return matches[0] if matches else None


MCM_VIS_PATH = _find_by_filename("mcm_visualization.html")
FSD_PATH = _find_by_filename("Latest_fsd.md")
TSD_PATH = _find_by_filename("Latest_tsd.md")
APPLICATION_OVERVIEW_PATH = _find_by_filename("APPLICATION_OVERVIEW.md")
DEPENDENCY_REPORT_PATH = _find_by_filename("DEPENDENCY_MAP.md")
RECOMMENDATIONS_PATH = _find_by_filename("MODERNIZATION_RECOMMENDATIONS.md")
POST_MODERNIZATION_PATH = _find_by_filename("MODERNIZATION_EXECUTION_REPORT.md")
APP_TAB_TITLE = "LEGACYLEAP"

def _detect_file_extension():
    """Derive the dominant source file extension from actual data (sheet7 or Source_code_JSONs)."""
    from collections import Counter
    counts = Counter()
    s7_path = TECH_DIR / "sheet7.json"
    if s7_path.exists():
        import json as _json
        for row in _json.load(open(s7_path)).get("data", []):
            fn = row.get("filename", "")
            dot = fn.rfind(".")
            if dot > 0:
                counts[fn[dot:]] += 1
    if not counts and SOURCE_JSONS_DIR.exists():
        for p in SOURCE_JSONS_DIR.rglob("*.combined.json"):
            stem = p.name.replace(".combined.json", "")
            dot = stem.rfind(".")
            if dot > 0:
                counts[stem[dot:]] += 1
    return counts.most_common(1)[0][0] if counts else ""

FILE_EXTENSION = _detect_file_extension()
LEGACY_CODE_ROOT_NAME = Path(_METADATA.get("legacy_code", "")).name if _METADATA.get("legacy_code") else ""
LEGACY_PROJECT_NAME = str(_METADATA.get("legacy_project_name", "") or "").strip()
LOGO_DATA_URI = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAlgAAAByCAYAAACPzq+lAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAA"
    "B1MAAA6mAAADqYAAAXcJy6UTwAAAAGYktHRAD/AP8A/6C9p5MAAAAldEVYdGRhdGU6Y3JlYXRlADIwMjYtMDQtMDFUMTM6NTY6ND"
    "crMDA6MDAkDMHIAAAAJXRFWHRkYXRlOm1vZGlmeQAyMDI2LTA0LTAxVDEzOjU2OjQ3KzAwOjAwVVF5dAAAACh0RVh0ZGF0ZTp0aW"
    "1lc3RhbXAAMjAyNi0wNC0wMVQxMzo1Njo0NyswMDowMAJEWKsAAAABb3JOVAHPoneaAABSoklEQVR42u29e5RdxXXn/9mNnVkrMa"
    "Bu7MiJTaulxhmvxMJgcCaJeUhI9OQ3iY2xM7+JBwHqBvKyzTP+gY1BLYFjKxPenkwyBrUEyEkmtjEkzkOtlsTDmfWLZYORk59j6F"
    "a3sBOIjVqCzGQSW71/f1RV37p1q84599EPSfVd66577zl1qnbtU49de+/aJRwbkNlfKwDQwfG1q4BViq4CzgROBL4hyLeAPx3p3/"
    "kgABMIoN6ny37HylDv20csfUZGRkZGRsZxCmk/iwWHq4MCcuf48CpV3bCv/6nzgjTq/145fs6kiDx8ff/wMHEBKRS2wjxmiAtbGR"
    "kZGRkZGcc5jnYBS1hhBKvB8bWrFB0GzqEmGPlaJ2jUQAlwQJCbR/p3bgdgYjadL1xVySsjIyMjIyMjAzi6BSwBuGtiY7eq3vLsii"
    "c/bK+lhCuHmJClp0+c+xhw7fX9w1OkTYXZPJiRkZGRkZFRiqNNwBK6rYDUDzeNDt364pKpDwOnUK6pikGD3yLI7YLcsaVn9BUApm"
    "ef9/PM2quMjIyMjIyMJLoWmoAKcMKRo1W2j45ccOOOwQlVHQZ6gvQaPFsmCIn/regtM8w8vX10ZD31zu++cBU+m5GRkZGRkZExi8"
    "UvIHRbGvuRm0aHVr24ZOoW4DyMwDVDTfAKzYGhmbDqff976o2Hll34qQu3jDNur0/P3o8JXBkZGRkZGRkZR4eA9dmdW5c8u+KJDa"
    "p6zUvdB5xQ5b6LHNAJ/kf9r0gLYCyd7lURuX/l+Ln/5ZILB8etyTBVBgENGRkZGRkZGcchFpuAVRN0zoaP7rxiyYsnT92g6FXAGy"
    "gXkiAt+LRTfwUOCXL3SP/OTwJHmJgN0+CX6YdvKCs7IyMjI6N9hG4g4fibx+OMBcFiEbAatE03TQ9drKr3vtR94E2R9LHdgeH9Tt"
    "Z/Vqiz8bOGr+8ffpj6WFi+L5evZcvIyMjImDsULbwhHXInI2NOsRgELNPYV5hOMDi+drWitwDnJ2hMOZnHOk7ZyqWZ+tflL8ijwH"
    "Uj/TunABc/q75ONWErIyMjI2NukbJipASvLGRlzCkWWsByjb3rromNJ6nqHc+ueHKQtE9UGb2hqbBTPIjFw5oB5PSJc+8HPnV9//"
    "B+sokwIyMjYyEQc9EI7+eTODLmFQsnYHWbr6GDF56s6HWKXg0sodynqgpitvcih/RW8vbznXrjoWXDn7pwy4OMW/qn8y7DjIyMjD"
    "nG7Biuqr3AoHdtJkzj4esi8shCE59xbGNBBaztoyPrR896eAPQR/rMP2hNIGpHiCrKMxZsVJZO9yowefrEeb96yYWDY3a34XElXK"
    "nq+iaSf1VE9i00zRkZGccERFXXAn9JNf/crSJyFXBkoQnPOHYxfwKW1VjZCOyrXlwytQHjZ1UWNiHlU1VkPnTPHFo5fs4zwDcAFZ"
    "FlL3VPnQP0vNR9ICyvCDHhz6epbqUkyLalh3pv+9SFW/az9/gRslS1mboOi8jGhaY5IyPjqMbsmKyq5wN7Kj63VUQGF5r4jGMbr5"
    "nPwraPjvTt639yg9V0hLs6/N9ljupFAUIBvgv8PnDPDQMbD9YR0YPeuGNwELgFozlrBmUhIgBE0ctVdf1No0ObPtW9ZUOFfMsEy4"
    "yMjIyMRvjj5GuDa0UL54X2P844DjD3jczEszr5xZOnPqLolcCPUm9mKzquJ+a07tvXGwKNnj5x7qOqev0Np2309/WJV5YCesfzG0"
    "4DPrqv/6nB4F6RsFeFzpCn44J8YqR/5wgAE01HlT9qkDVYGRkZCwVVvQAYq5h8m4isX2iaM45tdFrAatA23TQ9NKiqH3up+8BpxD"
    "VTRUgJWH4IBCcYPQ5s3No/9jigCUGm9vwK82f9+Jo+4HPAmQ1pOsdPXTl+zqiI/Mb1/cPj1GJkxRz62yl/QZEFrIyMjIWCqq4Bdl"
    "ZMvs2aCI+6cTbj6EEnBKx6jcsK823jWX0cWEX9eYFQrPEJEWpznLZpBuhaOt07Ddy2uWfkXnsvFiYhppWq0yDdeHBwCLj5pe4Dy1"
    "usexlc/KyHgFtHenYeAPCc4WOm0aOq82cBKyMjY6FgNVg7qTYeZw1Wxpyjq/0sAE9YunN0uO/O0eFHFR0DLsAzy3npuqg/MLks75"
    "QJbRPwE5sHRu7CCFYzXr54vyXIy4cCsnlgZCtGi7XJu56qZ7OYPUpH0UsVHds+OnJFopwcQysjIyMjI+MoR7saLPHiWZ2k6LWKXg"
    "ec7KWpcqxNlW21AqgNh/DkyvFzr1g3MDThHb7s51WmCYodnWDQDQ/v2LJ8X/+TtwKX2d2GRfxrJgBqSN/EGw8tu+pTF27ZzbjNb/"
    "ro9L+CrMHKyMhYOGQNVsZiQ0c0WNtHR94zw8ykohswwlVMwIl93P0yuDwmgbWbB0ZWrxsY8p3Yi3b1hfmUCS+6bmBo/+aBkUFgHT"
    "AFbQs9qd2OK1R1502jQw9sHx1ZRnOm04yMjIyMjIxFitYncaO5ksGDa29VdJi0f1MncGjt3kuG1w0M3ZvwWSoyq6XOMqyym89ptD"
    "bsPHv7NdSEx2aFoJQGq05oE2TjSP/O24EZe7bhUaXFyhqsjIyMhULWYGUsNrSlwdo+OnKr1VpVRSsCw31A/7qBoXto9OWCxsjqsT"
    "JTGrMqZx7quoGhYeAMYBvNCY8x/6pZf6yAHlF0+I4dG/7uztHhweBeRkZGRkZGxlGElifwQV27XtGRismTu/dIaHZWjp+zC/jIDa"
    "dt/FoTddEK18K6p2JfRUMo3PH8hjOBz+3rf2p5UEZZ8FMS5aWwU5APjfTvfA4TdoJEebG6LIjmK2uwMjIyFgpZg5Wx2NCygLVe1+"
    "ynWiT0omChMV+tceDXtvaPmYBxExVKSOfZ7HMu/INPT326FaY+68fXXAHcHOFBkYm0yr06Ien0iXO3Ahuu7x9+AQpNsClhbt6QBa"
    "yMjIyFQhawMhYbmjcRroA7x4dX0fwxM7H4VLMT8tLp3uml0723rd17yTu29oyNMUFV4SqmiarqOJ862zAGQ+sEwgRs7Rl7YO3eS1"
    "Yvne7dvnS6N0ZP/XPFdCVpf3bFk4PPrnjyiZumhwY5G6UbobuBf7FYYRkZGRkZGRkLhFZ9sM5vIm3M1BZGYf800Ld5YGTDuoGhV1"
    "ukyeVZp3lS1Xeq6npVHVLV1ar6JsrNaKk4WnU8WzcwNLV5YORSoB+zw7EorxS05JoCfar6wI07Bie3j46sovFYn1RZ2YcrIyMjIy"
    "NjAdDqYc8rm0wfmuGOLJ3u7QKeWDl+7ifWDQyNthH/qcG0pqrnAO8H1lOLyTWbRlX3Ar8rIlsp94kKBZkjmHhV5t5eZHPPyATdLH"
    "94x5bLdp69fSOwjOrasZQGrm6noY3H1Tt61sNjgwfXPrT0UO/GT124ZZK9pU76GRkZGRkZGfOMljRYqnpKs48EvyeBCzcPjKxaNz"
    "A0SvumLSc4nauqu4AngWuAJYm0ZwEPqOoBVf0A9fGxqhzC7FAnEK4bGHoQczTQvTTWuUrE+jBtVFBS9FJVHb9pdOhWigW5bCrMyM"
    "jIyMhYAHTqqJwi+MLJ4ZXj52xYOX7OOzf3jOxiL+Ysvum28kdVe1T1v2MOfF5Nsd+T//9NwHZV/XNV7fP4UWUnoEtn7tl6bJWxqa"
    "0ydu3K8XNWrBw/52+Afw2eSwk9fqiJ0D+sgfaXug/oi0umNqzXNc8P6tpeuunyfLMyMjIyMjIyFhDzIWA53yiAVTcMbPzEDQMbX6"
    "ED2hVVRVU/DuwH/LP9Ytqg0CHc/1wIjKvqZ1S1l5op0337z6XyrxPCbhjYOHnDwMa3AR8Dngd+QL2mLBZSIrwXE7gIyl+u6O6Hd2"
    "xZGbmXUR0pQfxoM7fOJ91hu8woxkLzaqHLP1qxWPh2tI5J84VwXl8oGmYxHwIWmLhWw1v7x/YxgTLRYD5rGqq6HiNY3QacRGPjk4"
    "JPCoPAHlV1gT79MwtD02EDSXX/7C7IrT1jd63de8nZS6d7P2HPUQyjuKcOe07yMqgfQN/Os7c/MnTwwiVN5JNhUKgpJG4WhtqB5e"
    "5a0fFMPrqCb+jcwBnTvMZojB2CXpSnX2f/mmu/XZH0MZ4tBpTxBDo/kQn1C7ZYewn5VcS/MppTeaUWbFV5NtfvMdYuY/1nvhcRRX"
    "zrZBsp+l1mVWkmf/e/rO00m3dZn5+LMSHVFlI8cn0x1keaGSNT/Kwrt1Un92bgCnyIxgZSFgSU8BlVXQ18FFhD57Q0fnl9wP2q+j"
    "HgoyLyeY+Ghl2KQR5RwWvdwNCr9LPxxh2D2zAC4SVBvVKTeJVG6Mpcpui1wHCHeHK8IBWctovi96Oquhw4EegF3gB8HzgM/DPwbR"
    "H5ppfewe2enaGzE0SRcNAwSajqycByTHtfQk3LrMAB4KCIPBvkFaM91Z9TR1LNuWZVVVcAp2BcAF5naX4F+Cfgu8ABETkU4ZP/P6"
    "xnO3S7Z8M4ez5/6mixLgt9mLbl8jjgvkVkKvKce78h3bE2ET2uq6S+nX53MRr9dhr7XXRqx1wh9o5CWqLBn1X19cBS4Ecx7fEE4B"
    "BmnHhZRPYleBKWG5bdDN2p9KWBsa1F5zSMEmMJZpPXq8BB+71fRA6X1MGV1clxIFzg+VEJYrwLr6mqLsFsSHsT5v2AGSe+B0yKyA"
    "vBM6lxO2y7s9/zIWAJMH3DaRsnI4xNCiVBZdQ21N8GLg8Y2mlaXb7Lgf+hqp8BPiUi+2mU8MtCPWiw23CSbi57eMeWnfv6n7wFWG"
    "F3B3ZisBBFLyULWJ3ACdQLHG6wXA78B8wO1bcT30QxCxt39RngWeBzIvIl6ttY0QKj1QEo1IzO9iNVfRfwPuACS38s8K+r7xFV/V"
    "dgFPgT4IsiMk1jQN5wgJsJ6IlNntDeAOsvuE4C3okx81+IEUq6I+XXaY9V9TDwBPAIsNsOpn7aKgN2VVqhkdc+fajqKuA9wCpqQm"
    "+ybNu29mDa1phtW45uf5FApLyyVXlMyx4TCNuFyzfG55g2ZV4F9aDMKhoZtRvALsWEMjoLOLUgXxec+evAV4GngL8QkX8M843QU2"
    "XXfey5GO/c+LYE0wYvAM7FtMNSzbyqfh1jTfoTTF+aDGjv9HsM2284BoX5zvJJVc/HjN8X2XcTCsV+iKd/AvYCj2HGv6lEneoEN+"
    "9eV/MT+wq4Y8eG3fv6n1rVxFNTW2VseYLJpSYyVb0F+E3MarQwbZsIY3T50uom4F47ycToTtWjvkN02+9+uHHH4M0vdR+4jcZO0y"
    "rNslXGTiigaU5xDERyT63iLgWGMIMO1E8IoZ+en1d47QCwC/ikiDxH8eRblZelqnFVvRwz6F9AfAJOrWR9oWQK2AI87A00s/1EVc"
    "MTEFLt+TwReZLWJmp/UL8Aowm+CBOKxY8NF1v5F61mwQgrD4rItoBuX3vXLM0xzdIsb1S1G/ggcB3Qk8ijyoIUjFbkEeA2O8FJ4v"
    "m6fFX1XuBDFeujwBs8Qbtd1GkHVPVx4F2UCAIWDZHY5yiSe2xx4K7Pzg9WQL4FI1i1Ykb0x5M/AD4jIk8Q70Ou7Gb5HNVqqup5wA"
    "bgPOrfSRndKe30g8CIpT+ktymNtqr2A9+qyMt+TxHiL4x7MG38OowmLuRBWB+/HD/dLswY8WBFvut87SJ0juOpzu7+1w1qqrpKVS"
    "cwWpkTiU8AnaQz1TEE0wCftv5Z/uo9pbKO1VeZRphG2Ytu7hn5xMrxc5atHD/HH9RbmXTmgh/HGxoEAtv+poARjHDlmw3D51LaIP"
    "/aMowG9m9Vdas1ZfmreKg+uBGkb8hHVS9Q1UmMYOSEq3CnrF9W7NvVeTlmkbFbVS+jJqB1WTNCzJQTg9OaNytAdtlKnWFDsYxaXn"
    "ZjNI4+rTEexbTP/rtajQnd8pwd1FOr/2bha8SceXaJqt6KWfVvsHUo0maGvA3vgdF4DWE264yo6qlB+tTY5lwg/PYajl0OXZbnKY"
    "1Os5h9L1Y7/HPU9yfHt5jp+d4OlF+G1IQ7S7sdI/YAYzQKV83yyaX/z8AuVX3QGyOifKuQn5++rhwbeHsnsJuacFVkhozdj42Hl2"
    "N8mbeo6mk0mtWa0V75m8PKhL+eMF9VvQYjoG2g5qtd1i9i9ClmDB1R1XFrwg/7TcMCZr6c3F3h4SQSXVWq6gpV/Rym0S7zmBLu7O"
    "ukBitUh4eN0gmKD6jqV23Dcc+VvTSHBgfnGwY2vnDDwMZBYC1mwG1WUPLTthoFP8PACfYnqernMZP4m+y90KSXWv2EaUKhowsjZF"
    "wOjFlhBeIDedX27ZejdgK/09LvL258rWyzA7+jZxlmkNlgrx3B+Gho4rl2MUu3qn4Yo7Jf5b2TsI/6fbis/NCM6lwDnlfV4cR7aK"
    "ZODYKK1XR8BdiIGfBfU5FWv+xUWserS4H99h2l0iuA1TLsoX4S88dqqG9fF9Pc+FSFR1iaY33oBBod278uIk93kIYqCAX9HlX9HY"
    "xW41zigkcr+ft97RJMW3R9zedX+FxRvnV9RFVPVtU7MPPraur7SziPxfpXSEdIu7u3HjPGXRHk20z7CWWUIo392+tuqN4N3IVZwK"
    "QWGGUm4NiisY/aGBFajOoErvkK05CSCBtgV49/ienIKYm50yiyVcck9XcA37IS+k9E7vv1rpv87L2aJsHtNpSx3VtlbMXS6d71S6"
    "d7DxTxKM1oeXQOeHM8YPZ9q+qZGL+pi7AaGtICN8H/UPAP33nYRpYBW60JPEVTFcyu8u2Kdwy4NqA7NlC0KmQB3Kqqm+z/70d4E+"
    "NBjG+l5VqBcQ9wd6QehSvICJ9i9XbvxncNuFVV7wL+DUSFrKoTm7+avhkzIfdH8mwWKYFeqQ36G1R1r6oui/DFp+9LFE8y7jkB3m"
    "X9YSGtMWylLpd5/1NWAYe7I/TNBUIaujBjxDLgz4DrqW+LnVr4h218g6o+Yv0NuyLpyupQ+2M0L3sxgbhj/SYlUMVoJHI/bPenAp"
    "/xxrhm2324oSZVlmCsXKKq3ar6VeDDGKVDbJFbZREWU7j4gvatqrpLVU8M0s7yZr5MhEVS9yxBVk08illFzgdStMWk7digPgh8UV"
    "V/HfihSN1iz7rVoW9Dn33hmwdGHsSaK5qoh+Efs6vujObgND9nAjuoOT/GVnKh4AzpwSYlyITtboPdTEHi+SLM0mIXJzuBMxLPdm"
    "Lg93/frKpXYwQGR2+MFy2bTayf0hjGhOHnEeN1iv+xa34evmbcF4SvVtXrMH07JWCnhJI6IcGaBDcleNIOwgWsLyiCaQtjdmyN1V"
    "0wJvDpRN4h77qAX6N+HCziQynt1geozyvDmXxjbekQxteMyL25gF+HGSug7MRsrPDvt/o+NfIdEyTegzEbnuzxpmwncl0ftLTvAl"
    "YENLfLw6KxxtVnk6pe20KZr8FoyZXGNhcKQH329wPAmTbNiR49GvkuoqNorHJ5nItxmziZxrrNiwYrxvQU3oMRrlIVS6lJQ4aHL6"
    "IKA2MmPim5BvBW4NOq+jde/KyiclODvnnhe2Fzz8jk1p6xD6/de8mPL53u3b10uneGmpZiJshHAF2795LhrT1jUwEfMipCVc/ATO"
    "RLqA3wyeQU8zi2Ooppwdz1LmC9qv7XyL2q9PdQM6lD8Q64Tq2wAW4FfjrCDz9NK+3R0Xgz9TseaSEv90yoTY4JJmF//4RdQIVlF0"
    "0UodbgVjq/u1cT3z5t7vcKYKcVVhs0mTZkxWjief+ae+bCSJkxLV/V8XcdjZNlirefF5FXOszLIvpqFTTa4VFqC4oQKSE/1nZTWr"
    "o6UyT17fFMTB+HxvmqTMBVjK9Vb+ReEb2xBSVUaPeRe3eq6koa+xAlz/kCZegH664DLLHm1PcW8CTkaVUainAWZgdlmP+8aLCaIX"
    "59SYVi6suYVNps+SkVaRFCCXgFsMWaDZdR3Hl8NWWqbv+8bmDo0OaBkTXAf8KcrxhbZR8Eblg3MHQ7zTXcDAu7uv8cZrVzQoVHyj"
    "pmaqKJ/XafLuBXrUYImm/Hv039lvCUabCVPlJUxyUYjUZZ6Am/TpXKt/5p10V4OhcI+47Ppw12C7tvBqpk6rAD/vAc0ukj9q7dM3"
    "2YNh5LD2YjRFWN6Tmquob4xFs00acWrO+O1I9Env+N+Rnnwr4zg9Fu99H47os0eTFBPCXspxQE/rNnWP+pIhNdWI478aSXerNuTB"
    "gUL01Mg+nzJrUzMEaPS/MY5eNniKLFlb8o+veYsSil4Y5ZpVJ8DuuQ0sK7ss61LgV19Z6POFjNMPF00i8qXGXGGpLPqFeAbRh1sg"
    "vQtwxj1jsXIxClTHhVEdN+rQcut/4pW+2Wdj9N2DD9OtTyNQr7f7G7DT9PN597eMeW5S91T10AuFXAC0unl42sGxg6zHRzk1dGHb"
    "ZhBp9Uf0iZvsAEr5zAHGAOJpTIUuCnqF91pVayIW5R1S+JyHhV4q0gMuhdimlp3PVYfKdYff18UmliAn9s8dAKBCOYhCv1onwPY+"
    "IJPYfxMxn36DsJ0+fPwQQpPjlRR58/7vtkjFP6NdSPP4XmBVV9E2b3UlXEtGoxvsS0aGUCvwLnqeo1InJPcA8R2WHj/pxIMVz9z8"
    "eYm6qWHRPCRFXXYYI8psxdfl3/WkS+Rrovdgr+/NKFiQl3N7U5I2UGT2kTX8FsYJqw+S2xn7dRW9A1E3j4GlX9ExHZHXmmYRFld/"
    "luTPA1xcODmLhcjwMvYQL0unN1T8H4IZ+FEWpiPEm13V5V/ZCIfJpq7y+mqfPr6GIWCvBjxAWmlLnZpytGc9X25Wi5WlUf8cNTLB"
    "YBq+rKOraCjNlT9wC/aicpn3kHgCesqvdjmEkpNoA3K11LJJ8NwGWqusnG1vEH8JRWoXAwWjcwtJ9uttTdm640aWckYLfx/gzw2o"
    "JkYducBD6NMVe8QOOAinVIfTe1+FmplWPY1nqA+zF+eLGyQ/p7MfF3QlrDyTclNB0E/hwjmBzA+OL8wNLRh4lL9HPAjyf4EotM3i"
    "66rNDYV/AO/PIP2fdxj4gcTNDpcK/VMK+3fCvjj/v+DVXdYKNWp0yvda8GE8i0DLHFoWL8Tv7KvpMpzEaCUzCT/FnAGyNlx8yGfj"
    "26gI+r6jYbyyrk7Z0Yk29ssnS/ndD5QcwYl5rgieTv/3f5+GNwyszovmN+ip1GWPcZ6yN2Nem5IdYGDmGc8UdE5NtE+qTViq7GBP"
    "/9QISGWDmOF/er6tnWvJtyBHdpPxZ5PqbN6cIsSj6JCYycMsUK8AWYHX+GqYXvgOJ51M2Nn674Psrm53BBV2VOncb0q3HMArnP8n"
    "B1olz/WliXUHt5KyYiQItYAXc8v2H3el2jFT8z63WNawAx1ePsf1WdVNUZTWNGVY/Y7xnvmvt8LaK69sv1yxdVPVVVnw/yOOLl2y"
    "mMq+rZQX3DT/jiiPEo8kwnJ7a20CRPmlnZzxW9fao61QTNh1T1evt46h34bc7FibrctgG/DfttN2zjquZIqLJ3KmpiHh1J5BXm6a"
    "ebUNX30NgnY32nS1WvVNX9iX4X5q+JNDO2XoV1suVNBnkciZQ3Y9/f8oqv3NdKdKnq21T1H7338YOgLmE9NnjPF2ptVHWw5J3E3s"
    "+M5fH1avylYrS7/N9p371qI8+PaLxduXvDRMZgNbuvNPGcRspaRXw8KmpL/ni/LNE2Z4KyZtT0vZ6Q5qA/X1CR36qqW2N8jbzfLv"
    "tOyt6fT+t9ltaidlLHGzWhifwxokp5wwFPG3ivJuSMz1//+bCcETWR6KM0Fn1U9RqNjwkpXFClw6oZo2P5xsaWI8Fv9b6/Z9/Lal"
    "vHaHtV1TVqYhRqpKxUuSFts/1ioX2wQgkwtUIJpcRQVXgIuF5EzhaRXTQ26pgpEBH5toi8BbOKmvLyDU0e7WIF8BWtBQAM6xSrb0"
    "r4itUJOkPn8YYN1Jw+U3B8nQJWiYizs5cJP7P2fRv5dy01M2JoMgzbt2K0K4VlqNHExFaOKVpcuvuAM0XkT700qbbm6uB25nwaop"
    "qG8JiKVtujqjGt9QZ5xMrbb9/J/qp52+8ZABH5BvDr1I8lLl3MzOmEXl9rl9LWfJzi/uvK8UNE3A2cJSJ3eSdGRJ8Xkb0iMkR9u4"
    "qZRAiudQHXqdGwuv82SzlEzYna5efzJAw18v6CtGWanhMwzvL+eEsiP8Foiw9W4GmzCPtd3RZ+NZrUZQXPhvW+QkSuCaLdx5QKdf"
    "ywbfhs4NFI/uHHPX+19x5jZjGondkbO23CL2NCRAZF5GXiAZUL+7OI3IsZV8KxKFXeUAvvp65IGudIvx/7Zv5HgZ8WkatFZI9tR1"
    "FtqYjsshH++zG7a5u1ECmeW8BCClixTvJ7GJNFisG+YAVGjb4JOM2+4JhqnER+s+nsBHgBJijZXAkqijFLTKqJCdIV3AvrGKM3o0"
    "NQE7tkVVky7/tiEfl6cK1IAKjLxx5fshrjJ+SQciYVYLWqnksaQi1WHJFvvw5+W7tdRK4TkVe9+359kpOkiBwWkaup+XOEC50iOq"
    "qiCzPRxHjsX+sCfqsJ4SrEjKmSPIrxM4kJcOG18zzNhE+Pn0bV7CZOTcoE6Z2P2KCIXO9NzDETzmwZ7r9dUF6AMXeESAnbJ2F2Wu"
    "GV5dLeHtYneDd++g9Q/L5jk5P//MeIj9WxNvxpWm9TzSA0mW0sSe/z6Fo7l/jCEDT2rWg9rYB7OeZ8ydicEM5/S4CfL0lzboSeWB"
    "0GIjTFxoKUWRqMYBEz0YdlCfB/NfleYjxLjcH+9RtE5P2RcaJBuPKuiYjsF5ErMPJFM+1OgPPd2D3fAlbY4epelpUsP5JgRLjK/x"
    "Lwb0VkY+BP4BA7zibWyNxAu19EPoKJSv0wVDrrSZu47r+kjWpMNFd498J6hrSmJvaMRpSa1jCr777guiby2SAizxCfTGLao3AyEQ"
    "ArZA1SP8mkBl8wvhlFKPILidXrNhEZpqaNCNu4X4fw92wae4bk3Ql+hxN2M3DPne79D/k620+sVq0dOD58gcZJJAzo6HAejX6UYd"
    "0/RrWx1dXrk3ZiLgpUGU52vib+AHBlhGdF7eL93v3ZsVJEHqe2CEhNpi7vblX9OdKTb7Kf2AmoL1HPkPav2f43V0hpr95JLSZe6j"
    "mHB0XkPhJ9hvT4UHfN+j1dQf2cUIRfjfHXu38m8XHLp+vpwF+5aP4JNVN+fzwM/CHx9x6iR+sD4FZ5PykBNeZrJRir1l0YRUzI95"
    "BPMTkDO9bdEPCrCL52d0HDNDTYizEvaStGPTdJvMPuxpgF3m2lUj8+VGzlUMYI/8XMiMiUiFyFiSxcJaJ62FnCgTo16PRiHBXHtX"
    "beVBXVekYxwjaVUs//BuVtRYFJEbk9kSYlSMQ0kG4AfRTj/FxkznG4KFVJNXG7+ijv8C7/A8Hh2uGgH6tfagUumJXduHe/Va1rjH"
    "7/LEB/4vPNdlUcyKuUrZiTI2KmhthE00f8vQuAqp5Oo/aqaCH2+yLiVsnuWJhUm0xOMHbnkq89KeP3qkiebj64r6Q8H1fQOIGXTU"
    "QC/McCnoT4XeYesfb7K5T3L/fsJyjWuJZZVWbv2Z2SRe3bz+d8q4336fbvdyee8/F14u2u7B2GaRV4ukJ5DmfTOYTj6V0icnekTu"
    "7bV8CEsSXdbyeT3EXNNaLq2PYBWFxhGmYFHRGZAFaocVj/KcyOppcxkvaXY0xoo9wGSRz4voh8FvgDNfFDrrE0VNEWxOpUhD7gOT"
    "W7DYcjtGQ0j5RmQTGr51MwAWKlJL1gtqLHNDsx4ST23mKD1R7MNvdY2T6WqeryhHr7fKpDqfk8lB28WmRGmA1hICKHVPUqjM9OlT"
    "5RtHgIebqD4kEPaoufVuFrgJ5T1TIeuLLfHuGdT//F1M4XbCiLxnZzH7Wjho4E+RLJP/Tf8/O7k9qRM0ULNQFOVNU3212wYZ67MD"
    "5kMXpDfrxbVU+02otQS5PqM4oJKh3TIoRahkOY2EmxNHMB/52uqvjMoyLyPLUxI9xZG2tXsXHBv7YBo0yogtXUfLdC3jyOEXrCBZ"
    "IvaHyJRv+6ojYL9WOkz7u/boLXS5tIG0NsATKDGRt+i8YTU5rJy6+jYnYHXkotvEsZTlHV0+ZTwCqaSBxj6tR8IjJGo9NlFca0Sl"
    "9IEyKySVUfxDT49TQOALG6+PlVUS+DOdeoT0QGO1yv4w2xCTtcYZ+DifeTGkD8/58hvTKNlUmkvPDZJyjuDz5WY5y5CfL8D03wZJ"
    "+NmZNSjVfR0PppXd/Yo6rT1E6xbxX+YC8i8jCwnbntA1X4HxOmf7TkmVWRazEnbsGYlf4Go7nSIG1KsEzlhYjsU9XdERpSZuzVGK"
    "2XfwYjIrJbVZ+gdohxKBz52s9ujKP9F2gcw0M6FWZjX50a0JTSlj1mHa/9PGK/W0VU86om4nhVE9bng+dDM1oRUn3xWeo3jhThPO"
    "CLRNqriFwbqWuZ1l0KrqXSuDz/V0WeQXlfahaOXxtsm2lGGZKCU/ocVnPSxseaePZdC2UiLDNN+Ndiavr5ghvwJ63g8w5MsLiUTd"
    "39Th0qm+KF+75MG49LyWgesQHbf0ervN/hhDDjpZ0Skf+X5gfKlGnNwanRQz/BGFYmymlGve5ip1U14ZTV0Z9IHqSzfbOKeSxGf8"
    "wknDIPg5no+1S1V02cI4jzJJxI/k0BrYrRLIaTdugc7trZY9QCTcYWZLGJLlYXv/28D3gL5sixZfZzKsYlYRlGY95n7zvNkB8s1u"
    "X7qPc7dsCw/34+GKlfjF53//3Uj+sxod/h7gQPOt3mwvH8DKr3kb9K0NgM6p61fsXfqfjs8gLehLwtm5tS5m+/LboQNCdgwlicZP"
    "vS2zFCeVW0uzCL0f6yiDzE3IxJdzRBhwBnzpsG666Jjadct3bDQSaiWgUt+F4IxHwKsI6Wp6nqeozKsM/eD1cavsq9GSFLgV9T1T"
    "+0PhULyYOjFaHZz58kHC/fRmMbJHjuB8A/2JABJ3h5xPx0ymjB5vcam/41Xn5QP7CH7aVhFW13si1pgidPVqCvKl99esFomK9tIp"
    "9WkNLAzN6z29WXYwSJHoyGstvyTzF+XUswKv4e6lX9qfcYex+pRalYv7gY7aG50/1/nLiQkRI2/P+xNGqdpF8JaC9ro04I9Cffz2"
    "BChZxEvfN9TDt1hqq+UURepFHIqvut5kDyi4L3FzPRAzzrObentMRzNT6urJjuACYY6XIa21Eo8PuICT1+vbowpuMigdWVt9LLs8"
    "wsGdOE1pWhqm8GXo/pS2/AtIHXUws23IvZDOZ+t4ofaeNZn1d+Xb/o8a+jQpZ1i9hDsenYb8/L503AmpmZeTuNNuUiM1qRkDVXQl"
    "g4acb8KEREtllGX4vxz0qpS5uZwPz6DGPil2Q0j9CEEbv3Vu8/1L8nZ645AXOI8Qs0TirttLlY2y1qxysi19xAV0mAF5Gnab6vpP"
    "pYOIj/TVU62kQ4UV+A0TKcjzH5LonQH/tdZI5qlTfuOzbZhOW5dvR4ECspKjBFyguv++UUHfCduuZr1GbzE5FXVfVhjHZqpiBvwU"
    "zAF2Oc0f2+F+P7uTRO7mH9He4L/helbRUpV4K3Ua1d9GKsGp2gI0QVEzYUa7CgJiBH47ep6vkYM++7MMLaKV66Ik1yp+vbDhxdTw"
    "V17STU5r+qJI3j28r5MBEKIPv6n3pgcHztMrqB7kLVd1VV+Vxqd/zOH105WbPhdZiVsTOTzJAWrnzBLbZi9lc756vqOXNYv2MRMZ"
    "OJz1N/AH0TJNug/78r+HZ5x56rSt9MJJ8ibcPJkbx6CAbJAkwm8m2Fdp8HbrGxH6OdmwvUvTtVPUVVb1HVZ4CdwH/BHEfUTeP7jP"
    "U3TdwP01TVSoboK0gflnsokUdMCxITcGNmtZhWImY2DWkLfazcvUcwjve+Fi5GTxfwy4n8wv+xALqx9nUQ+B+J+0XzR7NIaQR/vI"
    "W8OkFHiqYYZt+xqr4uwY+oy4qq9qjqx1X1exjFx80YnzwX5Tyc81p1KyikuwP5hG3t6wHNncZXS+77tJwwHwKWY8IyRfc8vGPLW7"
    "17oVYgNhjN9co4pNX/9hnmq/f9ld5+G1H5V4BvJ57x65T6H/LkHfNY72MBsQmlgf/WlBROvimkNGHh/bJPjD4S31XaSRXzpEOrq+"
    "vYJJmqw1wJWA5dqvohzCHOw5hVdswZPORj2QIuplmqMjDHBAIh7lMSM2kK8AzlE01ME+S/+xj9VRcAMQ1qXXu1QUy/SVy4kuDaOW"
    "rO1ovRLRit4+kYbUtMi+b/ngG+5AXDjcU07BRitCjwwx0soxU6HN+K4LeF1xekmU2nqifbI3aexwRRXRLQEGtTnUanBORYmx+n2t"
    "jeanll46lf5qnzpsGyn1N3nr193+DBtQ/cND20grMbXmDKLyb2fy7p9X/HpORQC6EiMiIiK4APY3Z9SfB8SoBMNYK3z1N9jxUUmb"
    "L8aycFz8TShPmFAkUr2qtW22+r2hSHN5TkUfVezESqFfNpBU4gPk1VHwPuxWjzHB0n+OkS/IgJTFW1A4V0eXlUWQyWTSixcSC8Fp"
    "roYnn4dFSZsIvycff/yPsdOsKH37/h5RH6bXVhxsaixYqr5wmYkBOxesXaYaso6pfNzI0xTWgziM0NrYwXhWVbH8FnMVpEFzsr1n"
    "61Sn5twm8j7WL2PXoHVM8F3Ur9SRxF9AAtBhr1Vhau0CqVcS+wS9HLVPV/3jQ6tJFqQlVqEpwLaIXfsfSKCVT6XzHHF/wejYNCuA"
    "JLdXCh0a6eUYwy4crhhxLP+Cgz27WDTq7equDEiunKUKSNPYFiQaeVuqk9t/PPgF8gbtIrKssJBEUaq07zpUiokZLniyZY38wT01"
    "6leFG0ePDTFPmBfca7F45hofCz2v7viuQlwCrSY57vC/a0PZYqRv9cTfoh31/XwrN+XWM0pz7QKNRU/aToqMvXbszaidlRGhsfY2"
    "cVzpUGa67RSRNymG+RzNSgAWxJwFLVyaDQKhXxJ6uul7oPvOHFJVM3r9c1zw/q2stYgUTdeYvzWmxwfinfEpFfx2yXnqB4hZr9rD"
    "qD1KQB9Xz+P6QnxZQWYCHbW8xZs5k2091h+usGYFU9mZo2CYpNqlXghKvlmICXLqq7P7ilTK1Q/+66mNt3107eRQJXMzxMTaoxAR"
    "Pi41A6c5F/BL5MsfDm6F1j40eFbVZV9Rcw77IITkN2H+23o1bgl/e/28xnvj7Q+N7x+Wc1V/8dY8KeCegMaa57NnIvVr8iPh5rKH"
    "KeD103Dre6i/ALGHWvQ2oiiknYoclsuaIjd44OrwY2Xt8/vL/k2cUoXIWNWjBmw3FVHQC+hlkRFZlEU/key421kyjSOM3yUUReUt"
    "WYqdb993dMHQReZWHxnYrXUjhJVU+1EbvbRaw9nkH68ONW8xdgK2YHZbiDDRrfdd3iLbj2KuYUiJeBF+33K8A/YnwmZzA7Re+nmt"
    "a4aFEU0y6lcFLi+ZhfWex6ShBLaelaXSwo5lik0Ui+MSHr/wb2Bc93UTsrMQY/v8PAnzRJY6ehFIdI8HHQfvwNMQ1CzhzTWqS5Wo"
    "GZr2PHTaWsJxp8u3SHgX8Avgt8z37+xX5/x34foT7y/rwiGOvmgvfV1UDwT80LWNOwdHrZvn089Sr15ofYgBdec9Kfa4SzaZ9d8e"
    "RlwGWDunYY2DbSs3PKlUfjYFKkrVgIhGYI15BnRGS/qt6JiQTvp6+i+Vvoeh0tKBNa/f9HMAPFEmoToq8ed/GAujCH8FYNLjcfdT"
    "MXjODeTB4XA/fQ+uIkHHB9Hl9EZ/rjbL6qOoTZzq+JfFOC9GHMMUR7MNupJ+wRLmFan/4uTByjKjwouzbVRH3DgTrVbhvMDok0sb"
    "xiGgk/qGjq+br8RWRMVV+hcUdrrJxfxhyzMzu+2bhK7y7ho8vnj73wFXM9tsd468o7QLXJ9E9F5PKQZ3NIc7P1+hCN4UNSdfbb26"
    "sYwWwU+P+A5wPXoGi5VvMc0jCfeAtmwTRXOLPkvs/PF1oyEa4bGHoZswPBR5EZDOodJJX4LiAUHVZ01/bREXd2WiikLVZNVqzRuu"
    "97A57E/LFCZOGqOsp45fuvCLWdIDGtl7/KezP15qj5/hShmcn8/RXySyGmnfX/X1TwTDPw876VmnkrjCIeK+sg8EngNBG5WETuEZ"
    "Gvicghyv2ifMGjCh+K8D2q99szaRwzfD6kFqkpYQriE2WYZ3i9Kr33UN9HYmYpxZwhe25w798H9BXx9veDui7UOF/1rMvlNPbbhX"
    "T9mOWXqi7DxGl018ssTGDGxiEROUlE1ovIZ0Xk6UC4So1Pi8Fna+Uc0eHyK9vd7/fB7zQvYE2bz9b+sTtXjp+zJ0GE/99fKRap8n"
    "3i+kbPevj+9QfX7Le7DbHxs/x8owLaAiK0h9eINQN9SHuV/Ba6sR4tSE08MShmJ01skgknoTMWYb0c3bup1vYFs4V+dYIXVemI+d"
    "WsIW5WK9MiJmG38vuCbUirP4EJRtD8aRG52TuzrspEEuZZSFZFPn0ToyGtkv5UVT3Nq0vMvBgbU2L38Z4Nx1n/fkqLV4YuzHFLMf"
    "NlzFz4S97/EzDBSlPwaf2GiOxN5DnfeKZiup/yfofvsFWfKoi/u6KPK9M/VeTnS/gYtpOvAmeLyNaS58Lx0sdcBPhsBv6Cr5Ptx9"
    "X5Zyrmq8A3YgJW1RW0YjrSVwICUr/9BtRF8eDhvpep6nM3jQ793vbRkRWJ/FtlZEsTQAWexL7D/P16FjXixSI8LnakVryhdsJ9/x"
    "2NE1JsUlrlmY4Wg7DrCxdPVXzGVeBW6ttU1bYVM8u5358qoNP/bgYXBOWUmQVXich4Ad1Vsayk/qX5ichzGN+dqvX+TxF+pTRuRc"
    "FuFbuTU1VvVNVRVd1lP7vtZ4+qPm7vjdnP+yrSqdavZXdQbopP61wae9TU2xPPhf/vol6Yn+8x0C/r6xWf6VHVn/Pq0+6iv0jQSs"
    "HnmT8OrqJxrgmFYqfsmATWeib1qm04FLaWBHnPN1arqjOJdrR8G/zbLYqqYF+ofg9NV2nJdwJuOG3jy1t7xn5m7d4POBNYSosQEy"
    "QqCXIvdR/gxSVTV42e9fDOwYNrr6YfDfai+A0qJrjEBnup/XitCK/lBF6rJ/Bafsh+3JGog3rhSet17fr1uvaW9br2Nz/68pXn8Q"
    "7gRKTiBviU0NWpVXOGQUyQD9X17vsvIs+lMFgxXSuoMoilhL9HIvUtev5cVb2eeB+pgrrxQFWvo7kDp6uWsSrgTVh///+DIjKZyK"
    "dymYkzBEP+VcVoE+X/56BeRQvHsrHUtYP/BzgPEzJhFeYoofPttXMxR3CtsvdfpjpmaHQ+Ty2Ol3hmwluC9CkN3JTVnCwWzf0zmM"
    "0QVfDz3u9OjhPN5BWb395KsTnPx72ecOWXXcV9wW9/ZxSUMZfw5ZYNVJQvKsLlcwXl78Qv7+muCglDIsNV5cy6gSuvoxaSoAqxzT"
    "JOgF5F775jx60Td45ueB+NA5IvaJX5XRCkbRDC7hndtOKe0U1bZpg5rOiIohsV/W1V3X3Tjiv2/9GObasq0B3+DgeXKpNjRnsITU"
    "qIyLMYvx2HlNkD4LIgv5RKP4VoelU9U1UnVHV/yWfcRsiu64PWEXhPE3zoAm5R1XfQKHBW4Z/7jaqeSfWT5cO8yu4tKUgb9t2/bp"
    "L3sXchGOGjLJ+qGCM9BoV4q41PFNZRCv6T+K+qejnmAF13qHhsYvTHuypaGl8L/CCm39SdZhGhVTD9RjDCXSy/cCx8ikbhaj7Gv6"
    "iVwfavvZSbvBT4oD2APVwAtArBaCNPqjA+7FfVSRsewz3r2nfVA6ud20RIA5T3n5CHq9qseysIhcH1ET/A9gowrguXVUlqv78jIp"
    "OpODHhAOE3nPrrxidLt8rYxFYZO23lxLuuWDnxLv+A3E5BAN234svLn13+1OcGde22QV3bRzdqzzb0/bpC/y6f7rqBrwsTDOzIyd"
    "/nyMnf5wO66pRf1vM/+rXTHn/6a6c9PuiNGCIg/3DKpPzDKZN9f/YzD45d/sqay+ghfkBGI+3+76LVQOyZjNYQ84lw+EOqDYbn28"
    "NQUyu6Kr4RYXowB4Wfitnhk/qcChz2VpZhf72N+lhHZZP6EmCHql5ckjbWb7owk/hlNCfYVYUr580JWsL6KcYc1ypc3WYw76KMrq"
    "oYidBdlPfvqGp/wTMxzVWDpcAGZb2FmnDl0sUESgWeCXxDS/kkIgeBh6mZpGK+bq6c96jqOmqxr2Lzgf//1oo86zRCQcLHY969Ii"
    "wBrg740Akh62JmbSmFnyUi4kJjFJ2HW1T/v2+TXuwOwve0m08b/HL1F2Cbqr6euOtIU3naej1Co/yTZAXw5xCP5O4LKy5x2Spqdk"
    "C+YWDTyA0Dm/owsVM6xbiGSVLRdYpObB994HYaJ7Tw0NPYAEPwLX8w+uCHZpj5lqK/RX0IirDzuVXNHQ+NPpDy3QgZHrtWpAVZKB"
    "v2sYjYAuHzlJvC3bMjdoUK8UmrrOy69mk77CWUd/ouasJMQ3sQkT00PzD2AF9Q1RHPVyFmUne0Y2nuU9UHMPGpOhUdPlXnokWHz4"
    "MfaSLfqAZbVQdJ+181DRH5J4wWqypNpwCfU9UTI/dCeotMiPdQCyuQMuv47X1rBfpi4+YX7P8wNllYbg+10DSxBYB/7cmEqXc+kB"
    "oDxNb1VYrHYnfvartrL1bXZiZ3p418M/WhfYrgt7dWg+v+UAvPhFiPvxVt7hG2TV/b2AuMVhSyUm5EqqrdwB9jBNmyucLP53ehFs"
    "k9XLGGZoGwc8ZWLuZ7HBiHrT1jw2v3fmDF0unerUune1O+WVURmitnP6Nnffbm9QfXPH/T9NCgt9uwvIF1I3TDkbO+z0cOXr7q0k"
    "Nr/vrP3rntni7o6QK1BWiXQpfWEyI1ek75+579H+aUUtrL1OlFdc7oHGaDVlrhZLd3r2gAXQbstp2tHTjhag/lvlDu2n8roE8x2h"
    "e3qGgG64EpK2hdZCOy19Ghqm9W1SFV3YU5RHWwzfpXQdH2+HDSegfN95PZQVJV+6j3EeoEBLO4bEb4PgN43O4q9K/H6lwnpKjq61"
    "R1FHhvJH2MNpfmTyvWxacVEXkCeJL4ZBPSupz6eSRGB8ADFfk1F0hqBUXk2xjHe3/Hesr95GTgr6yQ5edbZt4N4Sb1x6hN6qn503"
    "3/aaQeiosiWY0H51dMG6PDaXk63Zeq0O3T0UUtzhvA6cBXvHcScwdKfatdgO6kMaRKGT+mROQZPA2Wu5GyrTu1Y6oxhpOFArJu4M"
    "r9mwdGrrAEHiAuwHUC/ar6wE2jQ5/fPvrACuobWYNUal8C20cfOPWm0Sv/WFV3U4tvUTigRcp+fwfrcTxhWOceM/b7+7aT+dpNBT"
    "5haaniuLgS+KrXWZuGqp6HEa5OJa0V9vvYmIg8H7k3m15EHsFMeK0K5Osx6u9pVf2e5xemmIB9DzC/fhXjBfdCbcwvelo4Sp5z31"
    "0Aqvo64HPUCwGdgIrIk8DjVNNyurqcAfyl55OVGneccLjE+lw9jXFcb8Ys9ICITJSkL6L7c4m6heNlkVnTYUpEHqpI91whtcjpwm"
    "gGD1OuXBDgxzALsV4a58uYi00DDXZ82UVt5yVBmSF/J0RkC3Gt+qEKdXfPXEtjm6sirDvhaied7UdVEdIcHki+DJhQ1S1qotr77y"
    "Xqg66qb1DVjRi/tDPt5WYWsLPWu/DEc7/gLuq3t4cmQ408W6vsNMo0wl50c8/Is1t7xpat3fuBQYyg1UkhSwFe6j4gLy6Zeu/oWZ"
    "99fvDg2m03TQ8t52xk1kermy66Uc6m66OHrugePLj2o6NnffZv/6F7//te7Jmccb5Y7s1YzdUsT0JNloe+DtQhhqzBah+OhydQH7"
    "hSMcLJLupNJWUDyjJgUlXvbkbQUtVVqvoYNeGqiFYfn6DcJCnA5ZgdYe22mR5Me+6YyawFfI3i9+Dz4WTgMWu+LdIS1z1vBd1nqS"
    "2qioSAKn56YXoFhoP/RWmd4L8ceEBVn7eaxXer6rnWPNtr29F6Vd2G2VA0Qs3HqSqNbmERO9w3ljZG88MYoSNVJ//5lObVpX2c1o"
    "S8TqGoX6n1f7yH9HsMBSc3Rmy1Y0Rosou2U1V9h6regtm9eEaQd6o8BW730oTpv1yh/u6Z5ap6l8eTMuuKcdUx8fWephZwdT4Rav"
    "JmF1DUBCIncK0HxtWELLnF9qVzbN86w2rxP2i19X+POY3AP86qat32e3HEZgmaZaiq/iwwAPwoJjLxX4iI/6J84UgS1xthjSvrD6"
    "5ZDnwE+PVIHu0yezavpdO9UyKyaeX4u/7nJRde8U1AP7tzS/ezK566XFWvean7wDL7UN1z4glUsTrNSN0blZ+c/FluHLhdeC5Jl1"
    "txHmmyrntEZHWHeDMvsFqPxYpeq/Kve992h94EtWNASlX4XprdmMHl69Q0tGDs/z2YIIQX0nhURRkUE4JgMHHPwa/HxRjNwmITzE"
    "N6LxCR3cnEJmTC18L6lWACuM0f2AK4se0czJl4vv9buFhM1cHde1xELqDcfxJV/QJGu/Q6qrUrfwHQTP2bwQYRcX6rYfl19BfUr0"
    "tVx6im2Yxpcvx8l4vIFBQKopWgqhdgNClV+LZNRNaX1NW9ixNU9asYk1MVn03//jMYjdQU9Wc09mKc45cDv0j5QdgxHBARd15nhB"
    "16OdV87XxMAleKiNsNG0JU9SSMhu1WanHrmoUCD0WOGQorsczSFJM3/N/hEVANdJfc9/Nppv+F7WZQRLb5hTpnrtWYaL19kUz2A7"
    "eLyEgk41TniXWYWcHsjvFbl4nIHc8uf+p9dFbQiuEg8E9EJjp1vgWWvoSWKhSsZvGTkz/7wo0Dt/dGBKw6ITQLWAsOJ2DNkuvRfQ"
    "EmflHZSnM+oJj+NuCZcaqYmVDVDczdbqzUwmo/8A1qZ83FnvPpLBKwnCC0GxOzKVZeET3TmElsP2ZQFozGcAVmQjiR2pgHjWNUFU"
    "3KExUELGw9BHiO6qv72BjaKSjwNRF5Z8C3sB5lgo4/X6Qm4RT/wrnCjXEdsWa0IWCVaRi7VPXHgL8lfkh3WNeidttWFQMerhARZx"
    "FqSGOFk6ephT4pyxsv/3/CBBH/Dmbx+EPAGzDatX7MoqHdejzYhoDl0xwTsKrwv1BGKckjJudsEZGr/DxfY+qglwAPFWTUB9yvqp"
    "cCV9iBP0Zcmb/S7LUbBjZNAb+0/vk1g8BHMS9trhpmLJhCRwYxK+mn+JaxeJDyG0REdqvqJoxw4u7NtdCfolGB65sVrmw9NtpJ/Z"
    "YO0O7Xf3ZzQMCbF4C1mN1OnehPswMVJjZV0TuQ4BuMnvw8GuNapWjz67MbE3wzZWpsGiKiqvpem3dPhfyk5H47mAL+I2nhMuRVCg"
    "p0icgeVT1Mtck71BK5srcF1xcCVUykKiJ/b0OUPBLUKVXXuXiHPh9vs5q/VBpEZEpVP40xd7nnyuh26X6Eeg1lFe2uYtqZYJQZcz"
    "2O+uX6wpV/XFAr+VV5h2H/mcSEzalDl91Jc0/AMPcdMmcV8Lyqbgs885upgCHM7DbUrTI2slXG3rJ0unfT0unewx7h2kL+zTKzgY"
    "EzUtNW+f8dQTP1n0Nv/N6yTU3FQ85YTJj1bRKR26h1kLlue0W0XC8ij7XwHAAisgEzke5vkx7XD91gFZ79OQWcZ7fXl/lsNFewcX"
    "re3an8Cmhz134LeMLjZxGqtgm1dfkGxoxysIU8OoVJjOYw3KHZijDgTC0A97VAi2tDEwUm3UUJ2y8vp/G8yfl8nzPAJhHZSKP2Mf"
    "b/Dmq7CauaqV3alOY4VZYAGzFm0Y5oJSvS6/zcvo3xfSw7ID5Eq2OXe2aKWv+qq3MXZtV+ildISkXtM3QdZrfE9YkCyxjSICluHh"
    "gZBt5GLZBdMwyaT/gN7COXDVzZ7kSWsfAQTCDFYeqFrNC5fC4FLwWuEpF7g2vNPO8m9S9gfL+2RvKqWgfXT2PC1Rcxh8JORfLvFK"
    "4gvguq1cVXakLcLSIfp7byLsu3mYnDvY99GCFr0suj0zxL1W+S+ODfatk+7++IXC+Cr9GoepbmYoC/gHkYcwbvq969uZyjwnd2uy"
    "dc+YJBzAyLddIfSuTn//fzC2WA2Hwc04RuskLz/hQ9QfntHAwda8szdqG8LZGuKI9WMQWssmNhQ35dwFk0TiYxKTVk8jJMFOL91s"
    "G2WXVgfVl7kc09I9/e2jN22dq9H3jn0uneyaXTvZ1iQmViHBKaK7X/9//8Vy5b+1D32P0cpH5tWg+fF4fnox4ZTSFsq2IHr1/CmL"
    "/8wSblA9CJ9jkBvMPzcWw3XxWRceskfxHGydbl6zt7VinHHwv2AKtF5P0i8nIkTSfgNIqTGCHxsH+dRgGnStmx58Boyd5rf78SeS"
    "YcD0N+NFOffcAvYAbksD21y7+UVuER4O2pwb9d2Ml7j/tbsQyX7hMV0i4m+NruxzC+SDHn/E7xOZx3XwbebzXUdfQE6fy2JZbeR6"
    "nFqCrzO6xq6g8VJRs92lILr3AMbYdXEvl/BEBErqCmXQ3rE8op7QjHU5jxMBm7rwujNfIRxpEoq+Qy4PM2zkQfVBKyYi/Yqfp03c"
    "CVX908MLICs7XyhTYY0EkoZkW9ATjrkoHLd1d8xtU1GxIXH8LVmxtAv4jx43mQxlPqqzhANoPbgbPs+Yg+TR2BiDwmImswBzM/jI"
    "kz5Zt5XJkpH7Vp4G7MKu3nbaDJ+VD9IyJ7MQEQJ4k7p4eTSkpLF3NcvUtE1ojI/7L/9wbpw49DV5Cmcp1E5Jt219fGgO52zCmxdj"
    "iJmYx/yUaWj/K3jTJ9+BNZVYf3PV58t6MSIjIpIsupj7Yevsuqwn+0CO/enwDvtDHvYs9o4tpsPnbn6DWYBUtMq9TsWObSHwausZ"
    "oj1yemiQtSIW9OaIX3AQ1hOa6+1wC/SWOw1Vk5g/oxvSpc+k8Dp3suEtE8xDoqnuglcCaBKnFSwsoqRk3oAm1VUQGmvP4VkDvGb+"
    "0Fhvet+PL6Vt5AFW4V3JptEGc8f95O4Nd/8y23T9iKqUlU6Tg0UdVJmtuun3cRdhanBrsIK01qdtGwAeN74T/XjpB1CCO83Z04Im"
    "RO+ajm3Lp/h9l2/mOYvr4Es3NIqe3C+yvLs3+hcRCZFXbsETqXJ3gRamvWFIVpIPJerL/nRltGFYEk5cwOJu7SRhF5nGDbtqrOeO"
    "lT+Y2JyIVB3s1AbFnLMVqFWLtqBv6E9b+BO4E7RcTXyJXxq+X2ZsOc7Me0n6r0r/e3sncKBbsIY3S5XYStoE4pYPvTBsxJB82ODU"
    "WLgDHgkwUbqVrhUR/wO8D7CsqtQu8MZmPcb4nIc0EZKyk/SFwxYRrWl9C7jPJdhO66E3odxDutwY1PYX0J8iijeTdm/HgyoCEKUd"
    "WdGP+AGJObVfu635MYW/EWygfCsLL1Ph8mOoisf35NH+ZMoLNIN4SmJz5N5+F+7wOu2bZi7HFAT9j/WqAmOTYhYDVrb95tt4MfNV"
    "DVkfZzmTPcYoWFlrQFtqNfBPwKJr5Vs4PSKxgtyReBP7AH54Z5LGYBNYQvmGzBaJtTdfdRJmD5eddNPjYS882YOH1vpjoOAtuBz1"
    "kNXEwD1qWqdwI/DLzWXjti7/tOs38vIp04EsTVqQ8z/q7D7GJsVsj6HuaolC120E+1yZRppu02Z/l2bUW6p0SknxpvOwbbPj5ONQ"
    "Hr8Q452fv9oBcT9+xyGneyRkn28lCMNuhp4EvAiB0jOjUu1OWjqqswffYiajtBq7S9Axgfp7vsYeENtKk5dut3CuhwB5I/aWWENI"
    "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"
    "Jggg=="
)

MODULE_TERM_PATTERNS = (
    (re.compile(r"\bAssemblies\b"), "Modules"),
    (re.compile(r"\bAssembly\b"), "Module"),
    (re.compile(r"\bassemblies\b"), "modules"),
    (re.compile(r"\bassembly\b"), "module"),
)
SECURITY_ISSUE_PATTERN = re.compile(
    r"(security|credential|certificate|ssl|tls|sensitive|exposure|injection|plaintext|password|secret|token|trustall|mitm|insecure transport|certificate validation)",
    re.IGNORECASE,
)

def load_json(path):
    with open(path) as f:
        return json.load(f)

def load_file_analysis_jsons():
    files = {}
    for root, dirs, filenames in os.walk(SOURCE_JSONS_DIR):
        for fn in filenames:
            if fn.endswith('.combined.json'):
                full_path = Path(root) / fn
                data = load_json(full_path)
                rel_path = data.get('path', str(full_path.relative_to(SOURCE_JSONS_DIR)))
                files[rel_path] = data
    return files


def replace_module_terms(value):
    if isinstance(value, str):
        for pattern, replacement in MODULE_TERM_PATTERNS:
            value = pattern.sub(replacement, value)
        return value
    if isinstance(value, list):
        return [replace_module_terms(item) for item in value]
    if isinstance(value, dict):
        return {key: replace_module_terms(item) for key, item in value.items()}
    return value


def is_security_issue(issue):
    text = " | ".join(str(issue.get(key, "")) for key in ("type", "category", "description"))
    return bool(SECURITY_ISSUE_PATTERN.search(text))


def prune_hidden_metrics(value):
    if isinstance(value, dict):
        return {
            key: prune_hidden_metrics(item)
            for key, item in value.items()
            if key not in {"vulnerabilities", "total_vulnerabilities"}
        }
    if isinstance(value, list):
        return [prune_hidden_metrics(item) for item in value]
    return value


def case_preserving_replace(match, replacement):
    original = match.group(0)
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement.capitalize()
    return replacement


def sanitize_dashboard_text(value):
    if isinstance(value, str):
        replacements = (
            (r"\bsecurity vulnerabilities\b", "security risks"),
            (r"\bsecurity vulnerability\b", "security risk"),
            (r"\bvulnerabilities\b", "issues"),
            (r"\bvulnerability\b", "issue"),
        )
        for pattern, replacement in replacements:
            value = re.sub(pattern, lambda m, repl=replacement: case_preserving_replace(m, repl), value, flags=re.IGNORECASE)
        return value
    if isinstance(value, list):
        return [sanitize_dashboard_text(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_dashboard_text(item) for key, item in value.items()}
    return value


def file_data_uri(path):
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime_type};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def normalize_source_path(path_value):
    text = str(path_value or "").strip().replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    prefixes = []
    for candidate in (LEGACY_CODE_ROOT_NAME, LEGACY_PROJECT_NAME):
        token = str(candidate or "").strip().strip("/")
        if token and token not in prefixes:
            prefixes.append(token)
    changed = True
    while changed and text:
        changed = False
        for prefix in prefixes:
            marker = prefix + "/"
            if text.startswith(marker):
                text = text[len(marker):]
                changed = True
    return text


BRAND_ICON_DATA_URI = (
    "data:image/png;base64,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"
    "gErjQAAAAASUVORK5CYII="
)


def build_favicon_data_uri(logo_data_uri):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#020617" stroke="#1e293b" stroke-width="1.5"/>'
        f'<image href="{html_lib.escape(logo_data_uri, quote=True)}" '
        'x="8" y="7" width="48" height="50" preserveAspectRatio="xMidYMid meet"/>'
        "</svg>"
    )
    return "data:image/svg+xml;charset=UTF-8," + quote(svg, safe="")


FAVICON_DATA_URI = build_favicon_data_uri(BRAND_ICON_DATA_URI)


def resolve_markdown_asset_path(base_dir, target):
    target_path = Path(target)
    candidates = [target_path] if target_path.is_absolute() else [
        (base_dir / target_path).resolve(),
        (REPO_ROOT / target_path).resolve(),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    target_suffix = str(target_path).lstrip("./")
    for candidate in REPO_ROOT.rglob(target_path.name):
        rel_path = candidate.relative_to(REPO_ROOT).as_posix()
        if rel_path.endswith(target_suffix) or rel_path.endswith(target_path.name):
            return candidate.resolve()
    raise FileNotFoundError(f"Unable to resolve markdown asset: {target}")


def slugify_heading(text):
    slug = re.sub(r"<[^>]+>", "", text)
    slug = html_lib.unescape(slug).strip().lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug or "section"


def normalize_recommended_action(value):
    text = str(value or "").strip()
    if text.lower() == "refactor":
        return "Refactor/Upgrade"
    return text


def theme_mcm_visualization(raw_html):
    overrides = """
<style id="legacyleap-embed-theme">
html,body{background:#0f172a !important;color:#e2e8f0 !important}
body,.container{background:#0f172a !important}
.header{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%) !important;color:#e2e8f0 !important;border-bottom:1px solid #334155 !important;box-shadow:none !important}
.stat-item{background:rgba(148,163,184,0.16) !important;color:#e2e8f0 !important}
.sidebar,.main-content,.filters,.table-container,table,.details-panel,.legend,.controls-3d{background:#1e293b !important;color:#e2e8f0 !important}
.sidebar,.filters,.legend,.details-panel,.graph-container,.filter-group select,.filter-group input,.view-btn,.control-group button,.close-btn{border-color:#475569 !important}
.graph-container{background:#020617 !important}
.filter-group label,.legend h3,.controls-3d h3,.details-panel h2,.details-section h3,.details-section p,.details-section div{color:#cbd5e1 !important}
.filter-group select,.filter-group input,.view-btn,.control-group button,.close-btn{background:#0f172a !important;color:#e2e8f0 !important}
.filter-group select option{background:#0f172a !important;color:#e2e8f0 !important}
.view-btn.active,.view-btn:hover,.control-group button,.close-btn{background:#3b82f6 !important;color:#fff !important;border-color:#3b82f6 !important}
th{background:#0f172a !important;color:#94a3b8 !important}
td{color:#e2e8f0 !important;border-bottom-color:#334155 !important}
tr:hover{background:#334155 !important}
.details-panel{box-shadow:-14px 0 34px rgba(2,6,23,.45) !important}
.details-panel h2{border-bottom-color:#60a5fa !important}
.loading{color:#60a5fa !important}
</style>"""
    return raw_html.replace("</head>", overrides + "\n</head>", 1) if "</head>" in raw_html else overrides + raw_html


def render_markdown_inline(text, base_dir):
    placeholders = {}

    def reserve(fragment):
        key = f"__HTML_PLACEHOLDER_{len(placeholders)}__"
        placeholders[key] = fragment
        return key

    def image_repl(match):
        alt_text, raw_target, raw_attrs = match.group(1), match.group(2).strip(), match.group(3) or ""
        target = raw_target.split()[0]
        if re.match(r"^[a-z]+://", target, re.I) or target.startswith("data:"):
            src = target
        else:
            try:
                src = file_data_uri(resolve_markdown_asset_path(base_dir, target))
            except FileNotFoundError:
                return reserve(
                    '<div class="doc-missing-asset"><strong>'
                    + html_lib.escape(alt_text or "Missing image")
                    + '</strong><span>Asset not found: '
                    + html_lib.escape(target)
                    + '</span></div>'
                )
        style = ""
        width_match = re.search(r"width\s*=\s*([0-9.]+%?)", raw_attrs)
        if width_match:
            width_value = width_match.group(1)
            if width_value.endswith("%"):
                style = f' style="width:{width_value};"'
            else:
                style = f' style="width:{width_value}px;"'
        return reserve(f'<img src="{src}" alt="{html_lib.escape(alt_text)}"{style}>')

    def link_repl(match):
        label, target = match.group(1), match.group(2).strip()
        href = html_lib.escape(target, quote=True)
        text_html = render_markdown_inline(label, base_dir)
        if target.startswith("#"):
            return reserve(f'<a href="{href}">{text_html}</a>')
        return reserve(f'<a href="{href}" target="_blank" rel="noopener noreferrer">{text_html}</a>')

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)(\{[^}]+\})?", image_repl, text)
    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", link_repl, text)
    text = html_lib.escape(text)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{m.group(1)}</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: f"<strong>{m.group(1)}</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", lambda m: f"<em>{m.group(1)}</em>", text)
    for key, fragment in placeholders.items():
        text = text.replace(html_lib.escape(key), fragment)
    return text


def render_markdown_table(lines, base_dir):
    def parse_row(line):
        parts = [cell.strip() for cell in line.strip().strip("|").split("|")]
        return [render_markdown_inline(cell, base_dir) for cell in parts]

    headers = parse_row(lines[0])
    body_rows = [parse_row(line) for line in lines[2:]]
    html = ['<div class="doc-table-wrap"><table class="doc-table"><thead><tr>']
    html.extend(f"<th>{cell}</th>" for cell in headers)
    html.append("</tr></thead><tbody>")
    for row in body_rows:
        html.append("<tr>")
        html.extend(f"<td>{cell}</td>" for cell in row)
        html.append("</tr>")
    html.append("</tbody></table></div>")
    return "".join(html)


def render_markdown_document(md_path, document_name):
    lines = md_path.read_text(encoding="utf-8").splitlines()
    base_dir = md_path.parent
    blocks = []
    paragraph_lines = []
    list_items = []
    list_kind = None
    table_lines = []

    def flush_paragraph():
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines)
            blocks.append(f"<p>{render_markdown_inline(text, base_dir)}</p>")
            paragraph_lines = []

    def flush_list():
        nonlocal list_items, list_kind
        if list_items:
            tag = "ol" if list_kind == "ol" else "ul"
            blocks.append(f"<{tag}>" + "".join(f"<li>{item}</li>" for item in list_items) + f"</{tag}>")
            list_items = []
            list_kind = None

    def flush_table():
        nonlocal table_lines
        if table_lines:
            blocks.append(render_markdown_table(table_lines, base_dir))
            table_lines = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if table_lines and not (stripped.startswith("|") and stripped.endswith("|")):
            flush_table()

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            heading_html = render_markdown_inline(heading_text, base_dir)
            blocks.append(f'<h{level} id="{slugify_heading(heading_text)}">{heading_html}</h{level}>')
            continue

        if re.fullmatch(r"-{3,}", stripped):
            flush_paragraph()
            flush_list()
            blocks.append("<hr>")
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_paragraph()
            flush_list()
            table_lines.append(stripped)
            continue

        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if unordered_match:
            flush_paragraph()
            if list_kind == "ol":
                flush_list()
            list_kind = "ul"
            list_items.append(render_markdown_inline(unordered_match.group(1), base_dir))
            continue

        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if ordered_match:
            flush_paragraph()
            if list_kind == "ul":
                flush_list()
            list_kind = "ol"
            list_items.append(render_markdown_inline(ordered_match.group(1), base_dir))
            continue

        flush_list()
        paragraph_lines.append(stripped)

    flush_table()
    flush_paragraph()
    flush_list()

    if blocks and "This document was automatically generated" in blocks[-1]:
        blocks.pop()
        if blocks and blocks[-1] == "<hr>":
            blocks.pop()

    body_html = "\n".join(blocks)
    title_html = html_lib.escape(document_name)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_html}</title>
<link rel="icon" type="image/svg+xml" href="{FAVICON_DATA_URI}">
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:Georgia,'Times New Roman',serif;background:#f6f4ee;color:#1f2937;line-height:1.72}}
.doc-shell{{max-width:980px;margin:0 auto;padding:32px 32px 64px}}
h1,h2,h3,h4,h5,h6{{font-family:'Segoe UI',system-ui,sans-serif;color:#111827;line-height:1.25;margin:32px 0 14px}}
h1{{font-size:34px}}h2{{font-size:28px}}h3{{font-size:22px}}h4{{font-size:18px}}
p{{margin:0 0 16px}}
ul,ol{{margin:0 0 18px 22px;padding:0}}
li{{margin:0 0 8px}}
hr{{border:0;border-top:1px solid #d6d3d1;margin:28px 0}}
strong{{color:#111827}}
code{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',monospace;background:#efeae0;border-radius:4px;padding:2px 6px;font-size:.92em}}
a{{color:#1d4ed8;text-decoration:none}}
a:hover{{text-decoration:underline}}
img{{display:block;max-width:100%;height:auto;margin:22px auto;border:1px solid #d6d3d1;border-radius:12px;background:#fff;box-shadow:0 14px 30px rgba(15,23,42,.08)}}
.doc-missing-asset{{display:flex;flex-direction:column;gap:6px;margin:22px 0;padding:16px 18px;border:1px dashed #c2410c;border-radius:12px;background:#fff7ed;color:#9a3412;font:13px/1.5 'Segoe UI',system-ui,sans-serif}}
.doc-missing-asset strong{{color:#9a3412}}
.doc-table-wrap{{overflow:auto;margin:20px 0 24px;border:1px solid #d6d3d1;border-radius:12px;background:#fff}}
.doc-table{{width:100%;border-collapse:collapse;font:14px/1.55 'Segoe UI',system-ui,sans-serif}}
.doc-table th,.doc-table td{{padding:12px 14px;border-bottom:1px solid #e7e5e4;text-align:left;vertical-align:top}}
.doc-table th{{background:#f5efe2;font-weight:700;color:#111827}}
.doc-table tbody tr:nth-child(even){{background:#fafaf9}}
@media(max-width:768px){{.doc-shell{{padding:26px 18px 44px}}.doc-title{{font-size:28px}}h2{{font-size:24px}}h3{{font-size:20px}}}}
</style>
</head>
<body>
<main class="doc-shell">
  {body_html}
</main>
</body>
</html>"""

def _safe_render_doc_b64(doc_path, title):
    """Render a markdown doc to base64 HTML, returning empty string if doc is missing."""
    if doc_path and doc_path.exists():
        return base64.b64encode(
            render_markdown_document(doc_path, title).encode("utf-8")
        ).decode("ascii")
    return ""


def generate_dashboard():
    logo_data_uri = LOGO_DATA_URI
    favicon_data_uri = FAVICON_DATA_URI

    mcm_visualization_b64 = ""
    if MCM_VIS_PATH and MCM_VIS_PATH.exists():
        mcm_visualization_html = theme_mcm_visualization(MCM_VIS_PATH.read_text(encoding="utf-8"))
        mcm_visualization_b64 = base64.b64encode(mcm_visualization_html.encode("utf-8")).decode("ascii")

    application_overview_b64 = _safe_render_doc_b64(APPLICATION_OVERVIEW_PATH, "Application Overview")
    fsd_document_b64 = _safe_render_doc_b64(FSD_PATH, "Functional Specification Document")
    tsd_document_b64 = _safe_render_doc_b64(TSD_PATH, "Technical Specification Document")
    dependency_report_b64 = _safe_render_doc_b64(DEPENDENCY_REPORT_PATH, "Dependency Report")
    recommendations_b64 = _safe_render_doc_b64(RECOMMENDATIONS_PATH, "Modernization Recommendations")
    post_modernization_b64 = _safe_render_doc_b64(POST_MODERNIZATION_PATH, "Post Modernization Report")
    sheet1 = load_json(TECH_DIR / "sheet1.json")
    sheet2 = load_json(TECH_DIR / "sheet2.json")
    sheet3 = load_json(TECH_DIR / "sheet3.json")
    sheet4 = load_json(TECH_DIR / "sheet4.json")
    sheet7 = load_json(TECH_DIR / "sheet7.json")
    sheet8 = load_json(TECH_DIR / "sheet8.json")
    sheet9 = load_json(TECH_DIR / "sheet9.json")
    meta = load_json(META_PATH)
    file_analyses = load_file_analysis_jsons()

    if sheet1.get('data'):
        summary_row = sheet1['data'][0]
        summary_row['recommended_action'] = normalize_recommended_action(summary_row.get('recommended_action'))
        high_risk_files = int(sheet7.get('summary', {}).get('high_risk_files', 0) or 0)
        medium_risk_files = int(sheet7.get('summary', {}).get('medium_risk_files', 0) or 0)
        if high_risk_files == 1:
            summary_row['key_blocking_risks'] = "1 high-risk file requires attention"
        elif high_risk_files:
            summary_row['key_blocking_risks'] = f"{high_risk_files} high-risk files require attention"
        elif medium_risk_files:
            summary_row['key_blocking_risks'] = f"{medium_risk_files} medium-risk files merit targeted cleanup"
        else:
            summary_row['key_blocking_risks'] = "No critical blocking risks identified"

    if 'columns' in sheet7:
        sheet7['columns'] = [column for column in sheet7['columns'] if column != 'vulnerabilities']
    sheet7.get('summary', {}).pop('total_vulnerabilities', None)
    for row in sheet7.get('data', []):
        row.pop('vulnerabilities', None)

    sheet1 = sanitize_dashboard_text(sheet1)
    sheet2 = sanitize_dashboard_text(sheet2)
    sheet3 = sanitize_dashboard_text(sheet3)
    sheet4 = sanitize_dashboard_text(sheet4)
    sheet7 = sanitize_dashboard_text(sheet7)
    sheet8 = sanitize_dashboard_text(sheet8)
    sheet9 = sanitize_dashboard_text(sheet9)
    meta = sanitize_dashboard_text(meta)
    file_analyses = {path: sanitize_dashboard_text(data) for path, data in file_analyses.items()}

    for row in sheet7.get('data', []):
        row['path'] = normalize_source_path(row.get('path', ''))
    for issue in sheet9.get('issues', []):
        issue['path'] = normalize_source_path(issue.get('path', ''))
    for suggestion in sheet9.get('suggestions', []):
        suggestion['path'] = normalize_source_path(suggestion.get('path', ''))
    for part in meta.get('nodes', {}).get('parts', []):
        identity = part.setdefault('identity', {})
        identity['file_path'] = normalize_source_path(identity.get('file_path', ''))
    normalized_file_analyses = {}
    for path, data in file_analyses.items():
        normalized_path = normalize_source_path(path)
        if isinstance(data, dict):
            data['path'] = normalized_path
        normalized_file_analyses[normalized_path] = data
    file_analyses = normalized_file_analyses

    sheet2 = replace_module_terms(sheet2)
    sheet4 = replace_module_terms(sheet4)
    meta = replace_module_terms(meta)

    def build_tree(paths):
        tree = {}
        for p in paths:
            parts = p.split('/')
            node = tree
            for part in parts[:-1]:
                if part not in node:
                    node[part] = {}
                node = node[part]
            node[parts[-1]] = None
        return tree

    file_paths = [d['path'] for d in sheet7['data']]
    tree = build_tree(file_paths)
    # Key by relative path (unique identifier). Basenames/class names collide
    # in real codebases (e.g. duplicate `index.js`, `Program.cs`, `utils.py`
    # in different folders/namespaces) which would cause later entries to
    # overwrite earlier ones and silently display wrong data.
    file_metrics = {d['path']: d for d in sheet7['data']}

    meta_parts_by_name = {}
    meta_parts_by_path = {}
    for part in meta.get('nodes', {}).get('parts', []):
        name = part.get('identity', {}).get('name', '')
        fp = part.get('identity', {}).get('file_path', '')
        if name:
            meta_parts_by_name[name] = part
        if fp:
            meta_parts_by_path[fp] = part

    assemblies = meta.get('nodes', {}).get('assemblies', [])
    relationships = meta.get('relationships', [])
    assembly_ids = {assembly.get('id') for assembly in assemblies}
    class_part_ids = {
        part.get('id') for part in meta.get('nodes', {}).get('parts', [])
        if part.get('kind') == 'Class' or str(part.get('id', '')).startswith('part-class-')
    }
    direct_assembly_to_parts = {}
    part_to_assemblies = {}
    assembly_children = {}

    def add_membership(mapping, key, value):
        if key and value:
            mapping.setdefault(key, set()).add(value)

    for rel in relationships:
        rel_type = rel.get('type')
        source_id = rel.get('from', '')
        target_id = rel.get('to', '')
        if rel_type == 'CONTAINS':
            if source_id in assembly_ids and target_id in class_part_ids:
                add_membership(direct_assembly_to_parts, source_id, target_id)
                add_membership(part_to_assemblies, target_id, source_id)
        elif rel_type == 'BELONGS_TO':
            if source_id in class_part_ids and target_id in assembly_ids:
                add_membership(direct_assembly_to_parts, target_id, source_id)
                add_membership(part_to_assemblies, source_id, target_id)
            elif source_id in assembly_ids and target_id in assembly_ids:
                add_membership(assembly_children, target_id, source_id)

    def collect_assembly_parts(assembly_id, seen=None):
        if seen is None:
            seen = set()
        if assembly_id in seen:
            return set()
        nested_seen = seen | {assembly_id}
        parts = set(direct_assembly_to_parts.get(assembly_id, set()))
        for child_id in assembly_children.get(assembly_id, set()):
            parts.update(collect_assembly_parts(child_id, nested_seen))
        return parts

    assembly_to_parts = {}
    for assembly in assemblies:
        assembly_id = assembly.get('id')
        parts = collect_assembly_parts(assembly_id)
        if parts:
            assembly_to_parts[assembly_id] = sorted(parts)

    part_to_assemblies = {part_id: sorted(assembly_set) for part_id, assembly_set in part_to_assemblies.items()}

    part_id_to_name = {}
    for part in meta.get('nodes', {}).get('parts', []):
        part_id_to_name[part['id']] = part.get('identity', {}).get('name', '')

    # Key issues/suggestions by relative path to avoid basename collisions.
    # Fall back to filename only if a path is absent in the record.
    issues_by_file = {}
    for issue in sheet9.get('issues', []):
        key = issue.get('path') or issue.get('filename', '')
        if not key:
            continue
        issues_by_file.setdefault(key, []).append(issue)

    suggestions_by_file = {}
    for sug in sheet9.get('suggestions', []):
        key = sug.get('path') or sug.get('filename', '')
        if not key:
            continue
        suggestions_by_file.setdefault(key, []).append(sug)

    # file_analyses is already keyed by the relative source path
    # (from each .combined.json's `path` field) so reuse that directly.
    detailed_by_file = {
        path: prune_hidden_metrics(data)
        for path, data in file_analyses.items()
    }

    all_security_zones, all_arch_layers, all_domains = set(), set(), set()
    for part in meta.get('nodes', {}).get('parts', []):
        b = part.get('boundary', {})
        if b.get('security_zone'): all_security_zones.add(b['security_zone'])
        if b.get('architecture_layer'): all_arch_layers.add(b['architecture_layer'])
        if b.get('domain'): all_domains.add(b['domain'])

    FILE_COUNT = sheet7.get('total_files_analyzed', len(sheet7.get('data', [])))
    total_loc_from_metadata = _METADATA.get("total_loc")
    try:
        TOTAL_LOC = int(total_loc_from_metadata) if total_loc_from_metadata is not None else None
    except (TypeError, ValueError):
        TOTAL_LOC = None
    if TOTAL_LOC is None:
        TOTAL_LOC = int(sheet7.get('summary', {}).get('total_lines', 0) or 0)

    data_b64 = base64.b64encode(json.dumps({
        'sheet1': sheet1, 'sheet2': sheet2, 'sheet3': sheet3, 'sheet4': sheet4,
        'sheet7': sheet7, 'sheet8': sheet8, 'sheet9': sheet9,
        'fileMetrics': file_metrics, 'issuesByFile': issues_by_file,
        'suggestionsByFile': suggestions_by_file, 'detailedByFile': detailed_by_file,
        'tree': tree, 'filePaths': file_paths,
        'metaPartsByName': meta_parts_by_name,
        'metaPartsByPath': meta_parts_by_path,
        'assemblies': assemblies, 'relationships': relationships,
        'assemblyToParts': assembly_to_parts, 'partToAssemblies': part_to_assemblies,
        'partIdToName': part_id_to_name,
        'securityZones': sorted(all_security_zones),
        'archLayers': sorted(all_arch_layers),
        'domains': sorted(all_domains),
        'fileExtension': FILE_EXTENSION,
        'technology': TECH_LABEL,
        'totalLoc': TOTAL_LOC,
    }, default=str).encode("utf-8")).decode("ascii")

    APP_NAME = sheet1.get('data', [{}])[0].get('application_name', PROJECT_NAME)
    app_tab_title_html = html_lib.escape(APP_TAB_TITLE)
    app_name_html = html_lib.escape(APP_NAME)
    tech_label_html = html_lib.escape(TECH_LABEL)

    # Build HTML in parts to avoid f-string brace escaping issues
    CSS = """
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0f172a;--surface:#1e293b;--surface2:#334155;--border:#475569;--text:#e2e8f0;--text2:#94a3b8;--accent:#3b82f6;--accent2:#8b5cf6;--red:#ef4444;--orange:#f97316;--yellow:#eab308;--green:#22c55e;--red-bg:rgba(239,68,68,0.15);--orange-bg:rgba(249,115,22,0.15);--yellow-bg:rgba(234,179,8,0.15);--green-bg:rgba(34,197,94,0.15)}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;min-height:100vh}
a{color:var(--accent);text-decoration:none;cursor:pointer}a:hover{text-decoration:underline}
.page-shell{min-height:100vh;height:100vh;display:flex;flex-direction:column;position:relative;overflow:hidden}
.page-shell::before{content:'';position:fixed;inset:0;background:url('__LOGO_DATA_URI__') center 56%/min(46vw,480px) auto no-repeat;opacity:.13;filter:grayscale(1) brightness(1.7);pointer-events:none;z-index:0}
.page-header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 24px;background:rgba(15,23,42,0.92);backdrop-filter:blur(12px);position:relative;z-index:1;border-bottom:1px solid var(--border)}
.brand-lockup{display:flex;align-items:center;gap:14px;min-width:0}
.brand-logo{display:block;height:38px;width:auto;object-fit:contain;flex-shrink:0}
.brand-eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:1.6px;color:var(--text2)}
.brand-title{font-size:18px;font-weight:700;line-height:1.15}
.page-header-meta{font-size:12px;color:var(--text2);text-align:right}
.app{display:flex;flex:1;min-height:0;overflow:hidden;position:relative;z-index:1}
.sidebar{width:320px;min-width:320px;background:var(--surface);border-right:1px solid var(--border);display:flex;flex-direction:column;transition:width .2s ease,min-width .2s ease}
.sidebar.is-collapsed{width:64px;min-width:64px}
.sidebar.is-collapsed .sidebar-header-copy,.sidebar.is-collapsed .sidebar-nav,.sidebar.is-collapsed .sidebar-search,.sidebar.is-collapsed .sidebar-content{display:none}
.sidebar.is-collapsed .sidebar-header{justify-content:center;padding:14px 10px}
.main{flex:1;overflow-y:auto;padding:24px}
.sidebar-header{padding:16px 18px;border-bottom:1px solid var(--border);display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.sidebar-header-copy{min-width:0}
.sidebar-header h2{font-size:12px;text-transform:uppercase;letter-spacing:1.5px;color:var(--text2);margin-bottom:6px}
.sidebar-header .app-name{font-size:18px;font-weight:700}
.sidebar-header .app-meta{font-size:12px;color:var(--text2);margin-top:2px}
.sidebar-toggle{width:40px;height:40px;padding:6px;border:1px solid var(--border);border-radius:12px;background:var(--bg);cursor:pointer;transition:all .15s;flex-shrink:0;display:inline-flex;align-items:center;justify-content:center}
.sidebar-toggle:hover{border-color:var(--accent);box-shadow:0 0 0 2px rgba(59,130,246,0.16)}
.sidebar-toggle-logo{width:100%;height:100%;display:block;object-fit:contain}
.sidebar-toggle.is-collapsed .sidebar-toggle-logo{transform:scale(.92)}
.sidebar-nav{display:flex;flex-wrap:wrap;border-bottom:1px solid var(--border)}
.sidebar-nav-btn{flex:1 1 50%;padding:10px;text-align:center;font-size:12px;font-weight:600;color:var(--text2);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s}
.sidebar-nav-btn:hover,.sidebar-nav-btn.active{color:var(--accent);border-bottom-color:var(--accent)}
.sidebar-search{padding:10px 14px;border-bottom:1px solid var(--border)}
.sidebar-search input{width:100%;padding:7px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:12px;outline:none}
.sidebar-search input:focus{border-color:var(--accent)}
.sidebar-content{flex:1;overflow-y:auto;padding:6px 0}
.tree-item{cursor:pointer;user-select:none}
.tree-label{display:flex;align-items:center;padding:4px 8px 4px 0;font-size:12px;transition:background .15s;border-radius:4px;margin:1px 6px}
.tree-label:hover{background:var(--surface2)}
.tree-label.active{background:rgba(59,130,246,0.2);color:var(--accent)}
.tree-icon{width:16px;margin-right:5px;font-size:11px;flex-shrink:0;text-align:center}
.tree-icon.folder{color:var(--yellow)}.tree-icon.folder-closed{color:var(--text2)}
.tree-icon.file{color:var(--text2);font-size:13px}
.tree-children{display:none;margin-left:8px;padding-left:8px;border-left:1px solid var(--border)}
.tree-children.open{display:block}
.tree-indent{display:inline-block;width:16px;flex-shrink:0}
.tree-badge{margin-left:auto;font-size:10px;padding:1px 6px;border-radius:8px;font-weight:600}
.tree-folder-name{font-weight:600;color:var(--text);font-size:12px}
.tree-file-name{color:var(--text);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.badge-high{background:var(--red-bg);color:var(--red)}.badge-medium{background:var(--orange-bg);color:var(--orange)}.badge-low{background:var(--green-bg);color:var(--green)}
.assembly-item{padding:8px 14px;cursor:pointer;font-size:12px;transition:background .15s;border-left:3px solid transparent}
.assembly-item:hover{background:var(--surface2)}.assembly-item.active{background:rgba(59,130,246,0.15);border-left-color:var(--accent)}
.assembly-name{font-weight:600}.assembly-meta{font-size:11px;color:var(--text2)}
.resource-item{padding:12px 14px;cursor:pointer;transition:background .15s,border-color .15s;border-left:3px solid transparent}
.resource-item:hover{background:var(--surface2)}
.resource-item.active{background:rgba(59,130,246,0.15);border-left-color:var(--accent)}
.resource-type{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--text2);margin-bottom:4px}
.resource-name{font-size:13px;font-weight:700;color:var(--text)}
.resource-meta{font-size:11px;color:var(--text2);margin-top:4px}
.tabs{display:flex;gap:2px;margin-bottom:20px;border-bottom:2px solid var(--border);overflow-x:auto}
.tab{padding:10px 18px;cursor:pointer;font-size:13px;font-weight:600;color:var(--text2);border-bottom:2px solid transparent;margin-bottom:-2px;transition:all .15s;white-space:nowrap}
.tab:hover{color:var(--text)}.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.panel{display:none}.panel.active{display:block}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px;margin-bottom:14px}
.card h3{font-size:15px;margin-bottom:10px}
.card-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.stat-card{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;text-align:center;cursor:pointer;transition:all .15s;display:flex;flex-direction:column;justify-content:center;min-height:108px}
.stat-card:hover{border-color:var(--accent);transform:translateY(-1px);box-shadow:0 0 0 2px rgba(59,130,246,0.2)}
.stat-value{font-size:clamp(18px,2vw,24px);font-weight:700;line-height:1.08;overflow-wrap:anywhere;word-break:break-word}.stat-label{font-size:11px;color:var(--text2);margin-top:6px;text-transform:uppercase;letter-spacing:.5px}
.stat-meta{font-size:10px;color:var(--text2);margin-top:4px;line-height:1.35}
.stat-red{color:var(--red)}.stat-orange{color:var(--orange)}.stat-yellow{color:var(--yellow)}.stat-green{color:var(--green)}.stat-blue{color:var(--accent)}.stat-purple{color:var(--accent2)}
.table-wrap{overflow-x:auto;max-height:500px;overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:12px}
th{text-align:left;padding:8px 10px;background:var(--bg);color:var(--text2);font-weight:600;text-transform:uppercase;font-size:10px;letter-spacing:.5px;position:sticky;top:0;z-index:1}
td{padding:7px 10px;border-bottom:1px solid var(--border);vertical-align:top}
tr:hover td{background:var(--surface2)}
.tag{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer}.tag:hover{opacity:.8}
.tag-bug{background:var(--red-bg);color:var(--red)}.tag-smell{background:var(--yellow-bg);color:var(--yellow)}.tag-cognitive{background:var(--orange-bg);color:var(--orange)}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.chart-box{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px}
.chart-box.full-width{grid-column:1/-1}
.chart-box h4{font-size:13px;margin-bottom:10px;color:var(--text2)}
canvas{max-height:280px}
.filters{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px}
.filter-btn{padding:5px 12px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text2);cursor:pointer;font-size:11px;transition:all .15s}
.filter-btn:hover{border-color:var(--accent);color:var(--text)}.filter-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.conf-bar{width:50px;height:5px;background:var(--bg);border-radius:3px;overflow:hidden;display:inline-block;vertical-align:middle;margin-left:4px}
.conf-fill{height:100%;border-radius:3px}
.risk-badge{padding:3px 10px;border-radius:12px;font-size:11px;font-weight:700;text-transform:uppercase;cursor:pointer}.risk-badge:hover{opacity:.8}
.collapsible-header{cursor:pointer;display:flex;align-items:center;justify-content:space-between;padding:4px 0}
.collapsible-header::after{content:'\\25BC';font-size:9px;transition:transform .2s}
.collapsible-header.open::after{transform:rotate(180deg)}
.collapsible-body{display:none;padding-top:10px}.collapsible-body.open{display:block}
.file-header{display:flex;align-items:center;gap:14px;margin-bottom:16px;flex-wrap:wrap}
.file-header h2{font-size:20px}
.file-path{font-size:12px;color:var(--text2);font-family:monospace}
.nfr-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.nfr-item{text-align:left;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px}
.nfr-label{font-size:10px;color:var(--text2);margin-bottom:6px;text-transform:uppercase;letter-spacing:.04em}
.nfr-bar{height:6px;background:var(--bg);border-radius:3px;overflow:hidden}
.nfr-fill{height:100%;border-radius:3px}
.nfr-val{font-size:12px;font-weight:700;margin-top:6px}
.nfr-scale{font-size:10px;color:var(--text2);margin-top:4px;line-height:1.35}
.intent-text,.behavior-text,.impact-text{font-size:13px;color:var(--text2);line-height:1.6;margin:0}
.intent-text{font-style:italic;color:var(--text);border-left:3px solid var(--accent);padding-left:12px}
.zone-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer}
.zone-Sensitive{background:rgba(239,68,68,0.15);color:var(--red)}.zone-Restricted{background:rgba(249,115,22,0.15);color:var(--orange)}.zone-PublicAPI{background:rgba(59,130,246,0.15);color:var(--accent)}
.layer-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer}
.layer-Data{background:rgba(139,92,246,0.15);color:var(--accent2)}.layer-Business{background:rgba(34,197,94,0.15);color:var(--green)}
.kind-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;background:rgba(59,130,246,0.1);color:var(--accent)}
.breadcrumb{display:flex;align-items:center;gap:8px;margin-bottom:16px;font-size:13px;color:var(--text2)}
.dep-chip{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;margin:2px;cursor:pointer;background:var(--surface2);color:var(--text);transition:all .15s}
.dep-chip:hover{background:var(--accent);color:#fff}
.viz-card{padding:0;overflow:hidden}
.viz-frame{width:100%;height:calc(100vh - 290px);min-height:760px;border:0;display:block;background:var(--surface)}
.doc-toolbar{display:flex;gap:10px;flex-wrap:wrap;padding:16px 18px;border-bottom:1px solid var(--border);background:rgba(15,23,42,0.45)}
.doc-btn{padding:9px 14px;border:1px solid var(--border);border-radius:999px;background:rgba(51,65,85,0.45);color:var(--text);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s}
.doc-btn:hover{border-color:var(--accent);color:#fff;background:rgba(59,130,246,0.25)}
.doc-btn.active{border-color:var(--accent);background:var(--accent);color:#fff}
::-webkit-scrollbar{width:5px;height:5px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:var(--surface2);border-radius:3px}
@media(max-width:900px){.app{flex-direction:column}.sidebar,.sidebar.is-collapsed{width:100%;min-width:0;max-height:42vh}.chart-row{grid-template-columns:1fr}.page-header{padding:12px 16px;flex-direction:column;align-items:flex-start}.page-header-meta{text-align:left}.brand-logo{height:32px}.main{padding:18px}.viz-frame{height:70vh;min-height:560px}.doc-toolbar{padding:14px 16px}}
"""

    # JavaScript - write as a separate block to avoid f-string brace issues
    JS = """
function decodeBase64Utf8(b64){
  var binary=atob(b64),bytes=new Uint8Array(binary.length);
  for(var i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}
const D=JSON.parse(decodeBase64Utf8(DATA_PLACEHOLDER));
const MCM_VIS_B64=MCM_VIS_PLACEHOLDER;
const DOC_APPLICATION_OVERVIEW_B64=DOC_APPLICATION_OVERVIEW_PLACEHOLDER;
const DOC_FSD_B64=DOC_FSD_PLACEHOLDER;
const DOC_TSD_B64=DOC_TSD_PLACEHOLDER;
const DOC_DEPENDENCY_B64=DOC_DEPENDENCY_PLACEHOLDER;
const DOC_RECOMMENDATIONS_B64=DOC_RECOMMENDATIONS_PLACEHOLDER;
const DOC_POST_MODERNIZATION_B64=DOC_POST_MODERNIZATION_PLACEHOLDER;
let sidebarMode='files',currentIssueType='all',currentIssueFile='all',currentSugFile='all',currentIssueScope='all';
let charts={};
let currentDocument='application_overview',currentSidebarResource='application_overview';

function rc(r){return r==='High'?'var(--red)':r==='Medium'?'var(--orange)':'var(--green)'}
function rb(r){return r==='High'?'var(--red-bg)':r==='Medium'?'var(--orange-bg)':'var(--green-bg)'}
function nc(v){return v<=2?'var(--green)':v<=3?'var(--yellow)':v<=4?'var(--orange)':'var(--red)'}
function tc2(v){return v>=80?'var(--green)':v>=60?'var(--yellow)':v>=40?'var(--orange)':'var(--red)'}
function tc(t){return t==='Bug'?'tag-bug':t==='Code_Smell'?'tag-smell':'tag-cognitive'}
function ft(t){return t==='Code_Smell'?'Code Smell':t==='Cognitive_complexity'?'Cognitive':t}
function cb(c){const k=c>=0.9?'var(--red)':c>=0.7?'var(--orange)':'var(--yellow)';return '<span class="conf-bar"><span class="conf-fill" style="width:'+c*100+'%;background:'+k+'"></span></span>'}
function moduleName(name){return String(name||'').replace(/\\bAssemblies\\b/g,'Modules').replace(/\\bAssembly\\b/g,'Module').replace(/\\bassemblies\\b/g,'modules').replace(/\\bassembly\\b/g,'module')}
function escHtml(s){return String(s===null||s===undefined?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')}
function escAttr(s){return escHtml(s)}
function escClassToken(s){return String(s===null||s===undefined?'':s).toLowerCase().replace(/[^a-z0-9_-]/g,'')}
function clampNum(v,min,max){v=Number(v);if(!isFinite(v))return min;return Math.min(Math.max(v,min),max)}
function metricScaleText(key){
  var map={
    security_risk_rating:'1 = best, 5 = baf',
    nfr_security_rating:'1 = best, 5 = worst',
    nfr_maintainability_rating:'1 = best, 5 = worst',
    nfr_reliability_rating:'1 = best, 5 = worst',
    cloud_compatibiliy_rating:'1 = best compatibility, 5 = worst',
    nfr_extensibility_rating:'1 = most extensible, 5 = least extensible',
    nfr_reusability_rating:'1 = highly reusable, 5 = not reusable',
    nfr_scalability_rating:'1 = high scalability, 5 = poor scalability',
    nfr_testability_rating:'0 = worst, 100 = best'
  };
  return map[key]||'';
}
function metricDisplayValue(key,value){
  if(value===null||value===undefined||value==='')return 'N/A';
  if(key==='nfr_testability_rating')return Math.round(clampNum(value,0,100))+'/100';
  return Math.round(clampNum(value,1,5))+'/5';
}
function metricFillWidth(key,value){
  if(value===null||value===undefined||value==='')return 0;
  if(key==='nfr_testability_rating')return clampNum(value,0,100);
  return (6-clampNum(value,1,5))/5*100;
}
function metricColor(key,value){
  if(value===null||value===undefined||value==='')return 'var(--text2)';
  if(key==='nfr_testability_rating')return tc2(clampNum(value,0,100));
  return nc(clampNum(value,1,5));
}
function summaryCard(content,label,title,onclick){
  var attrs=' class="stat-card"';
  if(title)attrs+=' title="'+escAttr(title)+'"';
  if(onclick)attrs+=' onclick="'+onclick+'"';
  else attrs+=' style="cursor:help"';
  return '<div'+attrs+'>'+content+'<div class="stat-label">'+label+'</div></div>';
}
function isSecurityIssue(i){
  var text=[i.type||'',i.category||'',i.description||''].join(' | ').toLowerCase();
  return /(security|credential|certificate|ssl|tls|sensitive|exposure|injection|plaintext|password|secret|token|trustall|mitm|insecure transport|certificate validation)/.test(text);
}
function issueSearchText(i){return [i.filename||'',ft(i.type||''),i.type||'',i.category||'',i.description||'',i.issue_location||'',i.path||''].join(' ').toLowerCase()}
function suggestionSearchText(s){return [s.filename||'',s.suggestion||'',s.code_suggestion||'',s.path||''].join(' ').toLowerCase()}
function filterIssues(){renderIssues()}
function filterSuggestions(){renderSuggestions()}
function sq(s){return String(s===null||s===undefined?'':s).replace(/\\\\/g,'\\\\\\\\').replace(/'/g,"\\\\'").replace(/\\r/g,'\\\\r').replace(/\\n/g,'\\\\n').replace(/\\u2028/g,'\\\\u2028').replace(/\\u2029/g,'\\\\u2029')}
function filterIssueCategory(category){
  var input=document.getElementById('issueSearch');
  if(input)input.value=category||'';
  renderIssues();
}
function loadMcmVisualization(){
  var frame=document.getElementById('mcmFrame');
  if(frame&&!frame.dataset.loaded){
    frame.srcdoc=decodeBase64Utf8(MCM_VIS_B64);
    frame.dataset.loaded='1';
  }
}
function loadDocument(name){
  currentDocument=name||currentDocument;
  currentSidebarResource=currentDocument;
  var frame=document.getElementById('docFrame');
  if(frame){
    var sources={application_overview:DOC_APPLICATION_OVERVIEW_B64,fsd:DOC_FSD_B64,tsd:DOC_TSD_B64,dependency:DOC_DEPENDENCY_B64,recommendations:DOC_RECOMMENDATIONS_B64,post_modernization:DOC_POST_MODERNIZATION_B64};
    frame.srcdoc=decodeBase64Utf8(sources[currentDocument]||DOC_APPLICATION_OVERVIEW_B64);
  }
  document.querySelectorAll('.doc-btn').forEach(function(btn){
    btn.classList.toggle('active', btn.dataset.doc===currentDocument);
  });
  if(sidebarMode==='resources')renderSidebar();
}

function switchTab(name,el){
  document.querySelectorAll('.tab').forEach(function(t){t.classList.remove('active')});
  document.querySelectorAll('.panel').forEach(function(p){p.classList.remove('active')});
  if(el)el.classList.add('active');
  else{var tb=document.querySelector('.tab[data-tab="'+name+'"]');if(tb)tb.classList.add('active')}
  document.getElementById('panel-'+name).classList.add('active');
  if(name==='issues')renderIssues();
  if(name==='suggestions')renderSuggestions();
  if(name==='assemblies')renderAssembliesTab();
  if(name==='mcm'){currentSidebarResource='mcm';loadMcmVisualization();if(sidebarMode==='resources')renderSidebar()}
  if(name==='documents')loadDocument(currentDocument);
}

function toggleSidebar(){
  var sidebar=document.getElementById('sidebar');
  var btn=document.getElementById('sidebarToggle');
  if(!sidebar)return;
  sidebar.classList.toggle('is-collapsed');
  if(btn){
    var collapsed=sidebar.classList.contains('is-collapsed');
    btn.classList.toggle('is-collapsed', collapsed);
    btn.setAttribute('aria-label', collapsed?'Expand sidebar':'Collapse sidebar');
    btn.setAttribute('title', collapsed?'Expand sidebar':'Collapse sidebar');
  }
}

function switchSidebar(mode,el){
  sidebarMode=mode;
  document.querySelectorAll('.sidebar-nav-btn').forEach(function(b){b.classList.remove('active')});
  if(el)el.classList.add('active');
  var search=document.getElementById('sidebarSearch');
  if(search){
    search.value='';
    search.placeholder=mode==='resources'?'Search resources...':'Search...';
  }
  renderSidebar();
}

function renderSidebar(){
  var c=document.getElementById('sidebarContent');
  if(sidebarMode==='files')c.innerHTML=buildTreeHTML(D.tree,'');
  else if(sidebarMode==='assemblies')c.innerHTML=buildAssemblyList();
  else c.innerHTML=buildResourceList();
}

function buildAssemblyList(){
  var html='';
  D.assemblies.forEach(function(a){
    var parts=D.assemblyToParts[a.id]||[];
    if(!parts.length)return;
    var name=moduleName(a.identity.name);
    html+='<div class="assembly-item" data-id="'+escAttr(a.id)+'" onclick="showAssembly(\\''+sq(a.id)+'\\')" data-name="'+escAttr(name.toLowerCase())+'"><div class="assembly-name">'+escHtml(name)+'</div><div class="assembly-meta">'+parts.length+' components</div></div>';
  });
  return html;
}

function buildResourceList(){
  function item(kind,kindLabel,name,meta){
    var active=currentSidebarResource===kind?' active':'';
    var dataName=(kindLabel+' '+name+' '+meta).toLowerCase();
    return '<div class="resource-item'+active+'" onclick="openResource(\\''+sq(kind)+'\\')" data-name="'+escAttr(dataName)+'"><div class="resource-type">'+escHtml(kindLabel)+'</div><div class="resource-name">'+escHtml(name)+'</div><div class="resource-meta">'+escHtml(meta)+'</div></div>';
  }
  return item('application_overview','Document','Application Overview','Application context and business summary')
    + item('fsd','Document','Functional Specification','Functional Specification Document')
    + item('tsd','Document','Technical Specification','Technical Specification Document')
    + item('dependency','Document','Dependency Report','Dependency mapping and relationships')
    + item('recommendations','Document','Recommendations','Modernization recommendations and roadmap')
    + item('post_modernization','Document','Post Modernization','Post modernization Document')
    + item('mcm','Visualization','Meta Cognitive BOM','Interactive architecture view');
}

function openResource(kind){
  currentSidebarResource=kind;
  if(kind==='mcm')switchTab('mcm');
  else{
    currentDocument=kind;
    switchTab('documents');
  }
  if(sidebarMode==='resources')renderSidebar();
}

function buildTreeHTML(node,path){
  var html='';
  var entries=Object.entries(node).sort(function(a,b){
    var ad=a[1]!==null,bd=b[1]!==null;
    if(ad&&!bd)return -1;if(!ad&&bd)return 1;return a[0].localeCompare(b[0]);
  });
  entries.forEach(function(e){
    var name=e[0],children=e[1];
    var fp=path?path+'/'+name:name;
    if(children===null){
      var fm=D.fileMetrics[fp],risk=fm?fm.risk_category:'',bugs=fm?fm.bugs:0;
      html+='<div class="tree-item" data-path="'+escAttr(fp)+'" data-name="'+escAttr(name.toLowerCase())+'" onclick="showFile(\\''+sq(name)+'\\',\\''+sq(fp)+'\\')"><div class="tree-label"><span class="tree-icon file">&#128196;</span><span class="tree-file-name">'+escHtml(name)+'</span>'+(risk?'<span class="tree-badge badge-'+escClassToken(risk)+'">'+bugs+'</span>':'')+'</div></div>';
    }else{
      html+='<div class="tree-item" data-name="'+escAttr(name.toLowerCase())+'"><div class="tree-label" onclick="this.parentElement.querySelector(\\'.tree-children\\').classList.toggle(\\'open\\');var ic=this.querySelector(\\'.tree-chevron\\');ic.textContent=ic.textContent===\\'\\u25B6\\'?\\'\\u25BC\\':\\'\\u25B6\\';var fi=this.querySelector(\\'.tree-icon\\');fi.classList.toggle(\\'folder\\');fi.classList.toggle(\\'folder-closed\\')"><span class="tree-chevron" style="font-size:8px;width:10px;display:inline-block;flex-shrink:0;color:var(--text2)">&#9654;</span><span class="tree-icon folder-closed">&#128193;</span><span class="tree-folder-name">'+escHtml(name)+'</span></div><div class="tree-children">'+buildTreeHTML(children,fp)+'</div></div>';
    }
  });
  return html;
}

function filterSidebar(q){
  q=q.toLowerCase();
  document.querySelectorAll('.sidebar-content .tree-item,.sidebar-content .assembly-item,.sidebar-content .resource-item').forEach(function(el){
    var n=el.dataset.name||'';el.style.display=n.includes(q)?'':'none';
    if(q&&n.includes(q)){var p=el.parentElement;while(p&&p.classList.contains('tree-children')){p.classList.add('open');p=p.parentElement?p.parentElement.parentElement:null}}
  });
}

function showAssembly(id){
  document.querySelectorAll('.assembly-item').forEach(function(e){e.classList.remove('active')});
  document.querySelectorAll('.assembly-item').forEach(function(e){if(e.dataset.id===id)e.classList.add('active')});
  var asm=D.assemblies.find(function(a){return a.id===id});
  if(!asm)return;
  var parts=D.assemblyToParts[id]||[];
  var partNames=parts.map(function(pid){return D.partIdToName[pid]||pid}).filter(function(n){return n});
  var displayName=moduleName(asm.identity.name);

  var html='<div class="breadcrumb"><a onclick="switchTab(\\'overview\\')">Overview</a> <span>/</span> <span>'+escHtml(displayName)+'</span></div>';
  html+='<div class="file-header"><div><h2>'+escHtml(displayName)+'</h2><div class="file-path">'+escHtml(moduleName(asm.identity.qualified_name))+'</div></div><span class="kind-badge">'+escHtml(asm.kind)+'</span>';
  if(asm.boundary&&asm.boundary.architecture_layer)html+='<span class="layer-badge layer-'+escClassToken(asm.boundary.architecture_layer)+'">'+escHtml(asm.boundary.architecture_layer)+'</span>';
  html+='</div>';

  if(asm.cognitive&&asm.cognitive.intent)html+='<div class="card"><h3>Intent</h3><p class="intent-text">'+escHtml(asm.cognitive.intent)+'</p></div>';
  if(asm.cognitive&&asm.cognitive.behavior)html+='<div class="card"><h3 class="collapsible-header" onclick="toggleColl(this)">Behavior</h3><div class="collapsible-body"><p class="behavior-text">'+escHtml(asm.cognitive.behavior)+'</p></div></div>';
  if(asm.cognitive&&asm.cognitive.impact&&asm.cognitive.impact.details)html+='<div class="card"><h3 class="collapsible-header" onclick="toggleColl(this)">Impact Analysis</h3><div class="collapsible-body"><p class="impact-text">'+escHtml(asm.cognitive.impact.details)+'</p></div></div>';

  html+='<div class="card"><h3>Components ('+partNames.length+')</h3><div>';
  partNames.forEach(function(n){var mp=D.metaPartsByName[n];var pp=mp&&mp.identity?mp.identity.file_path||'':'';var bn=pp?pp.split('/').pop():(n+D.fileExtension);html+='<span class="dep-chip" onclick="showFile(\\''+sq(bn)+'\\',\\''+sq(pp)+'\\')">'+escHtml(n)+'</span>'});
  html+='</div></div>';

  var asmIssues=[];
  partNames.forEach(function(n){var mp=D.metaPartsByName[n];var pp=mp&&mp.identity?mp.identity.file_path||'':'';if(pp){(D.issuesByFile[pp]||[]).forEach(function(i){asmIssues.push(i)})}});
  html+='<div class="card"><h3>Issues ('+asmIssues.length+')</h3>';
  if(asmIssues.length){
    html+='<div class="table-wrap"><table><thead><tr><th>File</th><th>Type</th><th>Category</th><th>Description</th><th>Conf.</th></tr></thead><tbody>';
    asmIssues.forEach(function(i){
      html+='<tr><td><a onclick="showFile(\\''+sq(i.filename)+'\\',\\''+sq(i.path)+'\\')">'+escHtml(i.filename)+'</a></td><td><span class="tag '+tc(i.type)+'">'+ft(i.type)+'</span></td><td>'+escHtml(i.category)+'</td><td>'+escHtml(i.description)+'</td><td>'+(i.confidence*100).toFixed(0)+'%</td></tr>';
    });
    html+='</tbody></table></div>';
  }
  html+='</div>';
  switchTab('assemblies');
  document.getElementById('assemblyDetail').innerHTML=html;
}

function showFile(filename,fullPath){
  document.querySelectorAll('.tree-label').forEach(function(l){l.classList.remove('active')});
  var item=null;
  document.querySelectorAll('.tree-item[data-path]').forEach(function(el){if(el.dataset.path===fullPath&&!item)item=el.querySelector('.tree-label')});
  if(item)item.classList.add('active');

  var fm=D.fileMetrics[fullPath];
  var issues=D.issuesByFile[fullPath]||[];
  var suggestions=D.suggestionsByFile[fullPath]||[];
  var detailed=D.detailedByFile[fullPath];
  var mp=D.metaPartsByPath[fullPath]||D.metaPartsByName[filename.replace(D.fileExtension,'')]||{};
  var asmNames=(D.partToAssemblies[mp.id]||[]).map(function(aid){var a=D.assemblies.find(function(x){return x.id===aid});return a?a.identity.name:aid}).filter(Boolean);

  var html='<div class="breadcrumb"><a onclick="switchTab(\\'overview\\')">Overview</a> <span>/</span> <span>'+escHtml(filename)+'</span></div>';
  html+='<div class="file-header"><div><h2>'+escHtml(filename)+'</h2><div class="file-path">'+escHtml(fullPath)+'</div></div>';
  if(fm)html+='<span class="risk-badge" style="background:'+rb(fm.risk_category)+';color:'+rc(fm.risk_category)+'" onclick="filterByRisk(\\''+sq(fm.risk_category)+'\\')">'+escHtml(fm.risk_category)+' Risk</span>';
  if(mp.boundary&&mp.boundary.security_zone)html+='<span class="zone-badge zone-'+escClassToken(mp.boundary.security_zone)+'" onclick="filterByZone(\\''+sq(mp.boundary.security_zone)+'\\')">'+escHtml(mp.boundary.security_zone)+'</span>';
  if(mp.boundary&&mp.boundary.architecture_layer)html+='<span class="layer-badge layer-'+escClassToken(mp.boundary.architecture_layer)+'" onclick="filterByLayer(\\''+sq(mp.boundary.architecture_layer)+'\\')">'+escHtml(mp.boundary.architecture_layer)+'</span>';
  if(mp.kind)html+='<span class="kind-badge">'+escHtml(mp.kind)+'</span>';
  html+='</div>';

  if(asmNames.length){html+='<div class="card" style="padding:12px"><span style="font-size:12px;color:var(--text2)">Modules: </span>';asmNames.forEach(function(n){html+='<span class="dep-chip" onclick="showAssembly(\\''+sq((D.assemblies.find(function(a){return a.identity.name===n})||{}).id)+'\\')">'+escHtml(moduleName(n))+'</span>'});html+='</div>'}

  if(mp.cognitive&&mp.cognitive.intent)html+='<div class="card"><h3>Intent</h3><p class="intent-text">'+escHtml(mp.cognitive.intent)+'</p></div>';
  if(mp.cognitive&&mp.cognitive.behavior)html+='<div class="card"><h3 class="collapsible-header" onclick="toggleColl(this)">Behavior</h3><div class="collapsible-body"><p class="behavior-text">'+escHtml(mp.cognitive.behavior)+'</p></div></div>';
  if(mp.cognitive&&mp.cognitive.impact&&mp.cognitive.impact.details)html+='<div class="card"><h3 class="collapsible-header" onclick="toggleColl(this)">Change Impact Analysis</h3><div class="collapsible-body"><p class="impact-text">'+escHtml(mp.cognitive.impact.details)+'</p></div></div>';

  if(fm){
    var hrs=(fm.tech_debt_time/60).toFixed(1);
    html+='<div class="card-grid">';
    html+='<div class="stat-card" onclick="filterIssuesByFile(\\''+fullPath+'\\')"><div class="stat-value stat-orange">'+fm.bugs+'</div><div class="stat-label">Bugs</div></div>';
    html+='<div class="stat-card" onclick="filterIssuesByFile(\\''+fullPath+'\\')"><div class="stat-value stat-yellow">'+fm.code_smells+'</div><div class="stat-label">Code Smells</div></div>';
    html+='<div class="stat-card"><div class="stat-value stat-purple">'+fm.cognitive_complexity+'</div><div class="stat-label">Cognitive Complexity</div></div>';
    html+='<div class="stat-card"><div class="stat-value stat-blue">'+fm.lines+'</div><div class="stat-label">Lines</div></div>';
    html+='<div class="stat-card"><div class="stat-value stat-orange">'+hrs+'h</div><div class="stat-label">Tech Debt</div></div>';

    html+='</div>';

    html+='<div class="card" style="margin-top:14px"><h3>Non-Functional Requirements</h3><div class="nfr-grid">';
    [
      {label:'Security',key:'nfr_security_rating',value:fm.nfr_security_rating},
      {label:'Maintainability',key:'nfr_maintainability_rating',value:fm.nfr_maintainability_rating},
      {label:'Reliability',key:'nfr_reliability_rating',value:fm.nfr_reliability_rating},
      {label:'Testability',key:'nfr_testability_rating',value:fm.nfr_testability_rating},
      {label:'Extensibility',key:'nfr_extensibility_rating',value:fm.nfr_extensibility_rating},
      {label:'Reusability',key:'nfr_reusability_rating',value:fm.nfr_reusability_rating},
      {label:'Scalability',key:'nfr_scalability_rating',value:fm.nfr_scalability_rating},
      {label:'Cloud Compatibility',key:'cloud_compatibiliy_rating',value:fm.cloud_compatibiliy_rating}
    ].forEach(function(metric){
      var color=metricColor(metric.key,metric.value);
      html+='<div class="nfr-item"><div class="nfr-label">'+metric.label+'</div><div class="nfr-bar"><div class="nfr-fill" style="width:'+metricFillWidth(metric.key,metric.value)+'%;background:'+color+'"></div></div><div class="nfr-val" style="color:'+color+'">'+metricDisplayValue(metric.key,metric.value)+'</div><div class="nfr-scale">'+metricScaleText(metric.key)+'</div></div>';
    });
    html+='</div></div>';
  }

  html+='<div class="card" style="margin-top:14px"><h3>Issues ('+issues.length+')</h3>';
  if(issues.length){
    html+='<div class="table-wrap"><table><thead><tr><th>Type</th><th>Category</th><th>Description</th><th>Location</th><th>Conf.</th></tr></thead><tbody>';
    issues.forEach(function(i){
      html+='<tr><td><span class="tag '+tc(i.type)+'">'+ft(i.type)+'</span></td><td>'+escHtml(i.category)+'</td><td>'+escHtml(i.description)+'</td><td style="font-family:monospace;font-size:11px;color:var(--text2)">'+escHtml(i.issue_location||'N/A')+'</td><td>'+(i.confidence*100).toFixed(0)+'% '+cb(i.confidence)+'</td></tr>';
    });
    html+='</tbody></table></div>';
  }else html+='<p style="color:var(--text2)">No issues</p>';
  html+='</div>';

  var allSugs=[].concat(suggestions).concat(detailed&&detailed.suggestions?detailed.suggestions:[]);
  html+='<div class="card"><h3>Suggestions ('+allSugs.length+')</h3>';
  if(allSugs.length){
    html+='<div class="table-wrap"><table><thead><tr><th>#</th><th>Suggestion</th></tr></thead><tbody>';
    allSugs.forEach(function(s,i){html+='<tr><td style="color:var(--text2)">'+(i+1)+'</td><td>'+escHtml(s.suggestion||s.code_suggestion||'')+'</td></tr>'});
    html+='</tbody></table></div>';
  }else html+='<p style="color:var(--text2)">No suggestions</p>';
  html+='</div>';

  switchTab('files');
  document.getElementById('fileDetail').innerHTML=html;
  document.querySelectorAll('#fileDetail .collapsible-header').forEach(function(h){h.classList.add('open');h.nextElementSibling.classList.add('open')});
}

function toggleColl(el){el.classList.toggle('open');el.nextElementSibling.classList.toggle('open')}

function filterByZone(z){applyIssueFilter(function(p){var mp=D.metaPartsByPath[p];return mp&&mp.boundary&&mp.boundary.security_zone===z})}
function filterByLayer(l){applyIssueFilter(function(p){var mp=D.metaPartsByPath[p];return mp&&mp.boundary&&mp.boundary.architecture_layer===l})}
function filterByDomain(dm){applyIssueFilter(function(p){var mp=D.metaPartsByPath[p];return mp&&mp.boundary&&mp.boundary.domain===dm})}
function filterByRisk(r){applyIssueFilter(function(p){var fm=D.fileMetrics[p];return fm&&fm.risk_category===r})}
function filterIssuesByFile(p){currentIssueScope='all';currentIssueFile=p;currentIssueType='all';renderIssues();switchTab('issues')}

function applyIssueFilter(matchFn){
  currentIssueScope='all';currentIssueFile='all';currentIssueType='all';renderIssues();
  document.querySelectorAll('#issuesTable tbody tr').forEach(function(tr){var p=tr.dataset.path||'';tr.style.display=matchFn(p)?'':'none'});
  switchTab('issues');
}

function renderOverview(){
  var s1=D.sheet1.data[0],s7=D.sheet7.summary,s9=D.sheet9.summary;
  document.getElementById('execSummary').innerHTML=
    summaryCard('<div class="stat-value stat-red">'+s9.total_issues+'</div>','Total Issues','All detected findings across bugs, code smells, and cognitive complexity observations.','currentIssueScope=\\'all\\';switchTab(\\'issues\\')')+
    summaryCard('<div class="stat-value stat-orange">'+s9.total_suggestions+'</div>','Suggestions','Recommended follow-up actions generated from the assessment.','switchTab(\\'suggestions\\')')+
    summaryCard('<div class="stat-value stat-yellow">'+s1.technical_health_score+'</div>','Health Score','Composite score for overall maintainability, quality, and technical condition.')+
    summaryCard('<div class="stat-value stat-green">'+s1.modernization_readiness_score+'</div>','Modernization Readiness','Readiness for modernization work such as upgrades, refactoring, migration, and architecture change.')+
    summaryCard('<div class="stat-value stat-red">'+s7.high_risk_files+'</div>','High Risk Files','Files classified as high risk based on issue severity, security, and maintainability signals.','filterByRisk(\\'High\\')')+
    summaryCard('<div class="stat-value stat-orange">'+s7.medium_risk_files+'</div>','Medium Risk','Files classified as medium risk and likely to need targeted cleanup.','filterByRisk(\\'Medium\\')')+
    summaryCard('<div class="stat-value stat-purple">'+D.totalLoc+'</div>','Lines of Code','Total analyzed source lines across the scanned application.')+
    summaryCard('<div class="stat-value" style="color:'+rc(s1.risk_level)+'">'+escHtml(s1.risk_level)+'</div>','Risk Level','Overall application risk classification from the assessment.','filterByRisk(\\''+sq(s1.risk_level)+'\\')')+
    summaryCard('<div class="stat-value stat-blue">'+escHtml(s1.recommended_action)+'</div>','Action','Recommended next step based on the overall assessment outcome.');
}

function renderCharts(){
  var s9=D.sheet9.summary,s7d=D.sheet7.data;
  Object.values(charts).forEach(function(c){if(c&&c.destroy)c.destroy()});charts={};
  charts.issueType=new Chart(document.getElementById('chartIssueType'),{type:'doughnut',data:{labels:Object.keys(s9.issues_by_type),datasets:[{data:Object.values(s9.issues_by_type),backgroundColor:['#ef4444','#eab308','#f97316'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#94a3b8'}}}}});
  var cats=Object.entries(s9.issues_by_category).sort(function(a,b){return b[1]-a[1]}).slice(0,12);
  charts.issueCat=new Chart(document.getElementById('chartIssueCat'),{type:'bar',data:{labels:cats.map(function(c){return c[0].length>28?c[0].slice(0,25)+'...':c[0]}),datasets:[{data:cats.map(function(c){return c[1]}),backgroundColor:'#3b82f6',borderRadius:4}]},options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#94a3b8'}},y:{ticks:{color:'#94a3b8',font:{size:9}}}}}});
  var hi=s7d.filter(function(d){return d.risk_category==='High'}).length,me=s7d.filter(function(d){return d.risk_category==='Medium'}).length,lo=s7d.filter(function(d){return d.risk_category==='Low'}).length;
  charts.risk=new Chart(document.getElementById('chartRisk'),{type:'doughnut',data:{labels:['High','Medium','Low'],datasets:[{data:[hi,me,lo],backgroundColor:['#ef4444','#f97316','#22c55e'],borderWidth:0}]},options:{responsive:true,plugins:{legend:{position:'bottom',labels:{color:'#94a3b8'}}}}});
  var cogS=s7d.slice().sort(function(a,b){return b.cognitive_complexity-a.cognitive_complexity});
  charts.cog=new Chart(document.getElementById('chartCognitive'),{type:'bar',data:{labels:cogS.map(function(d){return d.filename}),datasets:[{data:cogS.map(function(d){return d.cognitive_complexity}),backgroundColor:cogS.map(function(d){return d.cognitive_complexity>30?'#ef4444':d.cognitive_complexity>15?'#f97316':'#22c55e'}),borderRadius:4}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{x:{ticks:{color:'#94a3b8',font:{size:9}}},y:{ticks:{color:'#94a3b8'}}}}});
  var secS=s7d.slice().sort(function(a,b){return b.security_risk_rating-a.security_risk_rating});
  charts.sec=new Chart(document.getElementById('chartSecurity'),{type:'bar',data:{labels:secS.map(function(d){return d.filename}),datasets:[{data:secS.map(function(d){return d.security_risk_rating}),backgroundColor:secS.map(function(d){return d.security_risk_rating>=5?'#ef4444':d.security_risk_rating>=4?'#f97316':'#eab308'}),borderRadius:4}]},options:{responsive:true,indexAxis:'y',plugins:{legend:{display:false}},scales:{x:{max:5,ticks:{color:'#94a3b8'}},y:{ticks:{color:'#94a3b8',font:{size:9}}}}}});
}

function renderIssues(){
  var base=Object.values(D.issuesByFile).flat();
  if(currentIssueScope==='security')base=base.filter(isSecurityIssue);
  var types={},files={};
  base.forEach(function(i){types[i.type]=1;var k=i.path||i.filename;files[k]=i.filename||k});
  var fh='<button class="filter-btn '+(currentIssueScope==='all'&&currentIssueType==='all'?'active':'')+'" onclick="currentIssueScope=\\'all\\';currentIssueType=\\'all\\';renderIssues()">All</button>';
  fh+='<button class="filter-btn '+(currentIssueScope==='security'?'active':'')+'" onclick="currentIssueScope=\\'security\\';currentIssueType=\\'all\\';renderIssues()">Security Only</button>';
  Object.keys(types).forEach(function(t){fh+='<button class="filter-btn '+(currentIssueType===t?'active':'')+'" onclick="currentIssueType=\\''+sq(t)+'\\';renderIssues()">'+escHtml(ft(t))+'</button>'});
  document.getElementById('issueTypeFilters').innerHTML=fh;
  var ff='<button class="filter-btn '+(currentIssueFile==='all'?'active':'')+'" onclick="currentIssueFile=\\'all\\';renderIssues()">All Files</button>';
  Object.keys(files).forEach(function(p){ff+='<button class="filter-btn '+(currentIssueFile===p?'active':'')+'" onclick="currentIssueFile=\\''+sq(p)+'\\';renderIssues()" title="'+escAttr(p)+'">'+escHtml(files[p])+'</button>'});
  document.getElementById('issueFileFilters').innerHTML=ff;
  var q=(document.getElementById('issueSearch')?document.getElementById('issueSearch').value:'').toLowerCase();
  var all=base.slice();
  if(currentIssueType!=='all')all=all.filter(function(i){return i.type===currentIssueType});
  if(currentIssueFile!=='all')all=all.filter(function(i){return (i.path||i.filename)===currentIssueFile});
  if(q)all=all.filter(function(i){return issueSearchText(i).includes(q)});
  document.getElementById('issueCount').textContent='('+all.length+')';
  var h='<thead><tr><th>File</th><th>Type</th><th>Category</th><th>Description</th><th>Location</th><th>Conf.</th></tr></thead><tbody>';
  all.forEach(function(i){
    var pk=i.path||i.filename||'';
    h+='<tr data-path="'+escAttr(pk)+'"><td style="font-size:11px" title="'+escAttr(pk)+'"><a onclick="showFile(\\''+sq(i.filename)+'\\',\\''+sq(i.path)+'\\')">'+escHtml(i.filename)+'</a></td><td><span class="tag '+tc(i.type)+'">'+escHtml(ft(i.type))+'</span></td><td><a onclick="filterIssueCategory(\\''+sq(i.category)+'\\')">'+escHtml(i.category)+'</a></td><td>'+escHtml(i.description)+'</td><td style="font-family:monospace;font-size:10px;color:var(--text2)">'+escHtml(i.issue_location||'N/A')+'</td><td>'+(i.confidence*100).toFixed(0)+'% '+cb(i.confidence)+'</td></tr>';
  });
  document.getElementById('issuesTable').innerHTML=h+'</tbody>';
}

function renderSuggestions(){
  var files={};Object.values(D.suggestionsByFile).flat().forEach(function(s){var k=s.path||s.filename;files[k]=s.filename||k});
  var ff='<button class="filter-btn '+(currentSugFile==='all'?'active':'')+'" onclick="currentSugFile=\\'all\\';renderSuggestions()">All</button>';
  Object.keys(files).forEach(function(p){ff+='<button class="filter-btn '+(currentSugFile===p?'active':'')+'" onclick="currentSugFile=\\''+sq(p)+'\\';renderSuggestions()" title="'+escAttr(p)+'">'+escHtml(files[p])+'</button>'});
  document.getElementById('sugFileFilters').innerHTML=ff;
  var q=(document.getElementById('sugSearch')?document.getElementById('sugSearch').value:'').toLowerCase();
  var all=Object.values(D.suggestionsByFile).flat();
  if(currentSugFile!=='all')all=all.filter(function(s){return (s.path||s.filename)===currentSugFile});
  if(q)all=all.filter(function(s){return suggestionSearchText(s).includes(q)});
  document.getElementById('sugCount').textContent='('+all.length+')';
  var h='<thead><tr><th>File</th><th>Suggestion</th></tr></thead><tbody>';
  all.forEach(function(s){var pk=s.path||s.filename||'';h+='<tr><td style="font-size:11px" title="'+escAttr(pk)+'"><a onclick="showFile(\\''+sq(s.filename)+'\\',\\''+sq(s.path)+'\\')">'+escHtml(s.filename)+'</a></td><td>'+escHtml(s.suggestion||s.code_suggestion||'')+'</td></tr>'});
  document.getElementById('suggestionsTable').innerHTML=h+'</tbody>';
}

function renderAssembliesTab(){
  var html='<div class="card-grid">';
  D.assemblies.forEach(function(a){
    var parts=D.assemblyToParts[a.id]||[];
    if(!parts.length)return;
    var partNames=parts.map(function(pid){return D.partIdToName[pid]||pid}).filter(Boolean);
    var issueCount=0;partNames.forEach(function(n){var mp=D.metaPartsByName[n];var pp=mp&&mp.identity?mp.identity.file_path||'':'';if(pp)issueCount+=(D.issuesByFile[pp]||[]).length});
    html+='<div class="stat-card" onclick="showAssembly(\\''+sq(a.id)+'\\')"><div style="font-size:14px;font-weight:700;color:var(--text)">'+escHtml(moduleName(a.identity.name))+'</div><div style="font-size:11px;color:var(--text2);margin-top:4px">'+partNames.length+' parts | '+issueCount+' issues</div></div>';
  });
  html+='</div>';
  document.getElementById('assemblyDetail').innerHTML=html;
}

renderSidebar();
renderOverview();
renderCharts();
var ff=D.sheet7.data[0];if(ff)showFile(ff.filename,ff.path);
"""

    # Embed the structured payload as base64 so literal HTML sequences like
    # `</script>` inside findings/suggestions cannot terminate the inline
    # script block during HTML parsing.
    JS = JS.replace('DATA_PLACEHOLDER', json.dumps(data_b64))
    JS = JS.replace('MCM_VIS_PLACEHOLDER', json.dumps(mcm_visualization_b64))
    JS = JS.replace('DOC_APPLICATION_OVERVIEW_PLACEHOLDER', json.dumps(application_overview_b64))
    JS = JS.replace('DOC_FSD_PLACEHOLDER', json.dumps(fsd_document_b64))
    JS = JS.replace('DOC_TSD_PLACEHOLDER', json.dumps(tsd_document_b64))
    JS = JS.replace('DOC_DEPENDENCY_PLACEHOLDER', json.dumps(dependency_report_b64))
    JS = JS.replace('DOC_RECOMMENDATIONS_PLACEHOLDER', json.dumps(recommendations_b64))
    JS = JS.replace('DOC_POST_MODERNIZATION_PLACEHOLDER', json.dumps(post_modernization_b64))

    html = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>' + app_tab_title_html + '</title>\n<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>\n<style>' + CSS + '</style>\n</head>\n<body>\n<div class="page-shell">\n  <header class="page-header">\n    <div class="brand-lockup">\n      <img src="__LOGO_DATA_URI__" alt="LL logo" class="brand-logo">\n      <div>\n        <div class="brand-eyebrow"></div>\n        <div class="brand-title">' + app_name_html + ' Dashboard</div>\n      </div>\n    </div>\n    <div class="page-header-meta">' + tech_label_html + ' | ' + str(FILE_COUNT) + ' files</div>\n  </header>\n<div class="app">\n  <div class="sidebar">\n    <div class="sidebar-header">\n      <h2>Tech Debt Assessment</h2>\n      <div class="app-name">' + app_name_html + '</div>\n      <div class="app-meta">' + tech_label_html + ' | ' + str(FILE_COUNT) + ' files</div>\n    </div>\n    <div class="sidebar-nav">\n      <div class="sidebar-nav-btn active" onclick="switchSidebar(\'files\')">Files</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'assemblies\')">Assemblies</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'zones\')">Zones</div>\n    </div>\n    <div class="sidebar-search"><input type="text" id="sidebarSearch" placeholder="Search..." oninput="filterSidebar(this.value)"></div>\n    <div class="sidebar-content" id="sidebarContent"></div>\n  </div>\n  <div class="main">\n    <div class="tabs">\n      <div class="tab active" data-tab="overview" onclick="switchTab(\'overview\',this)">Overview</div>\n      <div class="tab" data-tab="files" onclick="switchTab(\'files\',this)">File Detail</div>\n      <div class="tab" data-tab="issues" onclick="switchTab(\'issues\',this)">Issues</div>\n      <div class="tab" data-tab="suggestions" onclick="switchTab(\'suggestions\',this)">Suggestions</div>\n      <div class="tab" data-tab="assemblies" onclick="switchTab(\'assemblies\',this)">Assemblies</div>\n    </div>\n    <div class="panel active" id="panel-overview">\n      <div class="card-grid" id="execSummary"></div>\n      <div class="chart-row" style="margin-top:14px"><div class="chart-box"><h4>Issues by Type</h4><canvas id="chartIssueType"></canvas></div><div class="chart-box"><h4>Top Issue Categories</h4><canvas id="chartIssueCat"></canvas></div></div>\n      <div class="chart-row"><div class="chart-box"><h4>Files by Risk</h4><canvas id="chartRisk"></canvas></div><div class="chart-box"><h4>Tech Debt by File</h4><canvas id="chartTechDebt"></canvas></div></div>\n      <div class="chart-row"><div class="chart-box"><h4>Cognitive Complexity</h4><canvas id="chartCognitive"></canvas></div><div class="chart-box"><h4>Security Rating</h4><canvas id="chartSecurity"></canvas></div></div>\n      <div class="card"><h3>Architecture Modules</h3><div class="table-wrap"><table id="archTable"></table></div></div>\n    </div>\n    <div class="panel" id="panel-files"><div id="fileDetail"><p style="color:var(--text2);text-align:center;padding:40px">Select a file from the sidebar</p></div></div>\n    <div class="panel" id="panel-issues"><div class="filters" id="issueTypeFilters"></div><div class="filters" id="issueFileFilters"></div><div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><h3 style="margin:0">All Issues <span id="issueCount" style="color:var(--text2);font-weight:400;font-size:13px"></span></h3><input type="text" id="issueSearch" placeholder="Search..." oninput="filterIssues()" style="padding:5px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:12px;width:220px;outline:none"></div><div class="table-wrap"><table id="issuesTable"></table></div></div></div>\n    <div class="panel" id="panel-suggestions"><div class="filters" id="sugFileFilters"></div><div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><h3 style="margin:0">Suggestions <span id="sugCount" style="color:var(--text2);font-weight:400;font-size:13px"></span></h3><input type="text" id="sugSearch" placeholder="Search..." oninput="filterSuggestions()" style="padding:5px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:12px;width:220px;outline:none"></div><div class="table-wrap"><table id="suggestionsTable"></table></div></div></div>\n    <div class="panel" id="panel-assemblies"><div id="assemblyDetail"><p style="color:var(--text2);text-align:center;padding:40px">Select an assembly from the sidebar</p></div></div>\n  </div>\n</div>\n</div>\n<script>' + JS + '</script>\n</body>\n</html>'
    html = html.replace("__LOGO_DATA_URI__", logo_data_uri)
    html = html.replace(
        '<title>' + app_tab_title_html + '</title>',
        f'<title>{app_tab_title_html}</title>\n<link rel="icon" type="image/svg+xml" href="__FAVICON_DATA_URI__">'
    )
    html = html.replace('<div class="sidebar">', '<div class="sidebar" id="sidebar">')
    html = html.replace(
        '<div class="sidebar-header">\n      <h2>Tech Debt Assessment</h2>\n      <div class="app-name">' + app_name_html + '</div>\n      <div class="app-meta">' + tech_label_html + ' | ' + str(FILE_COUNT) + ' files</div>\n    </div>',
        '<div class="sidebar-header">\n      <div class="sidebar-header-copy">\n        <h2>Tech Debt Assessment</h2>\n        <div class="app-name">' + app_name_html + '</div>\n        <div class="app-meta">' + tech_label_html + ' | ' + str(FILE_COUNT) + ' files</div>\n      </div>\n      <button type="button" class="sidebar-toggle" id="sidebarToggle" onclick="toggleSidebar()" aria-label="Collapse sidebar" title="Collapse sidebar"><img src="__FAVICON_DATA_URI__" alt="" class="sidebar-toggle-logo"></button>\n    </div>'
    )
    html = html.replace(
        '<div class="sidebar-nav">\n      <div class="sidebar-nav-btn active" onclick="switchSidebar(\'files\')">Files</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'assemblies\')">Assemblies</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'zones\')">Zones</div>\n    </div>',
        '<div class="sidebar-nav">\n      <div class="sidebar-nav-btn active" onclick="switchSidebar(\'files\',this)">Files</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'assemblies\',this)">Modules</div>\n      <div class="sidebar-nav-btn" onclick="switchSidebar(\'resources\',this)">Resources</div>\n    </div>'
    )
    html = html.replace(
        '<div class="chart-row"><div class="chart-box"><h4>Files by Risk</h4><canvas id="chartRisk"></canvas></div><div class="chart-box"><h4>Tech Debt by File</h4><canvas id="chartTechDebt"></canvas></div></div>',
        '<div class="chart-row"><div class="chart-box full-width"><h4>Files by Risk</h4><canvas id="chartRisk"></canvas></div></div>'
    )
    html = html.replace(
        '<div class="card"><h3>Architecture Modules</h3><div class="table-wrap"><table id="archTable"></table></div></div>',
        ''
    )
    html = html.replace(
        '<div class="sidebar-nav-btn" onclick="switchSidebar(\'assemblies\')">Assemblies</div>',
        '<div class="sidebar-nav-btn" onclick="switchSidebar(\'assemblies\')">Modules</div>'
    )
    html = html.replace(
        '<div class="tab" data-tab="assemblies" onclick="switchTab(\'assemblies\',this)">Assemblies</div>',
        '<div class="tab" data-tab="assemblies" onclick="switchTab(\'assemblies\',this)">Modules</div><div class="tab" data-tab="mcm" onclick="switchTab(\'mcm\',this)">Visualization</div><div class="tab" data-tab="documents" onclick="switchTab(\'documents\',this)">Comprehension</div>'
    )
    html = html.replace('Select an assembly from the sidebar', 'Select a module from the sidebar')
    html = html.replace(
        '<div class="panel" id="panel-assemblies"><div id="assemblyDetail"><p style="color:var(--text2);text-align:center;padding:40px">Select a module from the sidebar</p></div></div>',
        '<div class="panel" id="panel-assemblies"><div id="assemblyDetail"><p style="color:var(--text2);text-align:center;padding:40px">Select a module from the sidebar</p></div></div><div class="panel" id="panel-mcm"><div class="card viz-card"><iframe id="mcmFrame" class="viz-frame" title="Meta Cognitive BOM Visualization" loading="lazy"></iframe></div></div><div class="panel" id="panel-documents"><div class="card viz-card"><div class="doc-toolbar"><button class="doc-btn active" data-doc="application_overview" onclick="loadDocument(\'application_overview\')">Application Overview</button><button class="doc-btn" data-doc="fsd" onclick="loadDocument(\'fsd\')">Functional Spec</button><button class="doc-btn" data-doc="tsd" onclick="loadDocument(\'tsd\')">Technical Spec</button><button class="doc-btn" data-doc="dependency" onclick="loadDocument(\'dependency\')">Dependency Report</button><button class="doc-btn" data-doc="recommendations" onclick="loadDocument(\'recommendations\')">Recommendations</button><button class="doc-btn" data-doc="post_modernization" onclick="loadDocument(\'post_modernization\')">Post Modernization</button></div><iframe id="docFrame" class="viz-frame" title="Rendered comprehension document" loading="lazy"></iframe></div></div>'
    )
    html = html.replace("__LOGO_DATA_URI__", logo_data_uri)
    html = html.replace("__FAVICON_DATA_URI__", favicon_data_uri)

    output_path = TECH_DIR / "technical_assessment_dashboard.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(html + '\n')
    print(f"Dashboard generated: {output_path}")
    print(f"File size: {output_path.stat().st_size / 1024:.0f} KB")

if __name__ == '__main__':
    generate_dashboard()
