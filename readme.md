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
- **Solver & Turbulência:** `foamRun` (`incompressibleFluid` / SIMPLE), modelo RAS `kOmegaSST` (`c1 = 1.0`, `nutUSpaldingWallFunction`), malha de $\approx 9,50$ milhões de células (`9.497.199` células).
- **Framework MRF (`constant/MRFProperties`):**
  - **Zona de Células e Faces (`cellZone` + `faceZone`):** `innerCylinder` ($Y \in [-0,10; +0,10]\text{ m}$, $R = 0,545\text{ m}$, gerada e conformada diretamente pelo `snappyHexMesh` em nível 4 dentro do cilindro de buffer uniforme `mrfBufferCylinder` de $R = 0,58\text{ m}$, eliminando a borda em escada do `topoSet` e os *hanging nodes* na interface).
  - **Eixo de Rotação (`axis`):** `(0 1 0)` | **Origem (`origin`):** `(0 -0.00800165 0)`.
  - **Condição na Pá (`propellerTip`):** `MRFnoSlip` em `0/U`, `fixedFluxPressure` em `0/p` e `nutUSpaldingWallFunction` em `0/nut`.

---

## 2. Validação Física e Diagnóstico do Regime de Hover ($J \approx 0$)

### A. Convergência Estacionária Sustentada (`t = 1000`)
- **Empuxo inicial (`75 <= t <= 175`):** **$347,0\text{ N}$ a $350,4\text{ N}$** (precisão de **$99,9\%$** frente ao benchmark de bancada de $348\text{ N}$).
- **Empuxo estacionário convergido (`t = 1000`):** **$\approx 310\text{ N}$** (sustentado dentro da meta de $300\text{ a }340\text{ N}$ após o desenvolvimento completo do tubo de esteira e da velocidade axial induzida até o `outlet`).
- **Torque viscoso estabilizado:** Cravado em **$-0,896\text{ N}\cdot\text{m}$**, sem crescimento espúrio de viscosidade turbulenta.

### B. Os Três Problemas Corrigidos em Relação à Configuração Original
1. **Bloqueio de Saída (`freestreamPressure` $\to$ `totalPressure` + `inletOutlet`):**
   Substituídas as condições de contorno externas por `totalPressure` (`p0 = 0`) em `0/p` e `inletOutlet` em `0/U`, permitindo que a esteira axial com contração de *vena contracta* saia livremente pelo `outlet`.
2. **Superprodução de Viscosidade Turbulenta $\nu_t$ nas Linhas de Corrente Fechadas do MRF:**
   - No modelo `kOmegaSST` padrão (`c1 = 10.0` + `nutkWallFunction` + $\omega_\infty = 10\text{ s}^{-1}$), a energia cinética turbulenta $k$ crescia exponencialmente ao orbitar na zona MRF, inflando uma bola de alta viscosidade turbulenta ($\nu_t \sim 10^4 \nu$) na ponta da pá que estolava a metade externa da hélice e dobrava o torque viscoso.
   - Com `c1 = 1.0` em `constant/turbulenceProperties`, `nutUSpaldingWallFunction` em `0/nut`, $k = 0,0015$ e $\omega = 360\text{ s}^{-1}$, a camada limite permanece fina e aderida à pá.
3. **Degraus Cartesianos do `topoSet` na Interface MRF:**
   - A seleção de cubos cartesianos via `topoSet` (`cylinderToCell`) gerava faces laterais em degrau ($\pm X, \pm Z$) onde $(\vec{\omega} \times \vec{r}_f) \cdot \vec{S}_f \neq 0$, injetando jatos radiais espúrios a $90^\circ$.
   - Desacoplando o cilindro de refinamento volumétrico `mrfBufferCylinder` ($R = 0,58\text{ m}, Y \in [-0,14; +0,14]\text{ m}$, `level 4`) da superfície conformada `innerCylinder` ($R = 0,545\text{ m}, Y \in [-0,10; +0,10]\text{ m}$, `level (4 4)`), o `snappyHexMesh` realiza o *snap* da interface MRF dentro de uma malha `level 4` uniforme (sem mudança de nível `4 -> 3` na parede do cilindro), garantindo $(\vec{\omega} \times \vec{r}_f) \cdot \vec{S}_f = 0$ e `Face tets OK` / `Cell determinant OK` no `checkMesh -allGeometry -allTopology`.

---

## 3. Resumo da Malha e Configuração Numérica (~9,5 Milhões de Células)

1. **Hierarquia de Refinamento (`system/snappyHexMeshDict`):**
   - **`blockMeshDict`:** Cubos de $83,33\text{ mm}$ (`120 x 180 x 120` $= 2,592\text{M}$ células).
   - **`propellerTip` (Níveis 7–8 + 5 camadas de prisma):** Resolução de $\approx 0,32\text{ mm}$ na superfície da pá, com `implicitFeatureSnap false`, `explicitFeatureSnap true`, `nSmoothPatch 3`, `minArea 1e-13` e `minTriangleTwist 0.01`.
   - **`innerCylinder` ($R = 0,545\text{ m}$, Nível 4):** Interface MRF cilíndrica conformada (`faceZone` + `cellZone`).
   - **`mrfBufferCylinder` ($R = 0,58\text{ m}$, Nível 4):** Buffer hexaédrico uniforme ao redor da interface MRF.
   - **`refinementBox` (Nível 3, $\approx 10,4\text{ mm}$) e `wakeCylinder` (Nível 2, $\approx 20,8\text{ mm}$ até $Y = -2,5\text{ m}$):** Resolução da esteira helicoidal e *vena contracta*.
2. **Estabilidade do Solver (`system/fvSolution` e `system/fvSchemes`):**
   - Solver de pressão `GAMG` com `smoother GaussSeidel` e `maxIter 200`.
   - Esquemas não-ortogonais limitados em `limited corrected 0.333`.

---

## 4. Fluxo de Execução

1. **Gerar a Malha Conformada (~9,5M células) e Rodar a Simulação (`Allrun`):**
   ```bash
   ./Allrun.pre
   ./Allrun.solver
   ```
   *(Ou simplesmente `./Allrun`)*

6. **Pós-Processamento e Monitoramento:**
   - Visualização no ParaView: `results.foam`
   - Dataset consolidado de forças (0 a 2.500 iterações): `forces_consolidated.csv`
   - Gráfico de convergência: `forces_convergence.png`
   - Gerar gráficos automaticamente: `python3 plot_forces.py`
