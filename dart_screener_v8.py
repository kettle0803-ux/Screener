"""
dart_screener_v8.py - DART screener (ASCII-safe)
================================================
v8 adds ASSET-VALUE screening on top of v7:
  - PBR (marcap / equity), net cash (cash+deposits - debt)
  - hard assets (PPE + investment real estate) / marcap
  - treasury shares / equity
  - relative valuation: PBR & PER vs universe median
Score (100) = momentum 30 + earnings-quality 10 + qtr-direction 10
            + drawdown 15 + not-yet-run 5 + ASSET 20 + RELATIVE 10

Modes:
  python dart_screener_v8.py              -> run + open browser
  HEADLESS=1 python dart_screener_v8.py   -> no browser (for automation)
  OUTPUT_DIR=docs python dart_screener_v8.py  -> write index.html into docs/

Setup (once): pip install requests pandas finance-datareader
Free DART API key: https://opendart.fss.or.kr
Set API_KEY below (or env var DART_API_KEY).
Pure ASCII - editors cannot corrupt it.
"""

import io
import json
import os
import time
import sys
import webbrowser
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests

try:
    import FinanceDataReader as fdr
    HAS_FDR = True
except ImportError:
    HAS_FDR = False
    print("[warn] FinanceDataReader not installed -> price scores skipped")


API_KEY = os.environ.get("DART_API_KEY", "PUT_YOUR_KEY_HERE")




AUTO_MODE = True
AUTO_COUNT = 80
AUTO_MARCAP_MIN = 3e11
AUTO_MARCAP_MAX = 2e13
AUTO_MARKETS = ("KOSPI", "KOSDAQ")

UNIVERSE = {
    "119850": "\uc9c0\uc5d4\uc528\uc5d0\ub108\uc9c0",
    "033100": "\uc81c\ub8e1\uc804\uae30",
    "017040": "\uad11\uba85\uc804\uae30",
    "189860": "\uc11c\uc804\uae30\uc804",
    "108380": "\ub300\uc591\uc804\uae30\uacf5\uc5c5",
    "011930": "\uc2e0\uc131\uc774\uc5d4\uc9c0",
    "053080": "\ucf00\uc774\uc5d4\uc194",
    "139130": "iM\uae08\uc735\uc9c0\uc8fc",
    "004020": "\ud604\ub300\uc81c\ucca0",
    "011200": "HMM",
    "010130": "\uace0\ub824\uc544\uc5f0",
    "017960": "\ud55c\uad6d\uce74\ubcf8",
    "033500": "\ub3d9\uc131\ud654\uc778\ud14d",
}

FY_CUR, FY_PRV, Q_YEAR = "2025", "2024", "2026"
REPRT_ANNUAL, REPRT_Q1 = "11011", "11013"
BASE = "https://opendart.fss.or.kr/api"

BS_ACCOUNTS = {
    "\ud604\uae08\ubc0f\ud604\uae08\uc131\uc790\uc0b0": "cash", "\ub2e8\uae30\uae08\uc735\uc0c1\ud488": "st_fin", "\uae30\ud0c0\uc720\ub3d9\uae08\uc735\uc790\uc0b0": "st_fin2",
    "\ub2e8\uae30\ucc28\uc785\uae08": "st_debt", "\uc7a5\uae30\ucc28\uc785\uae08": "lt_debt", "\uc0ac\ucc44": "bond",
    "\uc720\ub3d9\uc131\uc7a5\uae30\ubd80\ucc44": "cur_lt_debt", "\uc790\ubcf8\ucd1d\uacc4": "equity", "\uc790\uae30\uc8fc\uc2dd": "treasury",
    "\uc720\ud615\uc790\uc0b0": "ppe", "\ud22c\uc790\ubd80\ub3d9\uc0b0": "invest_re",
}

ACCOUNTS = {"\ub9e4\ucd9c\uc561": "revenue", "\uc218\uc775(\ub9e4\ucd9c\uc561)": "revenue", "\uc601\uc5c5\uc218\uc775": "revenue",
            "\uc601\uc5c5\uc774\uc775": "op", "\uc601\uc5c5\uc774\uc775(\uc190\uc2e4)": "op",
            "\ub2f9\uae30\uc21c\uc774\uc775": "ni", "\ub2f9\uae30\uc21c\uc774\uc775(\uc190\uc2e4)": "ni",
            "\ubd84\uae30\uc21c\uc774\uc775": "ni", "\ubc18\uae30\uc21c\uc774\uc775": "ni"}


