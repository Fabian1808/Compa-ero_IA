import os

base_dir = r'C:\Users\Fabian Urteaga\Documents\Compañero_IA\Compa-ero_IA\frontend\src\pages'

def fix_admin_dashboard():
    p = os.path.join(base_dir, 'AdminDashboardPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('        </div>\n      </Card>\n    );', '        </div>\n      </CardContent>\n    </Card>\n  );')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def fix_admin_metrics():
    p = os.path.join(base_dir, 'AdminMetricsPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('< 200ms', '&lt; 200ms')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

def fix_commitments():
    p = os.path.join(base_dir, 'CommitmentsPage.tsx')
    with open(p, 'r', encoding='utf-8') as f: c = f.read()
    c = c.replace('</select>\n                  </div>\n                <div className="flex justify-end gap-2 pt-2">', '</select>\n                  </div>\n                )} \n                <div className="flex justify-end gap-2 pt-2">')
    with open(p, 'w', encoding='utf-8') as f: f.write(c)

fix_admin_dashboard()
fix_admin_metrics()
try:
    fix_commitments()
except: pass
print('Correcciones JSX parte 2 completadas.')
