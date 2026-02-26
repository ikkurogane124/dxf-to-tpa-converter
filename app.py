import streamlit as st
import numpy as np

def convert_auto_dimensions(dxf_file):
    try:
        content = dxf_file.getvalue().decode('utf-8', errors='ignore').splitlines()
        raw_lines, circles = [], []
        current_entity, temp_data = None, {}

        # 1. LETTURA DATI DAL DXF
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

        if not raw_lines and not circles:
            return "Errore: Il file DXF sembra vuoto o non leggibile.", 0, 0

        # 2. CALCOLO AUTOMATICO INGOMBRO E ORIGINE
        # Troviamo i minimi e massimi assoluti per definire il pannello (DL e DH)
        all_x = ([l['x1'] for l in raw_lines] + [l['x2'] for l in raw_lines] + 
                 [c['cx'] + c['r'] for c in circles] + [c['cx'] - c['r'] for c in circles])
        all_y = ([l['y1'] for l in raw_lines] + [l['y2'] for l in raw_lines] + 
                 [c['cy'] + c['r'] for c in circles] + [c['cy'] - c['r'] for c in circles])
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Dimensioni del pannello calcolate dinamicamente
        dl = round(max_x - min_x, 2)
        dh = round(max_y - min_y, 2)

        # 3. COSTRUZIONE FILE TPA
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

        # Scrittura Linee con reset origine a 0,0
        for l in raw_lines:
            x1, y1 = round(l['x1'] - min_x, 2), round(l['y1'] - min_y, 2)
            x2, y2 = round(l['x2'] - min_x, 2), round(l['y2'] - min_y, 2)
            header.append(f"W#2201{{ ::WTl \n#1={x2} #8054={x1} #2={y2} #8055={y1} #3=0 #8056=0 #8015=1 #9022=0 }}W")

        # Scrittura Fori con reset origine, Utensile 121 e macro di attacco
        for c in circles:
            cx, cy = round(c['cx'] - min_x, 2), round(c['cy'] - min_y, 2)
            r = round(c['r'], 2)
            header.append(f"W#89{{ ::WTs \n#1={cx} #2={cy} #3=0 #8015=0 #8101=0 #205=121 #40=0 #201=1 #203=1 #1001=100 #8135=0 #8136=0 #43=0 }}W")
            header.append(f"W#2101{{ ::WTa \n#1=0 #2=0 #8015=1 #3=0 #8056=0 #31={r} #32=0 #34=0 #36=0 #8017={r} }}W")

        header.append("}SIDE")
        
        # Generazione automatica degli altri lati (SIDE 2-6)
        for s in range(2, 7):
            l_v, h_v, s_v = (dl, dh, 20) if s == 2 else (dl, 20, 20) if s in [3, 5] else (dh, 20, dl)
            header.append(f"SIDE#{s}{{\n$=side  {s}\n::LF={l_v} HF={h_v} SF={s_v}\n}}SIDE")
        
        header.append("}")
        
        return "\r\n".join(header), dl, dh
    except Exception as e:
        return f"Errore durante la conversione: {str(e)}", 0, 0

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="TPA Smart Converter", page_icon="⚙️", layout="centered")

st.title("⚙️ TPA Smart Converter")
st.subheader("Conversione automatica DXF -> TPA (Tool 121)")

st.info("""
**Come funziona:**
1. Carica il file DXF.
2. Il sistema calcola da solo le dimensioni del pannello.
3. Il disegno viene spostato automaticamente all'origine (0,0).
4. Scarica il file pronto per EdiCad.
""")

uploaded_file = st.file_uploader("Scegli un file DXF", type="dxf")

if uploaded_file:
    tpa_content, final_dl, final_dh = convert_auto_dimensions(uploaded_file)
    
    if isinstance(tpa_content, str) and "Errore" in tpa_content:
        st.error(tpa_content)
    else:
        st.markdown(f"### ✅ Analisi Completata")
        col1, col2 = st.columns(2)
        col1.metric("Lunghezza (DL)", f"{final_dl} mm")
        col2.metric("Altezza (DH)", f"{final_dh} mm")
        
        st.success("File TPA generato correttamente!")
        
        st.download_button(
            label="📥 Scarica File .TPA",
            data=tpa_content,
            file_name=uploaded_file.name.replace(".dxf", ".tpa"),
            mime="text/plain"
        )

st.divider()
st.caption("Configurazione: Tool 121 | Reset Origine: Automatico | Formato: EdiCad TPA")