def load_corp_codes(api_key):
    r = requests.get(f"{BASE}/corpCode.xml", params={"crtfc_key": api_key}, timeout=30)
    r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    root = ET.fromstring(zf.read(zf.namelist()[0]))
    return {(c.findtext("stock_code") or "").strip(): c.findtext("corp_code").strip()
            for c in root.iter("list") if (c.findtext("stock_code") or "").strip()}


def fetch_fs(api_key, corp_code, year, reprt_code):
    for fs_div in ("CFS", "OFS"):
        try:
            js = requests.get(f"{BASE}/fnlttSinglAcntAll.json", params={
                "crtfc_key": api_key, "corp_code": corp_code,
                "bsns_year": year, "reprt_code": reprt_code, "fs_div": fs_div,
            }, timeout=30).json()
        except Exception:
            continue
        if js.get("status") != "000":
            continue
        out = {}
        for row in js.get("list", []):
            nm = row.get("account_nm", "").strip()
            key = ACCOUNTS.get(nm) or BS_ACCOUNTS.get(nm)
            if key and key not in out:
                try:
                    out[key] = int(row.get("thstrm_amount", "").replace(",", ""))
                except ValueError:
                    pass
        if out.get("revenue") and out.get("op") is not None:
            return out
    return None



def load_krx_listing():
    """KRX \uc0c1\uc7a5\uc815\ubcf4 (\uc2dc\ucd1d\u00b7\uc2dc\uc7a5 \ud3ec\ud568) \u2014 \uc2dc\ucd1d \ub9e4\ud551\uacfc \uc790\ub3d9 \uc720\ub2c8\ubc84\uc2a4\uc5d0 \uacf5\uc6a9."""
    if not HAS_FDR:
        return None
    try:
        return fdr.StockListing("KRX")
    except Exception as e:
        print(f"  [krx listing fail] {e}")
        return None


def load_marcaps(krx):
    if krx is None:
        return {}
    code_col = "Code" if "Code" in krx.columns else "Symbol"
    return {str(c).zfill(6): float(v) for c, v in zip(krx[code_col], krx["Marcap"])
            if v == v and v}



def build_auto_universe(marcap_df):
    """KRX \ub9ac\uc2a4\ud305\uc5d0\uc11c \uc2dc\ucd1d \uc870\uac74\uc73c\ub85c \uc790\ub3d9 \uc120\ubcc4 (\uc6b0\uc120\uc8fc\u00b7\uc2a4\ud329 \uc81c\uc678)."""
    out = {}
    try:
        code_col = "Code" if "Code" in marcap_df.columns else "Symbol"
        df = marcap_df.copy()
        if "Market" in df.columns:
            df = df[df["Market"].isin(AUTO_MARKETS)]
        df = df[(df["Marcap"] >= AUTO_MARCAP_MIN) & (df["Marcap"] <= AUTO_MARCAP_MAX)]
        df = df.sort_values("Marcap", ascending=False)
        for _, r in df.iterrows():
            code = str(r[code_col]).zfill(6)
            name = str(r["Name"])
            if not code.endswith("0"):
                continue
            if "\uc2a4\ud329" in name or "SPAC" in name.upper():
                continue
            out[code] = name
            if len(out) >= AUTO_COUNT:
                break
    except Exception as e:
        print(f"  [auto universe fail] {e}")
    return out



def asset_metrics(m, fy, marcap):
    if not fy:
        return
    eq = fy.get("equity")
    if eq and eq > 0 and marcap:
        m["pbr"] = marcap / eq
    cash = sum(fy.get(k, 0) or 0 for k in ("cash", "st_fin", "st_fin2"))
    debt = sum(fy.get(k, 0) or 0 for k in ("st_debt", "lt_debt", "bond", "cur_lt_debt"))
    if cash or debt:
        m["net_cash"] = cash - debt
        if marcap:
            m["net_cash_ratio"] = (cash - debt) / marcap
    hard = sum(fy.get(k, 0) or 0 for k in ("ppe", "invest_re"))
    if hard and marcap:
        m["hard_asset_ratio"] = hard / marcap
    tr = fy.get("treasury")
    if tr and eq and eq > 0:
        m["treasury_ratio"] = abs(tr) / eq


