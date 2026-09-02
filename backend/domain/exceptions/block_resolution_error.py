from pathlib import Path

from backend.domain.exceptions.domain_error import DomainError


class BlockResolutionError(DomainError):
    def __init__(self, file: Path, start_point: tuple[int, int], end_point: tuple[int, int]):
        message = (f'Impossible de trouver le noeud parent du code avec les coordonnées  '
                   f'(convention début a 0 pour ligne et colonnes)\n'
                   f'Fichier: {file}\n'
                   f'Début-> ligne: {start_point[0]}, colonne: {start_point[1]}\n'
                   f'Fin-> ligne: {end_point[0]}, colonne: {end_point[1]}')
        super().__init__(message)
