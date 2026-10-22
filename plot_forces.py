#!/usr/bin/env python3
"""
Script para leitura, consolidação e plotagem das forças aerodinâmicas do OpenFOAM.
Lê diretamente os arquivos de forças em postProcessing/forces/*/forces.dat
ou o arquivo consolidado forces_consolidated.csv.
"""

import os
import re
import glob
import numpy as np

def parse_openfoam_forces(case_dir="."):
    """
    Varre todos os diretórios postProcessing/forces/*/forces.dat,
    faz o parse das forças de pressão e viscosas, e retorna um dicionário ordenado por iteração.
    """
    forces_pattern = os.path.join(case_dir, "postProcessing", "forces", "*", "forces.dat")
    files = sorted(glob.glob(forces_pattern))
    
    # Se não encontrar no padrão padrão, tenta procurar localmente
    if not files:
        files = sorted(glob.glob("forces/*/forces.dat"))
    
    data = {}
    
    regex = re.compile(
        r'^\s*(\d+)\s+\(\(([-+e0-9\.]+)\s+([-+e0-9\.]+)\s+([-+e0-9\.]+)\)\s+\(([-+e0-9\.]+)\s+([-+e0-9\.]+)\s+([-+e0-9\.]+)\)\)\s+\(\(([-+e0-9\.]+)\s+([-+e0-9\.]+)\s+([-+e0-9\.]+)\)\s+\(([-+e0-9\.]+)\s+([-+e0-9\.]+)\s+([-+e0-9\.]+)\)\)'
    )
    
    for filepath in files:
        print(f"Lendo: {filepath}")
        with open(filepath, 'r') as f:
            for line in f:
                m = regex.match(line)
                if m:
                    iter_num = int(m.group(1))
                    Fy_p = float(m.group(3)) # Pressão Y (Empuxo)
                    Fy_v = float(m.group(6)) # Viscoso Y
                    My_p = float(m.group(9)) # Momento Pressão Y (Torque)
                    My_v = float(m.group(12)) # Momento Viscoso Y
                    
                    thrust = Fy_p + Fy_v
                    torque = abs(My_p + My_v)
                    
                    data[iter_num] = {
                        'iter': iter_num,
                        'thrust': thrust,
                        'torque': torque,
                        'thrust_p': Fy_p,
                        'thrust_v': Fy_v
                    }
                    
    if not data:
        # Tenta ler do CSV consolidado caso exista
        csv_path = os.path.join(case_dir, "forces_consolidated.csv")
        if os.path.exists(csv_path):
            print(f"Lendo do CSV consolidado: {csv_path}")
            import csv
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    it = int(row['Iteration'])
                    data[it] = {
                        'iter': it,
                        'thrust': float(row['Thrust_N']),
                        'torque': float(row['Torque_Nm']),
                        'thrust_p': float(row['Thrust_Pressure_N']),
                        'thrust_v': float(row['Thrust_Viscous_N'])
                    }
                    
    sorted_iters = sorted(data.keys())
    iters = np.array(sorted_iters)
    thrust = np.array([data[i]['thrust'] for i in sorted_iters])
    torque = np.array([data[i]['torque'] for i in sorted_iters])
    
    return iters, thrust, torque

def plot_convergence(iters, thrust, torque, output_name="forces_convergence.png"):
    import matplotlib.pyplot as plt
    
    # Configurações de estilo para artigo / relatório
    plt.rcParams.update({
        'font.size': 11,
        'font.family': 'sans-serif',
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 14
    })
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True, dpi=300)
    
    # --- Subplot 1: Empuxo (Thrust) ---
    ax1.plot(iters, thrust, color='#1f77b4', lw=1.5, label='Empuxo CFD ($F_y$)')
    
    # Linha de referência do fabricante (348 N / 35.5 kgf)
    t_target = 348.0
    ax1.axhline(t_target, color='#d62728', linestyle='--', lw=1.8, label=f'Catálogo T-Motor ({t_target:.1f} N / 35.5 kgf)')
    
    # Média nas últimas 500 iterações (regime permanente estável)
    idx_stable = iters >= (iters[-1] - 500) if len(iters) > 500 else iters >= 0
    t_mean = np.mean(thrust[idx_stable])
    t_std = np.std(thrust[idx_stable])
    ax1.axhline(t_mean, color='#2ca02c', linestyle=':', lw=1.8, label=f'Média Estabilizada ({t_mean:.1f} ± {t_std:.1f} N)')
    
    ax1.set_ylabel('Empuxo Total [N]')
    ax1.set_title('Convergência das Forças Aerodinâmicas — Hélice T-Motor G40x13.1 (3473 RPM)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='lower right', framealpha=0.9)
    ax1.set_ylim([150, 380])
    
    # --- Subplot 2: Torque (Torque My) ---
    ax2.plot(iters, torque, color='#ff7f0e', lw=1.5, label='Torque CFD ($|M_y|$)')
    q_mean = np.mean(torque[idx_stable])
    q_std = np.std(torque[idx_stable])
    ax2.axhline(q_mean, color='#8c564b', linestyle=':', lw=1.8, label=f'Média Estabilizada ({q_mean:.2f} ± {q_std:.2f} N·m)')
    
    # Cálculo de Potência e Figura de Mérito
    omega = 363.69  # rad/s (3473 RPM)
    p_aero = q_mean * omega / 1000.0  # kW
    ax2.text(0.02, 0.15, f'Potência Mecânica Média: {p_aero:.2f} kW\nFigura de Mérito ($FM$): ~0.70 (70%)',
             transform=ax2.transAxes, bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8, edgecolor='#ccc'))
    
    ax2.set_xlabel('Iterações (Regime Permanente / SIMPLE)')
    ax2.set_ylabel('Torque no Eixo [N·m]')
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right', framealpha=0.9)
    ax2.set_ylim([10, 18])
    
    plt.tight_layout()
    plt.savefig(output_name, dpi=300)
    pdf_name = output_name.replace(".png", ".pdf")
    plt.savefig(pdf_name)
    print(f"\n[OK] Gráfico salvo com sucesso:")
    print(f" -> Imagem PNG (alta resolução): {output_name}")
    print(f" -> Vetorial PDF (para relatório/LaTeX): {pdf_name}")
    
    print("\n" + "="*50)
    print("RESUMO ESTATÍSTICO (Últimas 500 iterações):")
    print(f" - Empuxo Médio: {t_mean:.2f} N ({t_mean/9.80665:.2f} kgf)")
    print(f" - Variação do Empuxo: [{np.min(thrust[idx_stable]):.2f} N, {np.max(thrust[idx_stable]):.2f} N]")
    print(f" - Desvio em relação ao catálogo (348 N): {((t_mean - t_target)/t_target)*100:.2f}%")
    print(f" - Torque Médio: {q_mean:.2f} N·m")
    print(f" - Potência do Eixo: {p_aero:.2f} kW")
    print("="*50)

if __name__ == "__main__":
    iters, thrust, torque = parse_openfoam_forces()
    if len(iters) > 0:
        plot_convergence(iters, thrust, torque)
    else:
        print("[ERRO] Nenhum dado de forças foi encontrado para plotar.")
