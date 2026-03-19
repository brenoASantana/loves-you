# Ama voce

Jogo curto de horror psicologico em pygame sobre trauma emocional, amor obsessivo e espacos liminares.

## O que foi implementado

1. Audio dinamico por proximidade da entidade:
- Ambiencia procedural em loop
- Camada grave + camada aguda + hiss atmosferico
- Batimento cardiaco que cresce com a tensao e distancia curta
- Timbre evolui por estagio (mais denso e abrasivo no final)
- Sussurro no evento de pico "Ama voce"

2. Iluminacao instavel por comodo:
- Tints diferentes por area da casa
- Flicker com parametros por comodo
- Vinheta de luz do jogador com instabilidade

3. Pos-processamento sujo (estilo fita/CRT):
- Granulacao procedural em tempo real
- Scanlines e vinheta pesada
- Aberracao cromatica leve em alta tensao
- Ruido visual adicional nas cutscenes

5. Presets de qualidade/desempenho:
- Alto: fidelidade maxima de ruido e pos-processamento
- Medio: equilibrio visual e desempenho (padrao)
- Baixo: menos ruido/filtros, melhor performance
- Auto: ajusta dinamicamente o preset com base no FPS medio
- Perfis de Auto: agressivo, balanceado e conservador

4. Cutscenes curtas entre puzzles:
- Fragmentos de memoria narrativos ao fim de cada estagio
- Efeito de texto progressivo
- Avanco manual com ESPACO

## Requisitos

- Python 3.10+
- Homebrew (macOS)

## Instalacao

### 1) Dependencias nativas via brew

make brew-install

### 2) Ambiente Python e pacotes

make install

## Executar

make run

### Executar com argumentos

.venv/bin/python main.py --quality alto --auto-quality on --auto-profile agressivo

- --quality: alto | medio | baixo
- --auto-quality: on | off
- --auto-profile: agressivo | balanceado | conservador

## Controles

- WASD: mover
- E: interagir
- ESPACO: avancar cutscene
- ENTER: iniciar no menu principal
- F1: preset Alto
- F2: preset Medio
- F3: preset Baixo
- F4: alternar Auto Quality (liga/desliga)
- S: abrir/fechar tela de configuracoes
- Y/N: escolha final
- R: reiniciar apos fim/captura
- ESC: sair

## Menu e configuracoes

- O jogo inicia em um menu principal.
- Pressione S para abrir a tela de configuracoes.
- O menu principal aceita clique com mouse (iniciar, configuracoes e sair).
- A tela de configuracoes aceita hover e clique nas opcoes.
- Brilho e Volume agora possuem slider visual com arraste do mouse.
- Na tela de configuracoes, voce pode ajustar:
	- Brilho
	- Volume mestre
	- Alto contraste do player
	- Preset de qualidade
	- Auto Quality
	- Perfil do Auto Quality
	- Restaurar padrao (reseta tudo para os valores iniciais)

## Persistencia de configuracoes

- As configuracoes sao salvas automaticamente ao fechar a tela de ajustes ou sair do jogo.
- Arquivo salvo em: ~/.ama_voce_settings.json
- Inclui: brilho, volume mestre, contraste do player, qualidade, auto quality e perfil auto.
