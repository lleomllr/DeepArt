# -*- coding: utf-8 -*-
"""
Created on Thu May 30 19:42:51 2024

@author: meill
"""

artist_groups = [
    'baroque', 'french-classicism', 'rococo', 'neoclassicism', 'manerism', 'romantism', 'orientalism', 'realism', 'naturalism', 
    'cubism', 'popart', 'edo-period', 'meiji-period'
]

def load_artists(group_name):
    if group_name == 'baroque':
        from .groups.baroque import groups
    elif group_name == 'french-classicism':
        from .groups.french_classicism import groups
    elif group_name == 'rococo':
        from .groups.rococo import groups
    elif group_name == 'neoclassicism':
        from .groups.neoclassicism import groups
    elif group_name == 'manerism':
        from .groups.manerism import groups
    elif group_name == 'romantism':
        from .groups.romantism import groups
    elif group_name == 'orientalism':
        from .groups.orientalism import groups
    elif group_name == 'realism':
        from .groups.realism import groups
    elif group_name == 'naturalism':
        from .groups.naturalism import groups
    elif group_name == 'cubism':
        from .groups.cubism import groups
    elif group_name == 'popart':
        from .groups.popart import groups
    elif group_name == 'edo-period':
        from .groups.edo_period import groups
    elif group_name == 'meiji-period':
        from .groups.meiji_period import groups
    else: 
        raise ValueError('unknown group: {}'.format(group_name))
    return groups

baroque = load_artists('baroque')
french_classicism = load_artists('french-classicim')
rococo = load_artists('rococo')
neoclassicism = load_artists('neoclassicism')
manerism = load_artists('manerism')
romantism = load_artists('romantism')
orientalism = load_artists('orientalism')
realism = load_artists('realism')
naturalism = load_artists('naturalism')
cubism = load_artists('cubism')
popart = load_artists('popart')
edo_period = load_artists('edo-period')
meiji_period = load_artists('meiji-period')