def sector_relative(rows):
    """\uc720\ub2c8\ubc84\uc2a4 \uc911\uc559\uac12 \ub300\ube44 PBR/PER \uc0c1\ub300\ube44\uc728 (1.0 \ubbf8\ub9cc\uc774\uba74 \ud3c9\uade0\ubcf4\ub2e4 \uc2f8\ub2e4)."""
    import statistics as st
    for key, out in (("pbr", "pbr_rel"), ("per", "per_rel")):
        vals = [r[key] for r in rows if r.get(key) and r[key] > 0]
        if len(vals) < 3:
            continue
        med = st.median(vals)
        if med <= 0:
            continue
        for r in rows:
            if r.get(key) and r[key] > 0:
                r[out] = r[key] / med


def fetch_price(stock_code):
    if not HAS_FDR:
        return None
    try:
        df = fdr.DataReader(stock_code).tail(260)
        last = float(df["Close"].iloc[-1])
        return {"last": last,
                "drawdown": last / float(df["Close"].max()) - 1,
                "ret_3m": last / float(df["Close"].iloc[-63]) - 1 if len(df) >= 63 else None,
                "spark": [round(float(x), 1) for x in df["Close"].iloc[::5]]}
    except Exception as e:
        print(f"  [price fail] {stock_code}: {e}")
        return None


def score_parts(m):
    """\ucd1d 100\uc810 = \ubaa8\uba58\ud14030 + \uc774\uc775\uc758\uc9c810 + \ubd84\uae30\ubc29\ud5a510 + \ub20c\ub9bc15 + \ubbf8\ubc18\uc6015
                 + \uc790\uc0b0\uac00\uce5820 + \uc0c1\ub300\uc800\ud3c9\uac0010"""
    p = {}
    p["momentum"] = (min(max((m.get("rev_yoy") or 0) / 0.30, 0), 1) * 8
                     + min(max((m.get("op_yoy") or 0) / 0.50, 0), 1) * 11
                     + (5.5 if m.get("q_op_yoy") is None
                        else min(max(m["q_op_yoy"] / 0.50, 0), 1) * 11))
    gap = m.get("ni_op_gap")
    p["quality"] = 5 if gap is None else max(0, 1 - min(gap / 0.60, 1)) * 10
    d = m.get("q_opm_delta")
    p["direction"] = 5 if d is None else min(max((d + 0.05) / 0.05, 0), 1) * 10
    dd = m.get("drawdown")
    p["pressed"] = 7.5 if dd is None else min(max(-dd / 0.40, 0), 1) * 15
    r3 = m.get("ret_3m")
    p["unrun"] = 2.5 if r3 is None else min(max((0.10 - r3) / 0.30, 0), 1) * 5
    a = 0.0
    pbr = m.get("pbr")
    a += 4 if pbr is None else min(max((1.0 - pbr) / 0.5, 0), 1) * 8
    ncr = m.get("net_cash_ratio")
    a += 3 if ncr is None else min(max(ncr / 0.40, 0), 1) * 6
    har = m.get("hard_asset_ratio")
    a += 1.5 if har is None else min(max(har / 1.0, 0), 1) * 3
    tr = m.get("treasury_ratio")
    a += 1.5 if tr is None else min(max(tr / 0.10, 0), 1) * 3
    p["asset"] = a
    rel = 0.0
    pr = m.get("pbr_rel")
    rel += 2.5 if pr is None else min(max((1.0 - pr) / 0.6, 0), 1) * 5
    er = m.get("per_rel")
    rel += 2.5 if er is None else min(max((1.0 - er) / 0.6, 0), 1) * 5
    p["relative"] = rel
    return {k: round(v, 1) for k, v in p.items()}


