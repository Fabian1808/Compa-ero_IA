import os

def replace_in_file(path, old, new):
    if not os.path.exists(path): return
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()
    if old in c:
        c = c.replace(old, new)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)

# 1. AdminDashboardPage
replace_in_file(
    r'C:\Users\Fabian Urteaga\Documents\Compañero_IA\Compa-ero_IA\frontend\src\pages\AdminDashboardPage.tsx',
    '< 200ms',
    '&lt; 200ms'
)

# 2. AdminMetricsPage
replace_in_file(
    r'C:\Users\Fabian Urteaga\Documents\Compañero_IA\Compa-ero_IA\frontend\src\pages\AdminMetricsPage.tsx',
    '< 0.1%',
    '&lt; 0.1%'
)

# 3. AttentionCard.tsx
p = r'C:\Users\Fabian Urteaga\Documents\Compañero_IA\Compa-ero_IA\frontend\src\components\home\AttentionCard.tsx'
with open(p, 'r', encoding='utf-8') as f: c = f.read()
if '<icons[item.type] className="h-4 w-4" />' in c:
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if '<icons[item.type] className="h-4 w-4" />' in line:
            indent = line[:len(line) - len(line.lstrip())]
            lines[i] = indent + "{(() => { const Icon = icons[item.type]; return <Icon className=\"h-4 w-4\" />; })()}"
    with open(p, 'w', encoding='utf-8') as f: f.write('\n'.join(lines))

print('Correcciones JSX parte 3 completadas.')
