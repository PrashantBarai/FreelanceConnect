def convert_lists_to_html(content):
    lines = content.split('\n')
    html_lines = []
    in_list = False

    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[2:]}</li>')
        elif line.strip().startswith(('1. ', '2. ', '3. ')):
            if not in_list:
                html_lines.append('<ol>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[3:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>' if line.strip().startswith('- ') else '</ol>')
                in_list = False
            html_lines.append(line)

    if in_list:
        html_lines.append('</ul>' if lines[-1].strip().startswith('- ') else '</ol>')

    return '<br>'.join(html_lines)
