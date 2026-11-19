# Sega Rally Championship (arcade, 1995) no ROG Ally

No ROG Ally, clique no analógico direito (R3) para pausar a corrida individual. Clique em R3 novamente para continuar. A imagem fica parada no ponto da pausa. O botão View abre o menu do jogo.

## Instalação testada

Use sua própria instalação da edição arcade para PC 1.0.0c com `segarally.exe` e seu próprio conjunto de revisão C. Coloque `jogar.sh`, `pausa.py`, `recordes.py` e `checkpoints.py` junto ao executável e torne o lançador executável com `chmod +x jogar.sh`. O perfil usa GE-Proton11-5, Steam Input e o Python com evdev fornecido pelo Bazzite. Esta instalação usa o prefixo `~/Games/.prefixes/SegaRally`.

O atalho lê o botão R3 do controle virtual da Steam e suspende ou retoma o processo do jogo iniciado nessa pasta. No teste em Desert, o cronômetro permaneceu em 1min51s17 durante a pausa e voltou a avançar ao retomar.

## Recordes e tempos do gabinete

Durante a partida individual, o leitor acompanha a memória não volátil do gabinete. Quando o jogo registra um resultado, o leitor verifica as duas cópias internas da tabela e grava o arquivo de forma atômica em `saves/arcade/backup1`. Na próxima abertura, recupera a cópia válida mais recente entre esse arquivo e `nvram/srallyc/backup1`. Preserve as pastas `nvram` e `saves` ao mover o jogo. Uma prova entra no ranking de acordo com as regras do arcade. No teste no Ally, a melhor volta de Desert (59,00 s) foi gravada durante a corrida e confirmada na memória do gabinete após reiniciar.

## Adversários 20% mais lentos e bônus de checkpoint

Na pasta do jogo, com a partida fechada, execute:

```sh
python3 checkpoints.py roms/srallyc.zip --ritmo 80
```

O ajuste multiplica por 0,8 as velocidades-alvo dos rivais nas quatro etapas de Championship (Desert, Forest, Mountain e Lakeside) e nos perfis alternativos dos adversários. A alteração alcança os carros que começam à frente ou atrás do jogador. Em Desert, por exemplo, alvos de 160 e 210 passam a 128 e 168. Curvas, largadas e colisões continuam afetando a velocidade instantânea. O ajuste mantém a física do jogador, a posição de largada e as regras de classificação.

No teste em Desert no ROG Ally, os sete rivais em movimento usaram os alvos de 128, 130,4, 132, 136, 140, 144 e 168 km/h. Cada valor corresponde a 80% do alvo original do mesmo carro.

O bônus de tempo acrescenta dez segundos aos checkpoints de Championship e Practice. O relógio inicial usa o tempo configurado no gabinete. Em Desert, os bônus observados foram de 28 e 41 segundos, ante 18 e 31 na tabela original.

O relógio da corrida admite no máximo 99 segundos. O jogo aplica o limite ao iniciar a etapa, ao transferir o saldo entre etapas e ao creditar um checkpoint. Por exemplo, com 90 segundos restantes e um bônus de 28, o saldo passa a 99 e a contagem regressiva continua. O tempo total da prova e os tempos de volta continuam independentes desse limite. No teste em Desert, um bônus de 44 segundos teria levado o saldo acima de 101 segundos. O saldo efetivo ficou em 99 e caiu para 98 após um segundo de corrida.

Para voltar ao ritmo original dos adversários e manter o bônus de tempo, execute:

```sh
python3 checkpoints.py roms/srallyc.zip --ritmo 100
```

Executar o comando sem `--ritmo` aplica o bônus de checkpoint e preserva o ritmo já escolhido. O script guarda uma cópia do conjunto original em `roms/srallyc.original.zip`. Para restaurar o painel, o tempo de checkpoint e o ritmo originais, feche o jogo e copie esse arquivo sobre `roms/srallyc.zip`.
