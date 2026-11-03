p = 'tools/build_town.py'
s = open(p, encoding='utf-8').read()

# remove three buildings to stay inside the tri/GLB budget
s = s.replace('''    shophouse(-130, -1, 10, 10, 3, C["wall_f"], shop=("shutter", "open"), name="sw1",
              style="brick", roof="flat", tank=True, awning_bays=(1,),
              awn_cols=("#6a7a68", "#d3c8ae"), balconies=((2, 1),), laundry=True)
''', '')
s = s.replace('''    shophouse(-135, 1, 9, 9, 2, C["wall_c"], shop=("shutter", "open"), name="se1",
              roof="tile", awning_bays=(1,))
''', '')
s = s.replace('''    shophouse(52, 1, 8, 9, 2, C["wall_i"], shop=("open", "door"), name="ne4",
              roof="tile", awning_bays=(0,), awn_cols=("#6b7a63", "#d6cab0"))
''', '')

# lighter terrain
s = s.replace('B.terrain("Terrain", 320, 300, 84, 80, terrain_h, terrain_col, matte,',
              'B.terrain("Terrain", 320, 300, 80, 76, terrain_h, terrain_col, matte,')

# fewer rooftop extras
s = s.replace('tank = floors >= 3 and R.random() < 0.55', 'tank = floors >= 3 and R.random() < 0.45')
s = s.replace('if R.random() < 0.16:\n            roof_solar(', 'if R.random() < 0.08:\n            roof_solar(')
s = s.replace('antenna_roof = R.random() < 0.45', 'antenna_roof = R.random() < 0.38')

# 6 willows, 7 street trees
s = s.replace("(36, 1), (58, -1), (76, 1)):", "(36, 1), (58, -1)):")
s = s.replace('''                                  (12, 1), (37, -1), (58, 1), (84, -1))):''',
              '''                                  (12, 1), (37, -1), (84, -1))):''')
# six market stalls
s = s.replace("for i, yy in enumerate((-2.6, 0.4, 2.9)):", "for i, yy in enumerate((-2.6, 2.9)):")

# dark backing behind every car window so the greenhouse reads as tinted glass
s = s.replace('''    quad("Glass", ws, "#a9c1bd", glassm, "windshield")''',
'''    quad("Glass", ws, "#a9c1bd", glassm, "windshield")
    quad("Trim", [(x, y - 0.02, z) for (x, y, z) in ws], "#1b2627", trim, "ws_back")''')
s = s.replace('''    quad("Glass", rw, "#9fb4b1", glassm, "rearglass")''',
'''    quad("Glass", rw, "#9fb4b1", glassm, "rearglass")
    quad("Trim", [(x, y + 0.02, z) for (x, y, z) in rw], "#1b2627", trim, "rw_back")''')
s = s.replace('''        for j, corners in enumerate(wins):
            quad("Glass", corners, "#a3b8b4", glassm, f"sideglass{sx}{j}")''',
'''        for j, corners in enumerate(wins):
            quad("Glass", corners, "#a3b8b4", glassm, f"sideglass{sx}{j}")
            quad("Trim", [(x - sx * 0.012, y, z) for (x, y, z) in corners],
                 "#1b2627", trim, f"sideback{sx}{j}")''')

open(p, 'w', encoding='utf-8').write(s)
print('town cut + car window backing')
