import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def convert_dxf_to_tpa_with_preview(dxf_file):
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
            return None, 0, 0, [], [], 0, 0

        # 2. CALCOLO INGOMBRO E ORIGINE
        all_x = ([l['x1'] for l in raw_lines] + [l['x2'] for l in raw_lines] + 
                 [c['cx'] + c['r'] for c in circles] + [c['cx'] - c['r'] for c in circles])
        all_y = ([l['y1'] for l in raw_lines] + [l['y2'] for l in raw_lines] + 
                 [c['cy'] + c['r'] for c in circles] + [c['cy'] - c['r'] for c in circles])
        
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        dl, dh = round(max_x - min_x, 2), round(max_y - min_y, 2)

        # 3. COSTRUZIONE FILE TPA
        header = [
            "TPA\\ALBATROS\\EDICAD\\00.00:561:1;698",
            f"$=c:\\albatros\\product\\import\\{dxf_file.name}",
            "::SIDE=1;",
            f"::UNm DL={dl} DH={dh} DS=20 OX=0 OY=0 OZ=0",
            "VAR{\n}VAR\nOPTI{\n}OPTI\nSIDE#1{",
            "$=side  1",
            f"::LF={dl} HF={dh} SF=20"
        ]

        for l in raw_lines:
            x1, y1 = round(l['x1'] - min_x, 2), round(l['y1'] - min_y, 2)
            x2, y2 = round(l['x2'] - min_x, 2), round(l['y2'] - min_y, 2)
            header.append(f"W#2201{{ ::WTl \n#1={x2} #8054={x1} #2={y2} #8055={y1} #3=0 #8056=0 #8015=1 #9022=0 }}W")

        for c in circles:
            cx, cy = round(c['cx'] - min_x, 2), round(c['cy'] - min_y, 2)
            r = round(c['r'], 2)
            header.append(f"W#89{{ ::WTs \n#1={cx} #2={cy} #3=0 #8015=0 #8101=0 #205=121 #40=0 #201=1 #203=1 #1001=100 #8135=0 #8136=0 #43=0 }}W")
            header.append(f"W#2101{{ ::WTa \n#1=0 #2=0 #8015=1 #3=0 #8056=0 #31={r} #32=0 #34=0 #36=0 #8017={r} }}W")

        header.append("}SIDE")
        for s in range(2, 7):
            l_v, h_v, s_v = (dl, dh, 20) if s == 2 else (dl, 20, 20) if s in [3, 5] else (dh, 20, dl)
            header.append(f"SIDE#{s}{{\n$=side  {s}\n::LF={l_v} HF={h_v} SF={s_v}\n}}SIDE")
        header.append("}")
        
        return "\r\n".join(header), dl, dh, raw_lines, circles, min_x, min_y
    except Exception as e:
        st.error(f"Errore: {e}")
        return None, 0, 0, [], [], 0, 0

# --- INTERFACCIA UTENTE ---
st.set_page_config(page_title="TPA Visual Converter", layout="wide")
st.title("🚀 DXF to TPA Visual Converter")

file = st.file_uploader("Carica il tuo file DXF", type="dxf")

if file:
    tpa_txt, dl, dh, lines, circles, ox, oy = convert_dxf_to_tpa_with_preview(file)
    
    if tpa_txt:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📊 Dati Pannello")
            st.metric("Lunghezza (DL)", f"{dl} mm")
            st.metric("Altezza (DH)", f"{dh} mm")
            st.success("Conversione completata con successo!")
            st.download_button("📥 Scarica .TPA", tpa_txt, file.name.replace(".dxf", ".tpa"))

        with col2:
            st.subheader("🖼️ Anteprima Grafica")
            fig, ax = plt.subplots()
            # Disegna Pannello
            rect = plt.Rectangle((0, 0), dl, dh, color='#D2B48C', alpha=0.5, label='Pannello')
            ax.add_patch(rect)
            # Disegna Linee
            for l in lines:
                ax.plot([l['x1']-ox, l['x2']-ox], [l['y1']-oy, l['y2']-oy], color='blue', linewidth=1)
            # Disegna Fori
            for c in circles:
                circle = plt.Circle((c['cx']-ox, c['cy']-oy), c['r'], color='red', fill=True)
                ax.add_patch(circle)
            
            ax.set_aspect('equal')
            plt.grid(True, linestyle='--', alpha=0.6)
            st.pyplot(fig)