# Pausa no Sega Rally Championship (arcade, 1995)

No ROG Ally, clique no analógico direito (R3) para pausar a corrida individual. Clique em R3 novamente para continuar. A imagem fica parada no ponto da pausa.

O atalho inicia um leitor do botão R3 do controle virtual da Steam enquanto a edição arcade está aberta. Ele suspende e retoma o processo `segarally.exe` executado a partir da pasta do próprio atalho. O botão View continua abrindo o menu do jogo.

## Instalação testada

Use sua própria instalação da edição arcade que contém `segarally.exe`. Coloque `pausa.py` e `jogar.sh` junto ao executável e torne o lançador executável com `chmod +x jogar.sh`. O perfil usa GE-Proton11-5, Steam Input e o Python com evdev fornecido pelo Bazzite. O prefixo usado por esta instalação é `~/Games/.prefixes/SegaRally`.

No teste em Desert, o cronômetro permaneceu em 1min51s17 durante a pausa e voltou a avançar ao retomar. O teste foi feito em corrida individual.
