import os
from werkzeug.utils import secure_filename


def convert_lists_to_html(content):
    if not content:
        return "" 
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


UPLOAD_FOLDER = "client_uploads"

def save_profile_picture(profile_pic, userid):
    user_dir = os.path.join(UPLOAD_FOLDER, "client_"+userid, "pfp")
    os.makedirs(user_dir, exist_ok=True)
    filename = secure_filename(profile_pic.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        return None  

    save_path = os.path.join(user_dir, f"profile{file_ext}")
    profile_pic.save(save_path)

    return save_path  

