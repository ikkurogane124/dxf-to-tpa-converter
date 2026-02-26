import streamlit as st
import io
import numpy as np

def convert_to_mirror_match(dxf_file):
    try:
        content = dxf_file.getvalue().decode('utf-8', errors='ignore').splitlines()
        raw_lines, circles = [], []
        current_entity, temp_data = None, {}

        # 1. LETTURA DXF
        for i, line in enumerate(content):
            line = line.strip()
            if line == "LINE": current_entity = "LINE"
            elif line == "CIRCLE": current_entity = "CIRCLE"
            if current_entity == "LINE":
                if line == "10": temp_data['x1'] = float(content[i+1])
                elif line == "20": temp_data['y1'] = float(content[i+1])
                elif line == "11": temp_data['x2'] = float(content[i+1])
                elif line == "21": temp_data['y2'] = float(content[i+1])
                if len(temp_data) == 4:
                    raw_lines.append(temp_data.copy()); temp_data = {}; current_entity = None
            elif current_entity == "CIRCLE":
                if line == "10": temp_data['cx'] = float(content[i+1])
                elif line == "20": temp_data['cy'] = float(content[i+1])
                elif line == "40": temp_data['r'] = float(content[i+1])
                if len(temp_data) == 3:
                    circles.append(temp_data.copy()); temp_data = {}; current_entity = None

        # 2. CALCOLO ORIGINE CON ARROTONDAMENTO FISSO
        all_x = [l['x1'] for l in raw_lines] + [l['x2'] for l in raw_lines] + [c['cx'] for c in circles]
        all_y = [l['y1'] for l in raw_lines] + [l['y2'] for l in raw_lines] + [c['cy'] for c in circles]
        
        # Usiamo un arrotondamento per evitare scarti di 0.00001 che spostano tutto
        min_x = round(min(all_x), 1) if all_x else 0
        min_y = round(min(all_y), 1) if all_y else 0

        dl, dh = 1680.0, 512.0

        header = [
            "TPA\\ALBATROS\\EDICAD\\00.00:561:1;698",
            f"$=c:\\albatros\\product\\import\\{dxf_file.name}",
            "::SIDE=1;",
            f"::UNm DL={dl} DH={dh} DS=20 OX=0 OY=0 OZ=0",
            "::FLT0=0 FLT1=0 FLT2=0 FLT3=0 FLT4=0 FLT5=0 FLT6=0 FLT7=0",
            "VAR{\n}VAR",
            "OPTI{\n}OPTI",
            "SIDE#1{",
            "$=side  1",
            f"::LF={dl} HF={dh} SF=20"
        ]

        # 3. SCRITTURA LINEE (Arrotondate come l'originale)
        for l in raw_lines:
            x1 = round(l['x1'] - min_x, 2)
            y1 = round(l['y1'] - min_y, 2)
            x2 = round(l['x2'] - min_x, 2)
            y2 = round(l['y2'] - min_y, 2)
            header.append(f"W#2201{{ ::WTl \n#1={x2} #8054={x1} #2={y2} #8055={y1} #3=0 #8056=0 #8015=1 #9022=0 }}W")

        # 4. SCRITTURA FORI (Tool 121 + Macro Identica)
        for c in circles:
            cx = round(c['cx'] - min_x, 2)
            cy = round(c['cy'] - min_y, 2)
            r = round(c['r'], 2)
            header.append(f"W#89{{ ::WTs \n#1={cx} #2={cy} #3=0 #8015=0 #8101=0 #205=121 #40=0 #201=1 #203=1 #1001=100 #8135=0 #8136=0 #43=0 }}W")
            header.append(f"W#2101{{ ::WTa \n#1=0 #2=0 #8015=1 #3=0 #8056=0 #31={r} #32=0 #34=0 #36=0 #8017={r} }}W")

        header.append("}SIDE")
        
        for s in range(2, 7):
            l_v, h_v, s_v = (dl, dh, 20) if s == 2 else (dl, 20, 20) if s in [3, 5] else (dh, 20, dl)
            header.append(f"SIDE#{s}{{\n$=side  {s}\n::LF={l_v} HF={h_v} SF={s_v}\n}}SIDE")
        
        header.append("}")
        return "\r\n".join(header)
    except Exception as e:
        return f"Errore: {str(e)}"

st.title("🎯 TPA Mirror Match (Identico 100%)")
file = st.file_uploader("Carica il DXF", type="dxf")
if file:
    tpa_content = convert_to_mirror_match(file)
    st.download_button("📥 Scarica TPA Identico", tpa_content, f"{file.name.replace('.dxf', '.tpa')}")