def flags(m):
    out = []
    if (m.get("q_opm_delta") or 0) < -0.03:
        out.append("\ucd5c\uadfc\ubd84\uae30 \ub9c8\uc9c4 \uc545\ud654 \u2014 \uc9c0\uc5d4\uc528 1Q \ud328\ud134")
    if (m.get("ni_op_gap") or 0) > 0.5:
        out.append("\uc21c\uc774\uc775-\uc601\uc5c5\uc774\uc775 \uad34\ub9ac \ud07c \u2014 \uc77c\ud68c\uc131 \uc758\uc2ec, \uc8fc\uc11d \ud655\uc778")
    if (m.get("ret_3m") or 0) > 0.30:
        out.append("\ucd5c\uadfc 3\uac1c\uc6d4 \uae09\ub4f1 \u2014 \uc774\ubbf8 \ubc18\uc601\ub410\uc744 \uc218 \uc788\uc74c")
    if m.get("rev_yoy") is None:
        out.append("\uc7ac\ubb34 \ub370\uc774\ud130 \ubbf8\ud655\ubcf4 \u2014 \uc218\ub3d9 \ud655\uc778 \ud544\uc694")
    if (m.get("pbr") or 9) < 1.0 and (m.get("net_cash_ratio") or 0) > 0.20:
        out.append("\u2605 PBR 1\ubc30 \ubbf8\ub9cc + \uc21c\ud604\uae08\uc774 \uc2dc\ucd1d\uc758 20% \uc774\uc0c1 \u2014 \uc790\uc0b0\uac00\uce58 \uc6b0\ub7c9")
    if (m.get("treasury_ratio") or 0) > 0.10:
        out.append("\u2605 \uc790\uc0ac\uc8fc \uc790\ubcf8\uc758 10% \uc774\uc0c1 \ubcf4\uc720 \u2014 \uc8fc\uc8fc\ud658\uc6d0 \uc5ec\ub825")
    if (m.get("net_cash") or 0) < 0 and 0 < (m.get("pbr") or 0) < 1.0:
        out.append("PBR 1\ubc30 \ubbf8\ub9cc\uc774\ub098 \uc21c\ucc28\uc785 \uc0c1\ud0dc \u2014 \ubd80\ucc44\uad6c\uc870 \ud655\uc778 \ud544\uc694")
    return out


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>\uc2e4\uc801-\uc8fc\uac00 \uad34\ub9ac \uc2a4\ud06c\ub9ac\ub108</title>
<style>
  :root{
    --bg:#101623; --card:#1a2232; --line:#28324a;
    --tx:#e8ecf4; --mut:#8b94a7;
    --up:
    --dn:
    --q:
    --dir:
    --un:
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--tx);
       font-family:Pretendard,-apple-system,"Malgun Gothic",sans-serif;
       font-variant-numeric:tabular-nums;padding:28px 20px 60px;max-width:1100px;margin:0 auto}
  header{margin-bottom:26px}
  h1{font-size:1.45rem;font-weight:800;letter-spacing:-.02em}
  h1 em{font-style:normal;color:var(--up)}
  .sub{color:var(--mut);font-size:.85rem;margin-top:6px}
  .legend{display:flex;flex-wrap:wrap;gap:14px;margin:18px 0 8px;font-size:.78rem;color:var(--mut)}
  .legend span{display:flex;align-items:center;gap:6px}
  .dot{width:10px;height:10px;border-radius:2px;display:inline-block}
  table{width:100%;border-collapse:collapse;font-size:.88rem}
  th{color:var(--mut);font-weight:600;font-size:.75rem;text-align:right;
     padding:10px 8px;border-bottom:1px solid var(--line);cursor:pointer;user-select:none;white-space:nowrap}
  th:first-child,th:nth-child(2){text-align:left}
  th.sorted{color:var(--tx)}
  td{padding:12px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}
  td:first-child,td:nth-child(2){text-align:left}
  tr.row{cursor:pointer;transition:background .12s}
  tr.row:hover{background:#1e2740}
  tr.row:focus-visible{outline:2px solid var(--dn);outline-offset:-2px}
  .rank{color:var(--mut);width:34px}
  .nm{font-weight:700}
  .cd{color:var(--mut);font-size:.75rem;margin-left:6px;font-weight:400}
  .pos{color:var(--up)} .neg{color:var(--dn)}
  .score{font-weight:800;font-size:1rem}
  .bar{display:flex;height:8px;width:150px;border-radius:4px;overflow:hidden;background:#0c111c;margin-left:auto;margin-top:5px}
  .bar i{display:block;height:100%}
  .detail{display:none;background:#141b2b}
  .detail.open{display:table-row}
  .detail td{padding:16px 14px 20px;text-align:left;white-space:normal}
  .dgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:12px}
  .dcell{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px}
  .dcell b{display:block;font-size:.7rem;color:var(--mut);font-weight:600;margin-bottom:4px}
  .dcell span{font-size:1rem;font-weight:700}
  .flag{color:#ffb224;font-size:.82rem;margin-top:4px}
  .flag::before{content:"\u26a0 "}
  .todo{margin-top:14px;padding:12px 14px;background:var(--card);border-left:3px solid var(--dn);
        border-radius:0 8px 8px 0;font-size:.82rem;color:var(--mut);line-height:1.7}
  .todo b{color:var(--tx)}
  footer{margin-top:34px;color:var(--mut);font-size:.75rem;line-height:1.8}
  @media(max-width:720px){
    body{padding:16px 10px 40px}
    h1{font-size:1.15rem}
    .bar{width:64px;height:6px}
    th,td{padding:8px 4px;font-size:.72rem}
    .rank{width:20px}
    .cd{display:none}
    .score{font-size:.85rem}
    .dgrid{grid-template-columns:repeat(2,1fr);gap:8px}
    .dcell{padding:8px 9px}
    .dcell span{font-size:.85rem}
    table{display:block;overflow-x:auto;-webkit-overflow-scrolling:touch}
    tr.row td:nth-child(n+6){display:none}
  }
  @media (prefers-reduced-motion: reduce){ *{transition:none!important} }
</style>
</head>
<body>
<header>
  <h1>\uc2e4\uc801 <em>\u2191</em> \u00b7 \uc8fc\uac00 <span style="color:var(--dn)">\u2193</span> \uad34\ub9ac \uc2a4\ud06c\ub9ac\ub108</h1>
  <div class="sub">\uc0dd\uc131 __GENERATED__ \u00b7 \uc720\ub2c8\ubc84\uc2a4 __COUNT__\uc885\ubaa9 \u00b7 \uc815\ub82c: \uc5f4 \uc81c\ubaa9 \ud074\ub9ad \u00b7 \uc0c1\uc138: \ud589 \ud074\ub9ad</div>
  <div class="legend">
    <span><i class="dot" style="background:var(--up)"></i>\uc2e4\uc801 \ubaa8\uba58\ud140 (30)</span>
    <span><i class="dot" style="background:var(--q)"></i>\uc774\uc775\uc758 \uc9c8 (10)</span>
    <span><i class="dot" style="background:var(--dir)"></i>\ubd84\uae30 \ubc29\ud5a5 (10)</span>
    <span><i class="dot" style="background:var(--dn)"></i>\uc8fc\uac00 \ub20c\ub9bc (15)</span>
    <span><i class="dot" style="background:var(--un)"></i>\ubbf8\ubc18\uc601 (5)</span>
    <span><i class="dot" style="background:var(--as)"></i>\uc790\uc0b0\uac00\uce58 (20)</span>
    <span><i class="dot" style="background:var(--rl)"></i>\uc0c1\ub300 \uc800\ud3c9\uac00 (10)</span>
  </div>
  <div class="sub" style="margin-top:6px">PSR = \uc2dc\ucd1d\u00f7\ub9e4\ucd9c (\ub0ae\uc744\uc218\ub85d \ub9e4\ucd9c \ub300\ube44 \uc2dc\ucd1d\uc774 \uc300) \u00b7 PER = \uc2dc\ucd1d\u00f7\uc21c\uc774\uc775</div>
</header>

<table id="tbl">
  <thead><tr>
    <th data-k="rank">
    <th data-k="score" class="sorted">\uc2a4\ucf54\uc5b4 \u25be</th>
    <th data-k="rev_yoy">\ub9e4\ucd9c YoY</th><th data-k="op_yoy">\uc601\uc5c5\uc775 YoY</th>
    <th data-k="q_op_yoy">\ucd5c\uadfc\ubd84\uae30 \uc601\uc5c5\uc775</th><th data-k="pbr">PBR</th><th data-k="psr">PSR</th><th data-k="per">PER</th>
    <th data-k="drawdown">\uace0\uc810\ub300\ube44</th>
    <th data-k="ret_3m">3\uac1c\uc6d4</th>
  </tr></thead>
  <tbody id="body"></tbody>
</table>

<div class="todo"><b>\ub7ad\ud0b9\uc740 \ud6c4\ubcf4 \ucd95\uc18c\uc6a9\uc785\ub2c8\ub2e4 \u2014 \uc0c1\uc704 \uc885\ubaa9 \ub9e4\uc218 \uac80\ud1a0 \uc804 DART \uc6d0\ubb38\uc5d0\uc11c \ubc18\ub4dc\uc2dc:</b><br>
\u2460 \uc218\uc8fc\uc794\uace0 \ucd94\uc774(\ubcf4\uace0\uc11c '\uc218\uc8fc\uc0c1\ud669' \ud45c \u2014 API \uc790\ub3d9\uc218\uc9d1 \ubd88\uac00) &nbsp;
\u2461 \uc21c\uc774\uc775 \ub0b4 \uc77c\ud68c\uc131 \ubd84\ud574(\uae08\uc735\uc218\uc775 \uc8fc\uc11d: \uc678\ud658\u00b7\ud30c\uc0dd\u00b7\ucc98\ubd84\uc774\uc775) &nbsp;
\u2462 \ub099\ud3ed \uc6d0\uc778 \uacf5\uc2dc(\uc870\ud68c\uacf5\uc2dc\u00b7\uc815\uc815\uacf5\uc2dc)</div>

<footer>\uc2a4\ucf54\uc5b4 \uad6c\uc131: \uc2e4\uc801 \ubaa8\uba58\ud140 40 + \uc774\uc775\uc758 \uc9c8 15 + \ucd5c\uadfc\ubd84\uae30 \ub9c8\uc9c4 \ubc29\ud5a5 15 + \uc8fc\uac00 \ub20c\ub9bc 20 + \ubbf8\ubc18\uc601 10 = 100.<br>
\ub370\uc774\ud130: OpenDART(\uc7ac\ubb34) \u00b7 FinanceDataReader(\uc8fc\uac00). \ubcf8 \ud654\uba74\uc740 \ub370\uc774\ud130 \uc815\ub9ac\uc774\uba70 \ud22c\uc790 \uad8c\uc720\uac00 \uc544\ub2d9\ub2c8\ub2e4.</footer>

<script>
const DATA = __DATA__;
const fmtx = (v)=> v==null ? '<span style="color:var(--mut)">\u2014</span>'
  : `${v.toFixed(1)}x`;
const fmt = (v,pct=true)=> v==null ? '<span style="color:var(--mut)">\u2014</span>'
  : `<span class="${v>=0?'pos':'neg'}">${(v*100).toFixed(1)}%</span>`;
const fmtKRW = (v)=> v==null ? '\u2014'
  : (Math.abs(v)>=1e12 ? (v/1e12).toFixed(2)+'\uc870\uc6d0' : Math.round(v/1e8).toLocaleString()+'\uc5b5\uc6d0');
const COLORS={momentum:'var(--up)',quality:'var(--q)',direction:'var(--dir)',pressed:'var(--dn)',unrun:'var(--un)',asset:'var(--as)',relative:'var(--rl)'};
const LABELS={momentum:'\uc2e4\uc801 \ubaa8\uba58\ud140',quality:'\uc774\uc775\uc758 \uc9c8',direction:'\ubd84\uae30 \ubc29\ud5a5',pressed:'\uc8fc\uac00 \ub20c\ub9bc',unrun:'\ubbf8\ubc18\uc601',asset:'\uc790\uc0b0\uac00\uce58',relative:'\uc0c1\ub300 \uc800\ud3c9\uac00'};
let sortKey='score', asc=false;

function render(){
  const rows=[...DATA].sort((a,b)=>{
    const x=a[sortKey]??-1e9, y=b[sortKey]??-1e9;
    return asc ? x-y : y-x;
  });
  const tb=document.getElementById('body'); tb.innerHTML='';
  rows.forEach((d,i)=>{
    const bar=Object.keys(COLORS).map(k=>
      `<i style="width:${d.parts[k]}%;background:${COLORS[k]}" title="${LABELS[k]} ${d.parts[k]}"></i>`).join('');
    const tr=document.createElement('tr');
    tr.className='row'; tr.tabIndex=0;
    tr.innerHTML=`<td class="rank">${i+1}</td>
      <td><span class="nm">${d.name}</span><span class="cd">${d.code}</span></td>
      <td><span class="score">${d.score}</span><div class="bar">${bar}</div></td>
      <td>${fmt(d.rev_yoy)}</td><td>${fmt(d.op_yoy)}</td>
      <td>${fmt(d.q_op_yoy)}</td><td>${fmtx(d.pbr)}</td><td>${fmtx(d.psr)}</td><td>${fmtx(d.per)}</td><td>${fmt(d.drawdown)}</td><td>${fmt(d.ret_3m)}</td>`;
    const det=document.createElement('tr');
    det.className='detail';
    const cells=Object.keys(COLORS).map(k=>
      `<div class="dcell"><b>${LABELS[k]}</b><span style="color:${COLORS[k]}">${d.parts[k]}\uc810</span></div>`).join('');
    const fl=(d.flags||[]).map(f=>`<div class="flag">${f}</div>`).join('')||'<div style="color:var(--mut);font-size:.82rem">\uacbd\uace0 \ud50c\ub798\uadf8 \uc5c6\uc74c</div>';
    det.innerHTML=`<td colspan="11"><div class="dgrid">${cells}
      <div class="dcell"><b>\ucd5c\uadfc\ubd84\uae30 \ub9e4\ucd9c</b><span>${fmtKRW(d.q_rev)}</span></div>
      <div class="dcell"><b>\ucd5c\uadfc\ubd84\uae30 \uc601\uc5c5\uc774\uc775</b><span class="${(d.q_op||0)>=0?'pos':'neg'}">${fmtKRW(d.q_op)}</span></div>
      <div class="dcell"><b>\uc5f0\uac04 OPM</b><span>${d.opm==null?'\u2014':(d.opm*100).toFixed(1)+'%'}</span></div>
      <div class="dcell"><b>\ubd84\uae30 OPM \ubcc0\ud654</b><span>${d.q_opm_delta==null?'\u2014':(d.q_opm_delta*100).toFixed(1)+'%p'}</span></div>
      <div class="dcell"><b>\ud604\uc7ac\uac00</b><span>${d.last==null?'\u2014':d.last.toLocaleString()+'\uc6d0'}</span></div>
      <div class="dcell"><b>\uc2dc\uac00\ucd1d\uc561</b><span>${d.marcap==null?'\u2014':(d.marcap/1e12>=1?(d.marcap/1e12).toFixed(2)+'\uc870\uc6d0':Math.round(d.marcap/1e8).toLocaleString()+'\uc5b5\uc6d0')}</span></div>
      <div class="dcell"><b>\uc21c\ud604\uae08</b><span class="${(d.net_cash||0)>=0?'pos':'neg'}">${fmtKRW(d.net_cash)}</span></div>
      <div class="dcell"><b>\uc21c\ud604\uae08/\uc2dc\ucd1d</b><span>${d.net_cash_ratio==null?'\u2014':(d.net_cash_ratio*100).toFixed(0)+'%'}</span></div>
      <div class="dcell"><b>\uc720\ud615\uc790\uc0b0+\ud22c\uc790\ubd80\ub3d9\uc0b0/\uc2dc\ucd1d</b><span>${d.hard_asset_ratio==null?'\u2014':(d.hard_asset_ratio*100).toFixed(0)+'%'}</span></div>
      <div class="dcell"><b>\uc790\uc0ac\uc8fc/\uc790\ubcf8</b><span>${d.treasury_ratio==null?'\u2014':(d.treasury_ratio*100).toFixed(1)+'%'}</span></div>
      <div class="dcell"><b>PBR \uc0c1\ub300(\uc911\uc559\uac12=1)</b><span>${d.pbr_rel==null?'\u2014':d.pbr_rel.toFixed(2)}</span></div>
      <div class="dcell"><b>PER \uc0c1\ub300(\uc911\uc559\uac12=1)</b><span>${d.per_rel==null?'\u2014':d.per_rel.toFixed(2)}</span></div>
      <div class="dcell"><b>\ub9e4\ucd9c/\uc2dc\ucd1d</b><span>${d.psr==null?'\u2014':'\ub9e4\ucd9c\uc774 \uc2dc\ucd1d\uc758 '+(1/d.psr).toFixed(1)+'\ubc30'}</span></div></div>${fl}</td>`;
    tr.addEventListener('click',()=>det.classList.toggle('open'));
    tr.addEventListener('keydown',e=>{if(e.key==='Enter')det.classList.toggle('open')});
    tb.append(tr,det);
  });
}
document.querySelectorAll('th[data-k]').forEach(th=>{
  th.addEventListener('click',()=>{
    const k=th.dataset.k;
    if(sortKey===k) asc=!asc; else {sortKey=k; asc=false;}
    document.querySelectorAll('th').forEach(t=>{t.classList.remove('sorted');t.textContent=t.textContent.replace(/ [\u25be\u25b4]$/,'')});
    th.classList.add('sorted'); th.textContent+= asc?' \u25b4':' \u25be';
    render();
  });
});
render();
</script>
</body>
</html>"""


def main():
    if API_KEY == "PUT_YOUR_KEY_HERE":
        raise SystemExit("ERROR: set your DART API key (replace PUT_YOUR_KEY_HERE)")

    print("Downloading corp_code map...")
    codes = load_corp_codes(API_KEY)
    krx = load_krx_listing()
    marcaps = load_marcaps(krx)

    universe = dict(UNIVERSE)
    if AUTO_MODE and krx is not None:
        auto = build_auto_universe(krx)
        added = 0
        for c, n in auto.items():
            if c not in universe:
                universe[c] = n
                added += 1
        print(f"Auto universe: +{added} stocks (total {len(universe)})")
    est_min = len(universe) * 3 // 60 + 1
    print(f"Estimated time: ~{est_min} min for {len(universe)} stocks")

    rows = []
    for stock, name in universe.items():
        print(f"\u25b6 {name}({stock})")
        corp = codes.get(stock)
        m = {"code": stock, "name": name}
        fy_cur = None
        if corp:
            fy_cur = fetch_fs(API_KEY, corp, FY_CUR, REPRT_ANNUAL)
            fy_prv = fetch_fs(API_KEY, corp, FY_PRV, REPRT_ANNUAL)
            q_cur = fetch_fs(API_KEY, corp, Q_YEAR, REPRT_Q1)
            q_prv = fetch_fs(API_KEY, corp, str(int(Q_YEAR) - 1), REPRT_Q1)
            time.sleep(0.6)
            if fy_cur and fy_prv:
                if fy_prv.get("revenue"):
                    m["rev_yoy"] = fy_cur["revenue"] / fy_prv["revenue"] - 1
                if fy_prv.get("op"):
                    m["op_yoy"] = (fy_cur["op"] - fy_prv["op"]) / abs(fy_prv["op"])
                m["opm"] = fy_cur["op"] / fy_cur["revenue"]
                if fy_cur.get("ni") is not None and fy_cur.get("op"):
                    m["ni_op_gap"] = abs(fy_cur["ni"] - fy_cur["op"]) / abs(fy_cur["op"])
            if q_cur:
                if q_cur.get("revenue"):
                    m["q_rev"] = q_cur["revenue"]
                if q_cur.get("op") is not None:
                    m["q_op"] = q_cur["op"]
            if q_cur and q_prv:
                if q_prv.get("op"):
                    m["q_op_yoy"] = (q_cur["op"] - q_prv["op"]) / abs(q_prv["op"])
                if q_cur.get("revenue") and q_prv.get("revenue"):
                    m["q_opm_delta"] = (q_cur["op"] / q_cur["revenue"]
                                        - q_prv["op"] / q_prv["revenue"])
        else:
            print("  corp_code not found")
        p = fetch_price(stock)
        if p:
            m.update({k: p[k] for k in ("last", "drawdown", "ret_3m")})
        mc = marcaps.get(stock)
        if mc:
            m["marcap"] = mc
            if fy_cur and fy_cur.get("revenue"):
                m["psr"] = mc / fy_cur["revenue"]
            if fy_cur and fy_cur.get("ni") and fy_cur["ni"] > 0:
                m["per"] = mc / fy_cur["ni"]
            asset_metrics(m, fy_cur, mc)
        rows.append(m)

    sector_relative(rows)
    for m in rows:
        m["parts"] = score_parts(m)
        m["score"] = round(sum(m["parts"].values()), 1)
        m["flags"] = flags(m)
    rows.sort(key=lambda r: r["score"], reverse=True)


    outdir0 = os.environ.get("OUTPUT_DIR", ".")
    os.makedirs(outdir0, exist_ok=True)
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("parts", "flags")}
                  for r in rows]).to_csv(os.path.join(outdir0, "screener_result.csv"),
                                         index=False, encoding="utf-8-sig")


    html = (HTML_TEMPLATE
            .replace("__DATA__", json.dumps(rows, ensure_ascii=False))
            .replace("__GENERATED__", datetime.now().strftime("%Y-%m-%d %H:%M"))
            .replace("__COUNT__", str(len(rows))))
    outdir = os.environ.get("OUTPUT_DIR", ".")
    os.makedirs(outdir, exist_ok=True)
    out = os.path.abspath(os.path.join(outdir, "index.html"))
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(outdir, "screener_result.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nDone: {out}")
    if os.environ.get("HEADLESS") or "--headless" in sys.argv:
        print("Headless mode - browser not opened.")
    else:
        print("Opening browser...")
        webbrowser.open("file://" + out)


if __name__ == "__main__":
    main()
