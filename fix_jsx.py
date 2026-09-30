import os

base_dir = r'C:\Users\Fabian Urteaga\Documents\Compañero_IA\Compa-ero_IA\frontend\src\pages'

def fix_admin_metrics():
    p = os.path.join(base_dir, 'AdminMetricsPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('        </div>\n      </Card>\n    );', '        </div>\n      </CardContent>\n    </Card>\n  );')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def fix_commitments():
    p = os.path.join(base_dir, 'CommitmentsPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('</div>\n                }\n                <div className="flex justify-end gap-2 pt-2">', '</div>\n                <div className="flex justify-end gap-2 pt-2">')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def fix_connectors():
    p = os.path.join(base_dir, 'ConnectorsPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('Configuracin > Autenticaci', 'Configuracin &gt; Autenticaci')
    c = c.replace('Configuraci\xf3n > Autenticaci', 'Configuraci\xf3n &gt; Autenticaci')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def fix_init():
    p = os.path.join(base_dir, 'InitializationPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('                  </div>\n                ))}\n            </div>', '                  </div>\n                );\n              })}\n            </div>')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

fix_admin_metrics()
fix_commitments()
fix_connectors()
fix_init()
print('Correcciones JSX completadas.')
