# Simulação Aerodinâmica de Hélice com MRF no OpenFOAM-dev

Este repositório contém os arquivos de configuração e scripts para a simulação aerodinâmica estacionária (RANS) da hélice bipá de fibra de carbono **T-Motor G40x13.1 (40 polegadas)** utilizando o método de Referencial Móvel de Rotação (**MRF - Multiple Reference Frame**) no **OpenFOAM-dev** (`foamRun -solver incompressibleFluid`).

---

## 1. Especificações Técnicas e Dados de Referência

- **Objeto:** Hélice T-Motor G40x13.1 / U15 II KV80 ($D = 1,0164\text{ m}$, passo nominal $\approx 13,1"$).
- **Rotação:** $3473\text{ RPM}$ ($\Omega = 363,69\text{ rad/s}$ em torno do eixo $Y$, gerando empuxo em $+Y$ e jato axial em $-Y$).
- **Velocidade de Ponta:** $V_{\text{tip}} = 184,8\text{ m/s}$ ($\text{Mach}_{\text{tip}} \approx 0,54$).
- **Benchmark Experimental (Fabricante):**
  - Empuxo Estático ($T_{\text{target}}$): $\approx 348\text{ N}$ ($35,5\text{ kgf}$)
  - Torque no Eixo ($Q_{\text{target}}$): $\approx 17,8\text{ N}\cdot\text{m}$
- **Solver & Turbulência:** `foamRun` (`incompressibleFluid` / SIMPLE), modelo RAS `kOmegaSST`, malha de $\approx 6,15$ milhões de células.
- **Framework MRF (`constant/MRFProperties`):**
  - **Zona de Células e Faces (`cellZone` + `faceZone`):** `innerCylinder` ($Y \in [-0,14; +0,14]\text{ m}$, $R = 0,58\text{ m}$, gerada e conformada diretamente pelo `snappyHexMesh` em nível 4 via `searchableCylinder`, eliminando a borda em escada do `topoSet`).
  - **Eixo de Rotação (`axis`):** `(0 1 0)` | **Origem (`origin`):** `(0 -0.00800165 0)`.
  - **Condição na Pá (`propellerTip`):** `MRFnoSlip` em `0/U` e `fixedFluxPressure` em `0/p`.

---

## 2. Validação Física e Diagnóstico do Regime de Hover ($J \approx 0$)

### A. Validação na Janela Axial (`40 <= t <= 111`)
Durante as iterações **40 a 111**, enquanto o escoamento axial limpo atravessa o disco do rotor:
- **Empuxo atingido:** **$347,0\text{ N}$ a $374,4\text{ N}$** (precisão de **$99,7\%$** em `t = 111` frente ao valor experimental de bancada de $348\text{ N}$).
- **Torque no eixo:** **$-13,9\text{ a }-15,6\text{ N}\cdot\text{m}$**.
- **Padrão de escoamento:** Jato axial cilíndrico colimado com contração clássica de tubo de corrente (*vena contracta*) descendo livremente até o `outlet` no sentido $-Y$.

### B. Causa Raiz da Degradação Tardia na Malha Antiga: Borda em Escada do `topoSet`
Na malha anterior, a `cellZone innerCylinder` era criada após o `snappyHexMesh` usando `topoSet` (`cylinderToCell`) sobre uma malha cartesiana:
- Como as faces dos cubos cartesianos apontam nas direções $\pm X$ e $\pm Z$ (em vez da direção radial $\hat{r}$), a parede lateral do cilindro MRF formava uma **escada serrilhada**.
- Nessas faces em degrau, o fluxo de rotação do MRF $(\vec{\omega} \times \vec{r}_f) \cdot \vec{S}_f \neq 0$ (chegando a $\pm 190\text{ m/s} \times A_f$) injetava fontes/sorvedouros artificiais na equação de pressão, gerando dois jatos radiais espúrios a $90^\circ$ nas pontas que drenavam o empuxo ao longo de 1000 iterações.

---

## 3. Configuração com Interface MRF Cilíndrica Conformada (~8,8 Milhões de Células)

1. **Interface MRF Cilíndrica Lisa no `snappyHexMeshDict` (Sem `topoSet`):**
   - O cilindro `innerCylinder` é definido como um cilindro analítico (`searchableCylinder`, $R = 0,58\text{ m}, Y \in [-0,14; +0,14]\text{ m}$) dentro de **`refinementSurfaces`** com `faceZone innerCylinder`, `cellZone innerCylinder` e `cellZoneInside inside` no **nível 4** ($\Delta x \approx 5,2\text{ mm}$).
   - Durante a etapa de `snap`, o `snappyHexMesh` projeta os vértices da interface exatamente sobre a superfície cilíndrica, garantindo que $(\vec{\omega} \times \vec{r}_f) \cdot \vec{S}_f = 0$ em toda a lateral do cilindro MRF.
2. **Refinamento Gradual da Malha e da Esteira ($\approx 8,5\text{ a }9,0$ Milhões de Células):**
   - **`blockMeshDict`:** Malha de fundo com cubos exatos de $83,33\text{ mm}$ (`120 x 180 x 120` $= 2,592\text{M}$ células).
   - **`innerCylinder` (Nível 4, $\approx 5,2\text{ mm}$):** Alta resolução em todo o disco rotativo e na interface cilíndrica.
   - **`refinementBox` (Nível 3, $\approx 10,4\text{ mm}$):** Transição suave ao redor do cilindro MRF.
   - **`wakeCylinder` (Nível 2, $\approx 20,8\text{ mm}$):** Cilindro de refinamento na esteira ($R = 0,65\text{ m}, Y \in [-2,50; -0,14]\text{ m}$) para capturar a contração do tubo de jato (*vena contracta*).
3. **Condições de Contorno Abertas (`0/U` e `0/p`):**
   - **`0/p` (`inlet`, `outlet`, `walls`):** `totalPressure` (`p0 uniform 0`).
   - **`0/U` (`outlet` e `walls`):** `inletOutlet` com `inletValue uniform (0 0 0)`.
   - **`0/U` (`inlet` e `internalField`):** `inletOutlet` com `inletValue uniform (0 -1 0)`.

---

## 4. Fluxo de Execução

1. **Gerar a Nova Malha Conformada (~8,8M células) e Rodar Completo (`Allrun`):**
   ```bash
   ./Allrun.pre
   ./Allrun.solver
   ```
   *(Ou simplesmente `./Allrun`)*

2. **Pós-Processamento e Monitoramento:**
   - Forças e momentos brutos: `postProcessing/forces/0/forces.dat`
   - Coeficientes adimensionais: `postProcessing/forceCoeffs/0/forceCoeffs.dat`
   - Visualização no ParaView: `results.foam` / `visualizar.foam`
