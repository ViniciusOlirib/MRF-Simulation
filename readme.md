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
  - **Zona de Células (`cellZone`):** `innerCylinder` ($Y \in [-0,14; +0,14]\text{ m}$, $R = 0,58\text{ m}$, gerada via `system/topoSetDict` dentro da região hexaédrica uniforme nível 3 da `refinementBox`).
  - **Eixo de Rotação (`axis`):** `(0 1 0)` | **Origem (`origin`):** `(0 -0.00800165 0)`.
  - **Condição na Pá (`propellerTip`):** `MRFnoSlip` em `0/U` e `fixedFluxPressure` em `0/p`.

---

## 2. Validação Física e Diagnóstico do Regime de Hover ($J \approx 0$)

### A. Validação na Janela Inicial ($40 \le t \le 80$)
Durante as iterações **40 a 80**, enquanto o escoamento axial limpo atravessa o disco do rotor sem contaminação por refluxo de fronteira ou bombeamento centrífugo acumulado:
- **Empuxo atingido:** **$327,9\text{ N}$** (**$94,2\%$** do valor experimental de bancada de $348\text{ N}$, erro $< 5,8\%$).
- **Torque no eixo:** **$-14,1\text{ N}\cdot\text{m}$**.
- **Padrão de escoamento:** Jato axial cilíndrico colimado descendo livremente no sentido $-Y$.

### B. Mecanismo de Degradação Tardia ($t > 1000$) na Configuração Anterior
Na configuração anterior, o empuxo decaía até um platô espúrio de $105,2\text{ N}$ devido a três fatores acoplados:
1. **Bloqueio de Saída por `freestreamPressure` + `freestreamVelocity`:** No contorno `outlet` ($Y = -10\text{ m}$), `freestreamPressure` impunha `zeroGradient` ($\partial p / \partial n = 0$) na saída do jato, deixando a pressão estática a jusante sem âncora atmosférica ($p = 0$). Além disso, quando ocorria refluxo ($\phi < 0$), `freestreamVelocity` forçava `inletValue (0 -1 0)` apontando para fora do domínio, criando um tampão numérico em $Y \in [-10, -2]\text{ m}$ ($U \approx 0$).
2. **Extrapolação da Zona MRF Fora da `refinementBox` (`topoSetDict`):** O cilindro MRF havia sido estendido até $Y = -0,30\text{ m}$ a jusante, saindo da `refinementBox` ($Y_{\min} = -0,15\text{ m}$) para dentro da malha grossa de nível 0 e aplicando aceleração centrífuga de $6.850\text{ G}$ sobre a esteira livre.
3. **Recirculação Toroidal:** O jato defletido atingia as laterais e retornava ao disco da hélice, aumentando a velocidade induzida $V_i$ e derrubando o ângulo de ataque efetivo $\alpha_{\text{eff}} = \theta - \text{arctg}(V_i / \Omega r)$.

---

## 3. Configuração Estabilizada para Escoamento Axial Livre (MRF Tuning)

1. **Condições de Contorno Abertas (`0/U` e `0/p`):**
   - **`0/p` (`inlet`, `outlet`, `walls`):** Configurado com `totalPressure` (`p0 uniform 0`). Na saída ($\phi \ge 0$), fixa a pressão estática em $p = 0$, permitindo que o jato saia livremente sem reflexão; na admissão ($\phi < 0$), aplica a relação de Bernoulli $p = p_0 - \frac{1}{2}|\vec{U}|^2$.
   - **`0/U` (`outlet` e `walls`):** Configurado com `inletOutlet` e `inletValue uniform (0 0 0)`, garantindo saída livre (`zeroGradient`) para o jato e amortecendo qualquer tentativa de refluxo (`backflow`) com velocidade nula.
   - **`0/U` (`inlet` e `internalField`):** Configurado com `inletOutlet` e velocidade axial estabilizadora $V_\infty = 1,0\text{ m/s}$ (`inletValue uniform (0 -1 0)`, razão de avanço quase-estática $J = V_\infty / (nD) \approx 0,017$), mantendo a lavagem convectiva axial do cilindro MRF.
2. **Posicionamento da Interface MRF em Malha Hexaédrica Uniforme (`system/topoSetDict`):**
   - A `cellZone innerCylinder` está definida em **$Y \in [-0,14; +0,14]\text{ m}, R = 0,58\text{ m}$**, permanecendo $100\%$ dentro da `refinementBox` (nível 3, $Y \in [-0,15; +0,15]\text{ m}$) e fora da casca de transição poliédrica (`level 8 -> 3`, $\approx 3\text{ cm}$ de espessura) ao redor da ponta das pás ($R_{\text{tip}} = 0,508\text{ m}$).

---

## 4. Fluxo de Execução

1. **Reexecução Rápida do Solver na Malha Existente (`Allrun.solver`):**
   *(Não requer regeração da malha `snappyHexMesh` — atualiza `0/` e a `cellZone` via `topoSet` diretamente)*
   ```bash
   ./Allrun.solver
   ```

2. **Pré-Processamento Completo e Malha (`Allrun.pre` / `Allrun`):**
   ```bash
   ./Allrun.pre
   ./Allrun
   ```

3. **Pós-Processamento e Monitoramento:**
   - Forças e momentos brutos: `postProcessing/forces/0/forces.dat`
   - Coeficientes adimensionais: `postProcessing/forceCoeffs/0/forceCoeffs.dat`
   - Visualização no ParaView: `results.foam` / `visualizar.foam`
