"""Conversión de HTML crudo en un árbol navegable con BeautifulSoup."""

from bs4 import BeautifulSoup


def obtener_soup(html):
    return BeautifulSoup(html, "html.parser")
