"""
Sistema de Controle de Portaria
UC - Teoria da Computação e Compiladores

Ponto de entrada do programa. O código está dividido em duas pastas:
- nucleo/:    dados, regras, validações e arquivos (sem interface gráfica)
- interface/: telas e fluxos em Tkinter
"""
from interface.inicializacao import iniciar


if __name__ == "__main__":
    iniciar()
