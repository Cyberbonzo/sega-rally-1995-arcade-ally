# Sega Rally Championship (arcade, 1995) no ROG Ally

No ROG Ally, clique no analÃƒÂ³gico direito (R3) para pausar a corrida individual. Clique em R3 novamente para continuar. A imagem fica parada no ponto da pausa.

O atalho inicia um leitor do botÃƒÂ£o R3 do controle virtual da Steam enquanto a ediÃƒÂ§ÃƒÂ£o arcade estÃƒÂ¡ aberta. Ele suspende e retoma o processo `segarally.exe` executado a partir da pasta do prÃƒÂ³prio atalho. O botÃƒÂ£o View continua abrindo o menu do jogo.

## InstalaÃƒÂ§ÃƒÂ£o testada

Use sua prÃƒÂ³pria instalaÃƒÂ§ÃƒÂ£o da ediÃƒÂ§ÃƒÂ£o arcade que contÃƒÂ©m `segarally.exe`. Coloque `recordes.py`, `pausa.py` e `jogar.sh` junto ao executÃƒÂ¡vel e torne o lanÃƒÂ§ador executÃƒÂ¡vel com `chmod +x jogar.sh`. O perfil usa GE-Proton11-5, Steam Input e o Python com evdev fornecido pelo Bazzite. O prefixo usado por esta instalaÃƒÂ§ÃƒÂ£o ÃƒÂ© `~/Games/.prefixes/SegaRally`.

No teste em Desert, o cronÃƒÂ´metro permaneceu em 1min51s17 durante a pausa e voltou a avanÃƒÂ§ar ao retomar. O teste foi feito em corrida individual.


## Recordes e tempos do gabinete

O atalho da ediÃ§Ã£o de PC 1.0.0c acompanha a memÃ³ria nÃ£o volÃ¡til do gabinete durante a partida individual. Quando o jogo registra um resultado, o leitor verifica as duas cÃ³pias internas da tabela e grava o arquivo de forma atÃ´mica em `saves/arcade/backup1`. Na prÃ³xima abertura, recupera a cÃ³pia vÃ¡lida mais recente entre esse arquivo e `nvram/srallyc/backup1`. Preserve as pastas `nvram` e `saves` ao mover o jogo. Uma prova entra no ranking de acordo com as regras do arcade. No teste no Ally, a melhor volta de Desert (59,00 s) foi gravada durante a corrida e confirmada na memória do gabinete após reiniciar.

## BÃ´nus de checkpoint

Com o jogo fechado, execute `python3 checkpoints.py roms/srallyc.zip` para aplicar o bÃ´nus Ã  sua cÃ³pia da revisÃ£o C. O script ajusta os valores positivos de extensÃ£o em 600 quadros da placa (10 segundos) e guarda o conjunto original em `roms/srallyc.original.zip`. Para desfazer, feche o jogo e copie esse original por cima de `roms/srallyc.zip`.

O ajuste abrange as tabelas de Championship e Practice. O relÃ³gio inicial mantÃ©m o tempo configurado no gabinete. Em Desert, com o perfil testado, os bÃ´nus observados foram de 28 e 41 segundos, ante 18 e 31 na tabela original.
