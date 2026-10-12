# Simulação Aerodinâmica de Hélice com MRF no OpenFOAM-dev

Este repositório contém os arquivos de configuração e scripts para a simulação aerodinâmica estacionária (RANS) de uma hélice genérica utilizando o método de Referencial Móvel de Rotação (**MRF - Multiple Reference Frame**) no **OpenFOAM-dev** (OpenFOAM Foundation / `openfoam.org`).

---

## Especificações Técnicas do Caso

- **Solver:** `simpleFoam` (RANS incompressível estacionário com acoplamento SIMPLE).
- **Modelo de Turbulência:** RAS $k$-$\epsilon$ (`kEpsilon`) com funções de parede em alta fidelidade (`kqRWallFunction`, `epsilonWallFunction`, `nutkWallFunction`).
- **Framework MRF:** `constant/MRFProperties` nativo da OpenFOAM Foundation.
  - **Zona de Células (`cellZone`):** `innerCylinder` (gerada via `system/topoSetDict`).
  - **Eixo de Rotação (`axis`):** `(0 1 0)` (Eixo $Y$, alinhado ao canal do escoamento).
  - **Origem (`origin`):** `(0 -0.00800165 0)` (Plano médio do cubo da hélice).
  - **Velocidade Angular (`omega`):** `363.69 rad/s` (~3.473 RPM), gerando empuxo na direção $+Y$.
- **Geometria:**
  - Hélice: `constant/triSurface/propellerTip.obj` (Diâmetro: 1,016 m).
  - Condição de contorno na pá: `movingWallVelocity` em `0/U` (malha estática compatível com MRF) e `fixedFluxPressure` em `0/p`.

---

## Fluxo de Execução

1. **Pré-Processamento e Malha (`Allrun.pre`):**
   ```bash
   ./Allrun.pre
   ```
   - Executa `blockMesh` para a malha de fundo.
   - Extrai arestas de transição via `surfaceFeatures` (`propellerTip.eMesh`).
   - Gera a malha tridimensional conformada com refinamento e camadas de limite via `snappyHexMesh`.
   - Executa `topoSet` para criar a `cellZone innerCylinder` necessária para o MRF.
   - Restaura o diretório `0/` limpo a partir de `0.orig/`.

2. **Execução da Simulação (`Allrun`):**
   ```bash
   ./Allrun
   ```
   - Decompõe o domínio em paralelo via `decomposePar`.
   - Executa o solver `simpleFoam` em paralelo.
   - Reconstitui os campos processados via `reconstructPar`.

3. **Pós-Processamento e Monitoramento:**
   - As forças e momentos aerodinâmicos brutos são calculados continuamente e salvos em `postProcessing/forces/`.
   - Os coeficientes aerodinâmicos ($C_L$, $C_D$, $C_M$) são monitorados em `postProcessing/forceCoeffs/`.
   - Para visualização no ParaView, abra o arquivo `results.foam`.
